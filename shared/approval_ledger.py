"""Host-owned, durable, one-use grants for external Tier-2 mutations.

The host must authenticate the operator before calling ``issue``. This class
enforces consumption, not the provenance of that operator decision.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import os
from pathlib import Path
import secrets
import sqlite3
import stat

from shared.policy import action_fingerprint, risk_tier


class ApprovalLedgerError(ValueError):
    pass


def _digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _time(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if not isinstance(current, datetime) or current.tzinfo is None:
        raise ApprovalLedgerError("UTC aware time required")
    return current.astimezone(timezone.utc)


class ApprovalLedger:
    """SQLite grant store. Keep this object outside model-facing tool inputs."""

    def __init__(self, path: Path):
        if not isinstance(path, Path) or not path.is_absolute() or path.name in {"", ".", ".."}:
            raise ApprovalLedgerError("absolute ledger file required")
        if not path.parent.is_dir() or any(parent.is_symlink() for parent in path.parents):
            raise ApprovalLedgerError("existing non-symlink ledger directory required")
        if path.exists() or path.is_symlink():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise ApprovalLedgerError("regular non-linked ledger file required")
            if os.name != "nt" and info.st_mode & 0o077:
                raise ApprovalLedgerError("ledger file must be private (0600)")
        else:
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                fd = os.open(path, flags, 0o600)
                os.close(fd)
            except FileExistsError as exc:
                raise ApprovalLedgerError("ledger path changed during creation") from exc
        self.path = path
        try:
            with closing(self._connect()) as db:
                db.execute("""CREATE TABLE IF NOT EXISTS grants (
                    grant_hash TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    target_hash TEXT NOT NULL,
                    fingerprint TEXT NOT NULL,
                    key_hash TEXT NOT NULL,
                    tier INTEGER NOT NULL,
                    decision_hash TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    consumed_at TEXT
                )""")
        except sqlite3.Error as exc:
            raise ApprovalLedgerError("approval ledger unavailable") from exc

    def _connect(self) -> sqlite3.Connection:
        if self.path.is_symlink() or any(parent.is_symlink() for parent in self.path.parents):
            raise ApprovalLedgerError("ledger path is no longer trusted")
        if not self.path.is_file() or self.path.stat().st_nlink != 1:
            raise ApprovalLedgerError("ledger file is no longer regular and single-linked")
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=5000")
            db.execute("PRAGMA synchronous=FULL")
        except sqlite3.Error:
            db.close()
            raise
        return db

    def issue(self, *, action: str, target: str, payload: object,
              idempotency_key: str, expires_at: datetime, decision_id: str,
              now: datetime | None = None) -> str:
        """Trusted host calls only after an authenticated operator decision."""
        current, expiry = _time(now), _time(expires_at)
        if risk_tier(action) != 2 or not target or not idempotency_key or not decision_id:
            raise ApprovalLedgerError("specific Tier-2 decision required")
        if not current < expiry <= current + timedelta(hours=24):
            raise ApprovalLedgerError("grant expiry must be within 24 hours")
        try:
            fingerprint = action_fingerprint(action, target, payload)
        except (TypeError, ValueError) as exc:
            raise ApprovalLedgerError("invalid approval payload") from exc
        grant_id = secrets.token_hex(32)
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO grants VALUES (?, ?, ?, ?, ?, 2, ?, ?, NULL)",
                           (_digest(grant_id), action, _digest(target), fingerprint,
                            _digest(idempotency_key), _digest(decision_id), expiry.isoformat()))
                db.commit()
        except sqlite3.IntegrityError as exc:
            raise ApprovalLedgerError("operator decision already used") from exc
        except sqlite3.Error as exc:
            raise ApprovalLedgerError("approval ledger unavailable") from exc
        return grant_id

    def consume(self, grant_id: str, *, action: str, target: str, payload: object,
                idempotency_key: str, now: datetime | None = None) -> None:
        """Atomically mark the exact grant used before any external side effect."""
        if not isinstance(grant_id, str) or len(grant_id) != 64 or any(c not in "0123456789abcdef" for c in grant_id):
            raise ApprovalLedgerError("invalid grant ID")
        if risk_tier(action) != 2 or not target or not idempotency_key:
            raise ApprovalLedgerError("specific Tier-2 action required")
        current = _time(now)
        try:
            fingerprint = action_fingerprint(action, target, payload)
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT action, target_hash, fingerprint, key_hash, tier, expires_at, consumed_at "
                                 "FROM grants WHERE grant_hash=?", (_digest(grant_id),)).fetchone()
                if row is None or row[6] is not None:
                    raise ApprovalLedgerError("grant missing or already consumed")
                if row[:5] != (action, _digest(target), fingerprint, _digest(idempotency_key), 2):
                    raise ApprovalLedgerError("grant binding mismatch")
                try:
                    expiry = datetime.fromisoformat(row[5])
                except (TypeError, ValueError) as exc:
                    raise ApprovalLedgerError("invalid stored grant expiry") from exc
                if expiry.tzinfo is None or expiry <= current:
                    raise ApprovalLedgerError("grant expired")
                updated = db.execute("UPDATE grants SET consumed_at=? WHERE grant_hash=? AND consumed_at IS NULL",
                                     (current.isoformat(), _digest(grant_id)))
                if updated.rowcount != 1:
                    raise ApprovalLedgerError("grant no longer available")
                db.commit()
        except sqlite3.Error as exc:
            raise ApprovalLedgerError("approval ledger unavailable") from exc
