"""Bounded CalDAV client with an explicit transport and fail-closed writes.

This is a provider-neutral RFC 4791 subset, not a calendar sync engine. A
trusted caller supplies authentication through its transport and verifies the
capability/approval records before passing them here.
"""

from __future__ import annotations

from dataclasses import dataclass
from contextlib import closing
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sqlite3
from typing import Callable, Mapping, Any
from urllib.parse import urlsplit, urljoin
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shared.approval_ledger import ApprovalLedger, ApprovalLedgerError
from shared.policy import action_fingerprint, capability_available


MAX_RESPONSE_BYTES = 1_000_000
MAX_EVENTS = 100
MAX_WINDOW = timedelta(days=31)
DAV = "{DAV:}"
CAL = "{urn:ietf:params:xml:ns:caldav}"
ETAG = re.compile(r'^"[^"\r\n]+"$')
UID = re.compile(r"^[A-Za-z0-9._@-]{1,160}$")
Transport = Callable[["Request"], "Response"]


class CalendarAdapterError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class Request:
    method: str
    url: str
    headers: Mapping[str, str]
    body: bytes
    timeout: float


@dataclass(frozen=True)
class Response:
    status: int
    headers: Mapping[str, str]
    body: bytes


def _endpoint(endpoint: str, allowed_host: str) -> str:
    if not isinstance(endpoint, str) or not isinstance(allowed_host, str):
        raise CalendarAdapterError("invalid_endpoint", "explicit HTTPS endpoint and host required")
    try:
        p = urlsplit(endpoint)
    except ValueError as exc:
        raise CalendarAdapterError("invalid_endpoint", "invalid calendar endpoint") from exc
    if (p.scheme != "https" or p.hostname != allowed_host or p.username or p.password
            or p.port is not None or not p.path.startswith("/") or not p.path.endswith("/")
            or p.query or p.fragment or "%" in p.path or not allowed_host
            or not re.fullmatch(r"[A-Za-z0-9.-]+", allowed_host)):
        raise CalendarAdapterError("invalid_endpoint", "endpoint must be an allowlisted HTTPS calendar collection")
    return endpoint


def _time(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise CalendarAdapterError("invalid_time", "timezone-aware datetime required")
    return value.astimezone(timezone.utc)


def _request(transport: Transport | None, request: Request, *, mutation: bool = False) -> Response:
    if transport is None:
        raise CalendarAdapterError("transport_required", "an authenticated transport must be supplied explicitly")
    try:
        response = transport(request)
    except Exception as exc:
        raise CalendarAdapterError("outcome_uncertain" if mutation else "unavailable", "calendar transport failed") from exc
    if not isinstance(response, Response) or not isinstance(response.status, int) or not isinstance(response.body, bytes):
        raise CalendarAdapterError("outcome_uncertain" if mutation else "invalid_response", "invalid transport response")
    if len(response.body) > MAX_RESPONSE_BYTES:
        raise CalendarAdapterError("outcome_uncertain" if mutation else "response_too_large", "calendar response too large")
    if response.status in (401, 403):
        raise CalendarAdapterError("auth_failed", "calendar access denied")
    return response


def _lines(ical: str) -> list[str]:
    if not isinstance(ical, str) or len(ical.encode("utf-8")) > 128_000 or "\x00" in ical:
        raise CalendarAdapterError("invalid_ical", "calendar data invalid or too large")
    normalized = ical.replace("\r\n", "\n")
    if "\r" in normalized:
        raise CalendarAdapterError("invalid_ical", "invalid line endings")
    unfolded: list[str] = []
    for line in normalized.split("\n"):
        if line.startswith((" ", "\t")):
            if not unfolded:
                raise CalendarAdapterError("invalid_ical", "orphan folded line")
            unfolded[-1] += line[1:]
        elif line:
            unfolded.append(line)
    if not unfolded or unfolded[0] != "BEGIN:VCALENDAR" or unfolded[-1] != "END:VCALENDAR":
        raise CalendarAdapterError("invalid_ical", "VCALENDAR envelope required")
    return unfolded


def _ical_time(key: str, value: str) -> datetime:
    params = key.split(";")
    tzids = [p[5:] for p in params[1:] if p.upper().startswith("TZID=")]
    is_date = any(p.upper() == "VALUE=DATE" for p in params[1:])
    if len(tzids) > 1:
        raise CalendarAdapterError("invalid_ical", "duplicate TZID")
    try:
        if is_date:
            if tzids or not re.fullmatch(r"\d{8}", value):
                raise ValueError("bad DATE")
            return datetime.combine(datetime.strptime(value, "%Y%m%d").date(), datetime.min.time(), timezone.utc)
        if value.endswith("Z"):
            if tzids:
                raise ValueError("UTC with TZID")
            return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        if len(tzids) != 1:
            raise ValueError("floating time")
        local = datetime.strptime(value, "%Y%m%dT%H%M%S")
        zone = ZoneInfo(tzids[0])
        aware = local.replace(tzinfo=zone)
        if aware.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None) != local:
            raise ValueError("nonexistent local time")
        if local.replace(tzinfo=zone, fold=0).utcoffset() != local.replace(tzinfo=zone, fold=1).utcoffset():
            raise ValueError("ambiguous local time")
        return aware.astimezone(timezone.utc)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise CalendarAdapterError("invalid_ical", "unsupported or ambiguous calendar time") from exc


