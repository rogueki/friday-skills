"""Optional, local-only observer for Hermes Kanban lifecycle hooks.

Only allowlisted identifiers are persisted. Hook payloads such as summaries,
block reasons, assignees, prompts, and secrets are intentionally ignored.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
from typing import Any


LOGGER = logging.getLogger(__name__)
HOOKS = (
    "kanban_task_claimed",
    "kanban_task_completed",
    "kanban_task_blocked",
)
_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_MAX_SQLITE_INT = (1 << 63) - 1
_SCHEMA = """
CREATE TABLE IF NOT EXISTS kanban_events (
    dedupe_key TEXT PRIMARY KEY,
    event_kind TEXT NOT NULL,
    task_id TEXT NOT NULL,
    run_id INTEGER,
    board TEXT,
    profile TEXT,
    timestamp TEXT NOT NULL
)
"""


def _repository_root() -> Path | None:
    candidate = Path(__file__).resolve().parents[2]
    if (candidate / "registry" / "skills.json").is_file() and (candidate / "skills").is_dir():
        return candidate
    return None


def _database_path() -> Path:
    """Resolve an opt-in DB location without creating any files/directories."""
    configured = os.environ.get("FRIDAY_KANBAN_OBSERVER_DB")
    home_value = os.environ.get("HERMES_HOME")

    if configured:
        candidate = Path(configured).expanduser()
        if not candidate.is_absolute():
            raise ValueError("FRIDAY_KANBAN_OBSERVER_DB must be an absolute path")
    elif home_value:
        home = Path(home_value).expanduser()
        if not home.is_absolute():
            raise ValueError("HERMES_HOME must be absolute for the observer journal")
        candidate = home / "state" / "friday-kanban-observer.sqlite3"
    else:
        raise ValueError("configure FRIDAY_KANBAN_OBSERVER_DB or HERMES_HOME")

    # Resolve the parent to catch symlinked paths, but require it to exist so
    # the observer never creates directories as a side effect.
    parent = candidate.parent.resolve(strict=True)
    if not parent.is_dir():
        raise ValueError("observer database parent must be an existing directory")
    target = parent / candidate.name
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError("observer database must be a regular file")
    repo = _repository_root()
    if repo is not None:
        try:
            target.resolve(strict=False).relative_to(repo.resolve(strict=True))
        except ValueError:
            pass
        else:
            raise ValueError("observer database must be outside the friday-skills repository")
    return target


def _identifier(value: Any) -> str | None:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        return None
    return value


def _event_row(event_kind: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    task_id = _identifier(payload.get("task_id"))
    if task_id is None:
        return None

    raw_run_id = payload.get("run_id")
    run_id = raw_run_id if (
        isinstance(raw_run_id, int)
        and not isinstance(raw_run_id, bool)
        and 0 <= raw_run_id <= _MAX_SQLITE_INT
    ) else None
    row = {
        "event_kind": event_kind,
        "task_id": task_id,
        "run_id": run_id,
        "board": _identifier(payload.get("board")),
        "profile": _identifier(payload.get("profile_name")),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
    }
    stable_fields = {key: row[key] for key in ("event_kind", "task_id", "run_id", "board", "profile")}
    row["dedupe_key"] = hashlib.sha256(
        json.dumps(stable_fields, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return row


def _append(event_kind: str, **payload: Any) -> None:
    """Append one sanitized event; observer errors never escape into Hermes."""
    row = _event_row(event_kind, payload)
    if row is None:
        return

    try:
        database = _database_path()
        with closing(sqlite3.connect(database, timeout=5.0)) as connection:
            with connection:
                connection.execute("PRAGMA busy_timeout = 5000")
                connection.execute(_SCHEMA)
                connection.execute(
                    """INSERT OR IGNORE INTO kanban_events
                       (dedupe_key, event_kind, task_id, run_id, board, profile, timestamp)
                       VALUES (:dedupe_key, :event_kind, :task_id, :run_id, :board, :profile, :timestamp)""",
                    row,
                )
        if os.name == "posix":
            database.chmod(0o600)
    except (OSError, sqlite3.Error, ValueError) as exc:
        # Never include exception text: SQLite diagnostics may reveal paths.
        LOGGER.warning("Kanban observer did not write its local journal (%s)", type(exc).__name__)


def register(ctx) -> None:
    """Subscribe as a best-effort observer; no DB is opened during registration."""
    for event_kind in HOOKS:
        ctx.register_hook(
            event_kind,
            lambda _event_kind=event_kind, **payload: _append(_event_kind, **payload),
        )
