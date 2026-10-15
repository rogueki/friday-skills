"""Opt-in GMX IMAP reader and approval-bound SMTP sender.

No network connection occurs unless a caller explicitly supplies credentials and
sets ``use_stdlib_transport=True`` or injects a transport. Mail is untrusted data.
"""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import closing
from datetime import datetime, timezone
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
import imaplib
import json
from pathlib import Path
import re
import smtplib
import sqlite3
import ssl
from typing import Any, Callable, Mapping

from shared.policy import PolicyError, action_fingerprint, authorize_action


IMAP_HOST = "imap.gmx.net"
SMTP_HOST = "mail.gmx.net"
MAX_MESSAGE_BYTES = 65_536
MAX_BODY_CHARS = 16_000
MAX_ATTACHMENT_BYTES = 2_000_000
ALLOWED_ATTACHMENTS = frozenset({"application/pdf", "text/plain", "image/png", "image/jpeg"})
_UID = re.compile(r"[1-9][0-9]{0,9}\Z")
_KEY = re.compile(r"[A-Za-z0-9_-]{16,128}\Z")
_INJECTION = re.compile(r"ignore (?:all |previous |prior )?instructions|system prompt|developer message|tool call|send (?:this |an )?email|übergehe .*anweisung", re.I)


class MailAdapterError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class GMXCredentials:
    address: str
    app_password: str

    def __post_init__(self) -> None:
        _address(self.address)
        if not isinstance(self.app_password, str) or not self.app_password:
            raise MailAdapterError("credentials_missing", "GMX app password required")


def _address(value: str) -> str:
    if not isinstance(value, str) or len(value) > 254 or "\r" in value or "\n" in value:
        raise MailAdapterError("invalid_address", "one valid mail address required")
    from email.utils import parseaddr

    display, parsed = parseaddr(value)
    if display or parsed != value or value.count("@") != 1 or not value.split("@", 1)[1]:
        raise MailAdapterError("invalid_address", "one valid mail address required")
    return value