def parse_event(ical: str) -> dict[str, str]:
    lines = _lines(ical)
    if lines.count("BEGIN:VEVENT") != 1 or lines.count("END:VEVENT") != 1:
        raise CalendarAdapterError("invalid_ical", "exactly one VEVENT required")
    start = lines.index("BEGIN:VEVENT")
    end = lines.index("END:VEVENT")
    if start >= end or any(x.startswith(("BEGIN:", "END:")) for x in lines[start + 1:end]):
        raise CalendarAdapterError("invalid_ical", "nested or malformed VEVENT")
    props: dict[str, tuple[str, str]] = {}
    for line in lines[start + 1:end]:
        if ":" not in line:
            raise CalendarAdapterError("invalid_ical", "malformed VEVENT property")
        key, value = line.split(":", 1)
        base = key.split(";", 1)[0].upper()
        if base in {"UID", "DTSTART", "DTEND", "SUMMARY", "RRULE", "RECURRENCE-ID"}:
            if base in props:
                raise CalendarAdapterError("invalid_ical", "duplicate VEVENT property")
            props[base] = (key, value)
    if "RRULE" in props or "RECURRENCE-ID" in props:
        raise CalendarAdapterError("unsupported_recurrence", "recurrence expansion is not supported")
    if not all(k in props for k in ("UID", "DTSTART", "DTEND", "SUMMARY")):
        raise CalendarAdapterError("invalid_ical", "VEVENT needs UID, DTSTART, DTEND and SUMMARY")
    uid = props["UID"][1]
    if not UID.fullmatch(uid):
        raise CalendarAdapterError("invalid_ical", "unsupported UID")
    begins = _ical_time(*props["DTSTART"])
    ends = _ical_time(*props["DTEND"])
    if ends <= begins:
        raise CalendarAdapterError("invalid_ical", "DTEND must follow DTSTART")
    return {"uid": uid, "starts_at": begins.isoformat(), "ends_at": ends.isoformat(), "summary": props["SUMMARY"][1]}


def _resource(url: str, endpoint: str) -> str:
    base = urlsplit(endpoint)
    candidate = urlsplit(urljoin(endpoint, url))
    if (candidate.scheme != "https" or candidate.netloc != base.netloc or
            not candidate.path.startswith(base.path) or "%" in candidate.path or
            candidate.query or candidate.fragment or
            candidate.path == base.path or not candidate.path.endswith(".ics")):
        raise CalendarAdapterError("invalid_href", "resource escaped calendar collection")
    return candidate.geturl()


