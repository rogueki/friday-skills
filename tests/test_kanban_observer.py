"""Hermes Kanban observer tests using a fake context and temporary SQLite DB."""

from __future__ import annotations

from contextlib import closing
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from plugins.friday_kanban_observer import HOOKS, register


class Context:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, hook_name, callback):
        self.hooks.setdefault(hook_name, []).append(callback)

    def fire(self, hook_name, **payload):
        return [callback(**payload) for callback in self.hooks[hook_name]]


class KanbanObserverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "journal.sqlite3"
        self.env = patch.dict(os.environ, {
            "FRIDAY_KANBAN_OBSERVER_DB": str(self.db),
            "HERMES_HOME": str(self.root / "hermes"),
        }, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.ctx = Context()
        register(self.ctx)

    def rows(self):
        with closing(sqlite3.connect(self.db)) as connection:
            return connection.execute(
                "SELECT event_kind, task_id, run_id, board, profile, timestamp FROM kanban_events ORDER BY event_kind"
            ).fetchall()

    def fire(self, event_kind, **payload):
        self.ctx.fire(event_kind, **payload)

    def test_registers_only_documented_observer_hooks_without_creating_db(self):
        self.assertEqual(set(self.ctx.hooks), set(HOOKS))
        self.assertFalse(self.db.exists())

    def test_persists_only_allowlisted_metadata_and_redacts_content_fields(self):
        secret_summary = "private summary with token=ghp_supersecret"
        secret_reason = "internal customer data and password=hunter2"
        self.fire("kanban_task_claimed", task_id="task-17", run_id=9, board="main", profile_name="work", assignee="worker")
        self.fire("kanban_task_completed", task_id="task-17", run_id=9, board="main", profile_name="work", summary=secret_summary)
        self.fire("kanban_task_blocked", task_id="task-18", run_id=10, board="main", profile_name="work", reason=secret_reason)

        rows = self.rows()
        self.assertEqual(len(rows), 3)
        self.assertEqual({row[0] for row in rows}, set(HOOKS))
        self.assertTrue(all(row[2] in (9, 10) and row[3:5] == ("main", "work") for row in rows))
        with closing(sqlite3.connect(self.db)) as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(kanban_events)")}
            self.assertEqual(columns, {"dedupe_key", "event_kind", "task_id", "run_id", "board", "profile", "timestamp"})
            raw = connection.execute("SELECT * FROM kanban_events").fetchall()
        serialized = repr(raw)
        self.assertNotIn(secret_summary, serialized)
        self.assertNotIn(secret_reason, serialized)
        self.assertNotIn("ghp_supersecret", serialized)
        self.assertNotIn("hunter2", serialized)

    def test_duplicate_hook_delivery_is_idempotent(self):
        payload = {"task_id": "task-1", "run_id": 3, "board": "main", "profile_name": "work"}
        self.fire("kanban_task_claimed", **payload)
        self.fire("kanban_task_claimed", **payload)
        self.assertEqual(len(self.rows()), 1)

    def test_invalid_or_unconfigured_path_fails_closed_without_creating_files(self):
        with patch.dict(os.environ, {"FRIDAY_KANBAN_OBSERVER_DB": "relative.sqlite3"}):
            self.fire("kanban_task_claimed", task_id="task-1")
        self.assertFalse((Path.cwd() / "relative.sqlite3").exists())

        self.db.unlink(missing_ok=True)
        with patch.dict(os.environ, {}, clear=True):
            self.fire("kanban_task_claimed", task_id="task-1")
        self.assertFalse(self.db.exists())

    def test_database_inside_repository_is_refused(self):
        # Patch the repo root to a temp directory and point the journal beneath it.
        repo = self.root / "repo"
        repo.mkdir()
        nested = repo / "state"
        nested.mkdir()
        with patch("plugins.friday_kanban_observer._repository_root", return_value=repo):
            with patch.dict(os.environ, {"FRIDAY_KANBAN_OBSERVER_DB": str(nested / "journal.sqlite3")}):
                self.fire("kanban_task_claimed", task_id="task-1")
        self.assertFalse((nested / "journal.sqlite3").exists())

    def test_installed_plugin_allows_journal_in_hermes_state(self):
        home = self.root / "hermes"
        state = home / "state"
        state.mkdir(parents=True)
        with patch("plugins.friday_kanban_observer._repository_root", return_value=None):
            with patch.dict(os.environ, {"FRIDAY_KANBAN_OBSERVER_DB": "", "HERMES_HOME": str(home)}):
                self.fire("kanban_task_claimed", task_id="task-1", run_id=1)
        journal = state / "friday-kanban-observer.sqlite3"
        self.assertTrue(journal.is_file())
        with closing(sqlite3.connect(journal)) as connection:
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM kanban_events").fetchone()[0], 1)

    def test_corrupt_database_is_not_repaired_or_overwritten(self):
        self.db.write_bytes(b"not a sqlite database")
        before = self.db.read_bytes()
        self.fire("kanban_task_claimed", task_id="task-1")
        self.assertEqual(self.db.read_bytes(), before)

    def test_non_identifier_payload_is_not_persisted_as_free_text(self):
        self.fire("kanban_task_claimed", task_id="token=secret-value", board="customer/project name", profile_name="work")
        self.assertFalse(self.db.exists())


if __name__ == "__main__":
    unittest.main()