def _mailbox(value: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 80 or not value.isascii() or not re.fullmatch(r"[A-Za-z0-9_/-]+", value):
        raise MailAdapterError("invalid_mailbox", "explicit simple mailbox name required")
    return value


def _uid(value: str | int) -> str:
    uid = str(value) if type(value) in (str, int) else ""
    if not _UID.fullmatch(uid) or int(uid) > 4_294_967_295:
        raise MailAdapterError("invalid_uid", "explicit numeric IMAP UID required")
    return uid


def _imap_read(credentials: GMXCredentials, mailbox: str, uid: str, timeout: float) -> bytes:
    client = imaplib.IMAP4_SSL(IMAP_HOST, 993, ssl_context=ssl.create_default_context(), timeout=timeout)
    try:
        client.login(credentials.address, credentials.app_password)
        status, _ = client.examine(mailbox)
        if status != "OK":
            raise MailAdapterError("mailbox_unavailable", "mailbox cannot be examined")
        status, rows = client.uid("FETCH", uid, f"(BODY.PEEK[]<0.{MAX_MESSAGE_BYTES + 1}>)")
        if status != "OK" or not rows:
            raise MailAdapterError("message_unavailable", "UID fetch failed")
        literals = [part[1] for part in rows if isinstance(part, tuple) and len(part) == 2
                    and isinstance(part[0], bytes) and isinstance(part[1], bytes)
                    and re.search(rb"\bUID " + uid.encode("ascii") + rb"\b", part[0], re.I)]
        if len(literals) != 1:
            raise MailAdapterError("message_unavailable", "UID not found")
        return literals[0]
    finally:
        try:
            client.logout()
        except (imaplib.IMAP4.error, OSError):
            pass


ReadTransport = Callable[[GMXCredentials, str, str, float], bytes]
SendTransport = Callable[[GMXCredentials, EmailMessage, float], None]


def _smtp_send(credentials: GMXCredentials, message: EmailMessage, timeout: float) -> None:
    with smtplib.SMTP(SMTP_HOST, 587, timeout=timeout) as client:
        client.ehlo()
        client.starttls(context=ssl.create_default_context())
        client.ehlo()
        client.login(credentials.address, credentials.app_password)
        client.send_message(message)


def _timeout(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 15:
        raise MailAdapterError("invalid_timeout", "timeout must be 0..15 seconds")
    return float(value)


def read_message(
    mailbox: str, uid: str | int, *, mode: str = "mock",
    credentials: GMXCredentials | None = None, transport: ReadTransport | None = None,
    use_stdlib_transport: bool = False, timeout: float = 8.0,
) -> dict[str, Any]:
    """Read one selected UID without marking it seen; never execute HTML or attachments."""
    if mode not in {"mock", "read_only", "live"}:
        raise MailAdapterError("invalid_mode", "unsupported mode")
    selected_mailbox, selected_uid = _mailbox(mailbox), _uid(uid)
    seconds = _timeout(timeout)
    if mode == "mock":
        if transport is not None or use_stdlib_transport or credentials is not None:
            raise MailAdapterError("invalid_transport", "mock mode has no external transport")
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "mail" / "adapter_message.json"
        sample = json.loads(fixture.read_text(encoding="utf-8"))
        if selected_mailbox != sample["mailbox"] or selected_uid != sample["uid"]:
            raise MailAdapterError("message_unavailable", "synthetic UID unavailable")
        raw = sample["rfc822"].encode("utf-8")
    else:
        if credentials is None or not isinstance(credentials, GMXCredentials):
            raise MailAdapterError("credentials_missing", "explicit GMX credentials required")
        if (transport is None) == (not use_stdlib_transport):
            raise MailAdapterError("transport_missing", "choose exactly one explicit transport")
        try:
            raw = (transport or _imap_read)(credentials, selected_mailbox, selected_uid, seconds)
        except MailAdapterError:
            raise
        except Exception as exc:
            raise MailAdapterError("imap_unavailable", "IMAP read failed") from exc
    if not isinstance(raw, bytes) or not 0 < len(raw) <= MAX_MESSAGE_BYTES:
        raise MailAdapterError("message_too_large", "message exceeds bounded read limit")
    try:
        message = BytesParser(policy=policy.default).parsebytes(raw)
    except Exception as exc:
        raise MailAdapterError("invalid_message", "mail could not be parsed") from exc
    body = ""
    attachments: list[dict[str, Any]] = []
    for part in message.walk():
        if part.is_multipart():
            continue
        content_type = part.get_content_type()
        payload = part.get_payload(decode=True) or b""
        if part.get_content_disposition() == "attachment" or part.get_filename():
            attachments.append({"name": (part.get_filename() or "unnamed")[:120], "content_type": content_type,
                                "size_bytes": len(payload), "allowed": content_type in ALLOWED_ATTACHMENTS and len(payload) <= MAX_ATTACHMENT_BYTES})
        elif content_type == "text/plain" and not body:
            try:
                body = payload.decode(part.get_content_charset() or "utf-8", errors="replace")[: MAX_BODY_CHARS + 1]
            except LookupError:
                body = payload.decode("utf-8", errors="replace")[: MAX_BODY_CHARS + 1]
    suspicious = bool(_INJECTION.search("\n".join((body, str(message.get("From", "")), str(message.get("Subject", ""))))))
    return {
        "status": "partial" if len(body) > MAX_BODY_CHARS else "completed", "mode": mode,
        "source": "synthetic:fixtures/mail/adapter_message.json" if mode == "mock" else "gmx:imap",
        "mailbox": selected_mailbox, "uid": selected_uid,
        "from": str(message.get("From", ""))[:254], "subject": str(message.get("Subject", ""))[:300],
        "date": str(message.get("Date", ""))[:120], "body_text_untrusted": body[:MAX_BODY_CHARS],
        "suspicious_instructions": suspicious, "attachments": attachments[:20],
        "html_ignored": any(p.get_content_type() == "text/html" for p in message.walk()),
        "truncated": len(body) > MAX_BODY_CHARS, "write_effect": False,
    }


def send_message(
    *, sender: str, recipient: str, subject: str, body: str,
    mode: str = "mock", credentials: GMXCredentials | None = None,
    capability: Mapping[str, Any] | None = None, approval: Mapping[str, Any] | None = None,
    idempotency_key: str | None = None, ledger_path: Path | None = None,
    transport: SendTransport | None = None, use_stdlib_transport: bool = False,
    timeout: float = 8.0, now: datetime | None = None,
) -> dict[str, Any]:
    """Reserve the fingerprint durably before the single SMTP attempt.

    All SMTP exceptions yield unknown outcome; retry needs human reconciliation.
    """
    if mode != "live":
        raise MailAdapterError("live_required", "SMTP send requires live mode")
    sender, recipient = _address(sender), _address(recipient)
    if credentials is None or not isinstance(credentials, GMXCredentials) or sender.casefold() != credentials.address.casefold():
        raise MailAdapterError("sender_mismatch", "sender must match authenticated GMX account")
    if not isinstance(subject, str) or not isinstance(body, str) or not subject.strip() or not body.strip() or len(subject) > 300 or len(body) > 50_000 or any(c in subject for c in "\r\n"):
        raise MailAdapterError("invalid_message", "bounded plain text subject and body required")
    if not isinstance(idempotency_key, str) or not _KEY.fullmatch(idempotency_key):
        raise MailAdapterError("idempotency_required", "stable idempotency key required")
    if ledger_path is None or not isinstance(ledger_path, Path) or not ledger_path.is_absolute() or not ledger_path.parent.is_dir():
        raise MailAdapterError("ledger_required", "existing absolute journal directory required")
    if (transport is None) == (not use_stdlib_transport):
        raise MailAdapterError("transport_missing", "choose exactly one explicit send transport")
    seconds = _timeout(timeout)
    payload = {"sender": sender, "recipient": recipient, "subject": subject, "body": body}
    try:
        authorize_action("send_message", recipient, payload, mode=mode, capability=capability or {}, approval=approval,
                         idempotency_key=idempotency_key, now=now)
    except PolicyError as exc:
        raise MailAdapterError("approval_required", str(exc)) from exc
    fingerprint = action_fingerprint("send_message", recipient, payload)
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    # A unique fingerprint blocks a second key for the same message, too.
    try:
        with closing(sqlite3.connect(ledger_path, timeout=5)) as db:
            db.execute("CREATE TABLE IF NOT EXISTS mail_send (idempotency_key TEXT PRIMARY KEY, fingerprint TEXT UNIQUE NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL)")
            db.execute("INSERT INTO mail_send VALUES (?, ?, 'reserved', ?)",
                       (idempotency_key, fingerprint, (now or datetime.now(timezone.utc)).isoformat()))
            db.commit()
    except sqlite3.IntegrityError as exc:
        raise MailAdapterError("duplicate_or_unknown", "message already reserved or attempted; reconcile before sending") from exc
    except sqlite3.Error as exc:
        raise MailAdapterError("ledger_unavailable", "durable send journal unavailable") from exc
    try:
        (transport or _smtp_send)(credentials, message, seconds)
        state = "accepted_by_smtp"
    except Exception:
        state = "unknown_outcome"
    try:
        with closing(sqlite3.connect(ledger_path, timeout=5)) as db:
            db.execute("UPDATE mail_send SET state = ? WHERE idempotency_key = ?", (state, idempotency_key))
            db.commit()
    except sqlite3.Error:
        state = "unknown_outcome"
    return {"status": state, "fingerprint": fingerprint, "idempotency_key": idempotency_key,
            "recipient": recipient, "smtp_attempted": True, "retry_allowed": False}