def _parse_multistatus(body: bytes, endpoint: str, start: datetime, end: datetime) -> list[dict[str, str]]:
    if len(body) > MAX_RESPONSE_BYTES or b"<!DOCTYPE" in body.upper() or b"<!ENTITY" in body.upper():
        raise CalendarAdapterError("invalid_xml", "unsafe calendar XML")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise CalendarAdapterError("invalid_xml", "malformed calendar XML") from exc
    if root.tag != DAV + "multistatus":
        raise CalendarAdapterError("invalid_xml", "DAV multistatus required")
    rows = root.findall(DAV + "response")
    if len(rows) > MAX_EVENTS:
        raise CalendarAdapterError("too_many_events", "calendar response exceeds event limit")
    events: list[dict[str, str]] = []
    for row in rows:
        href = row.findtext(DAV + "href")
        propstats = row.findall(DAV + "propstat")
        successful = [p for p in propstats if " 200 " in (p.findtext(DAV + "status") or "")]
        if not href or len(successful) != 1:
            raise CalendarAdapterError("invalid_xml", "calendar object missing successful propstat")
        prop = successful[0].find(DAV + "prop")
        if prop is None:
            raise CalendarAdapterError("invalid_xml", "calendar properties missing")
        etag = prop.findtext(DAV + "getetag")
        ical = prop.findtext(CAL + "calendar-data")
        if not etag or not ETAG.fullmatch(etag) or not ical:
            raise CalendarAdapterError("invalid_xml", "strong ETag and calendar-data required")
        event = parse_event(ical)
        event_start = datetime.fromisoformat(event["starts_at"])
        event_end = datetime.fromisoformat(event["ends_at"])
        if event_end <= start or event_start >= end:
            raise CalendarAdapterError("invalid_response", "server returned event outside requested range")
        events.append({**event, "href": _resource(href, endpoint), "etag": etag})
    return events


def list_events(endpoint: str, account: str, start: datetime, end: datetime, *,
                allowed_host: str, mode: str = "mock", transport: Transport | None = None,
                timeout: float = 8.0) -> dict[str, Any]:
    endpoint = _endpoint(endpoint, allowed_host)
    if not isinstance(account, str) or not account.strip():
        raise CalendarAdapterError("invalid_account", "explicit calendar account required")
    if mode not in {"mock", "read_only", "live"}:
        raise CalendarAdapterError("invalid_mode", "unsupported mode")
    begins, ends = _time(start), _time(end)
    if ends <= begins or ends - begins > MAX_WINDOW:
        raise CalendarAdapterError("invalid_window", "window must be positive and at most 31 days")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 15:
        raise CalendarAdapterError("invalid_timeout", "timeout must be within 15 seconds")
    body = ('<?xml version="1.0" encoding="utf-8"?>'
            '<C:calendar-query xmlns:C="urn:ietf:params:xml:ns:caldav" xmlns:D="DAV:">'
            '<D:prop><D:getetag/><C:calendar-data/></D:prop><C:filter>'
            '<C:comp-filter name="VCALENDAR"><C:comp-filter name="VEVENT">'
            f'<C:time-range start="{begins:%Y%m%dT%H%M%SZ}" end="{ends:%Y%m%dT%H%M%SZ}"/>'
            '</C:comp-filter></C:comp-filter></C:filter></C:calendar-query>').encode()
    if mode == "mock":
        if transport is not None:
            raise CalendarAdapterError("invalid_transport", "mock mode cannot use transport")
        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "calendar" / "adapter_multistatus.xml"
        raw = fixture.read_bytes()
        source = "synthetic:fixtures/calendar/adapter_multistatus.xml"
    else:
        response = _request(transport, Request("REPORT", endpoint, {
            "Depth": "1", "Content-Type": "application/xml; charset=utf-8", "Accept": "application/xml",
        }, body, float(timeout)))
        if response.status != 207:
            raise CalendarAdapterError("bad_status", "calendar REPORT did not return 207")
        raw = response.body
        source = endpoint
    return {"status": "completed", "mode": mode, "account": account,
            "events": _parse_multistatus(raw, endpoint, begins, ends), "source": source,
            "synthetic": mode == "mock", "write_effect": False}


def _ledger_claim(path: Path, key: str, fingerprint: str) -> dict[str, Any] | None:
    if not path.is_absolute() or path.exists() and path.is_symlink():
        raise CalendarAdapterError("invalid_ledger", "absolute, non-symlink ledger path required")
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path, timeout=5)) as db:
        with db:
            db.execute("CREATE TABLE IF NOT EXISTS operations (key TEXT PRIMARY KEY, fingerprint TEXT NOT NULL, state TEXT NOT NULL, receipt TEXT)")
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT fingerprint, state, receipt FROM operations WHERE key=?", (key,)).fetchone()
            if row:
                if row[0] != fingerprint:
                    raise CalendarAdapterError("idempotency_conflict", "key bound to a different mutation")
                if row[1] == "completed":
                    return json.loads(row[2])
                raise CalendarAdapterError("outcome_uncertain", "mutation already attempted; reconcile with server before retry")
            db.execute("INSERT INTO operations VALUES (?, ?, 'uncertain', NULL)", (key, fingerprint))
    return None


def _ledger_complete(path: Path, key: str, receipt: dict[str, Any]) -> None:
    with closing(sqlite3.connect(path, timeout=5)) as db:
        with db:
            db.execute("UPDATE operations SET state='completed', receipt=? WHERE key=?", (json.dumps(receipt), key))


def write_event(endpoint: str, account: str, ical: str, *, allowed_host: str,
                action: str, idempotency_key: str, approval_ledger: ApprovalLedger | None,
                grant_id: str | None,
                capability: Mapping[str, Any], ledger_path: Path, transport: Transport | None,
                href: str | None = None, etag: str | None = None, mode: str = "live",
                timeout: float = 8.0, now: datetime | None = None) -> dict[str, Any]:
    endpoint = _endpoint(endpoint, allowed_host)
    if not isinstance(account, str) or not account.strip():
        raise CalendarAdapterError("invalid_account", "explicit calendar account required")
    if mode != "live" or action not in {"create", "update"}:
        raise CalendarAdapterError("invalid_mode", "only live create/update supported")
    if transport is None:
        raise CalendarAdapterError("transport_required", "explicit authenticated transport required")
    if not isinstance(idempotency_key, str) or not UID.fullmatch(idempotency_key):
        raise CalendarAdapterError("invalid_key", "stable idempotency key required")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 15:
        raise CalendarAdapterError("invalid_timeout", "timeout must be within 15 seconds")
    event = parse_event(ical)
    if action == "create":
        if href is not None or etag is not None:
            raise CalendarAdapterError("invalid_target", "create has no existing resource")
        target = endpoint + sha256((account + ":" + idempotency_key).encode()).hexdigest() + ".ics"
        precondition = {"If-None-Match": "*"}
    else:
        if not href or not etag or not ETAG.fullmatch(etag):
            raise CalendarAdapterError("invalid_target", "update needs resource and strong ETag")
        target = _resource(href, endpoint)
        precondition = {"If-Match": etag}
    payload = {"account": account, "ical": ical, "etag": etag}
    if not capability_available(capability, permission="write", mode="live", now=now):
        raise CalendarAdapterError("approval_blocked", "fresh authenticated write capability required")
    if not isinstance(approval_ledger, ApprovalLedger) or not isinstance(grant_id, str):
        raise CalendarAdapterError("approval_blocked", "trusted approval ledger and grant ID required")
    try:
        approval_ledger.consume(grant_id, action="calendar_write", target=target, payload=payload,
                                idempotency_key=idempotency_key, now=now)
    except ApprovalLedgerError as exc:
        raise CalendarAdapterError("approval_blocked", str(exc)) from exc
    fingerprint = action_fingerprint("calendar_write", target, payload)
    prior = _ledger_claim(Path(ledger_path), idempotency_key, fingerprint)
    if prior is not None:
        return prior
    response = _request(transport, Request("PUT", target, {
        **precondition, "Content-Type": "text/calendar; charset=utf-8",
        "Accept": "text/calendar", "X-Friday-Idempotency-Key": idempotency_key,
    }, ical.encode("utf-8"), float(timeout)), mutation=True)
    if response.status in (409, 412):
        raise CalendarAdapterError("conflict", "calendar resource precondition failed; reconcile before retry")
    if response.status not in (200, 201, 204):
        raise CalendarAdapterError("outcome_uncertain", "calendar mutation outcome requires reconciliation")
    returned_etag = response.headers.get("ETag")
    if returned_etag is not None and not ETAG.fullmatch(returned_etag):
        raise CalendarAdapterError("outcome_uncertain", "invalid returned ETag; reconcile before retry")
    receipt = {"status": "completed", "mode": "live", "account": account, "action": action,
               "uid": event["uid"], "href": target, "etag": returned_etag,
               "write_effect": True, "idempotency_key": idempotency_key}
    _ledger_complete(Path(ledger_path), idempotency_key, receipt)
    return receipt
