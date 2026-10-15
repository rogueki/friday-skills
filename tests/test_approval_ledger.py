"""Offline tests for the host-owned, one-use Tier-2 grant store."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import tempfile
import unittest

from shared.approval_ledger import ApprovalLedger, ApprovalLedgerError


NOW = datetime(2026, 10, 15, 14, tzinfo=timezone.utc)
ACTION = "send_message"
TARGET = "recipient@example.invalid"
PAYLOAD = {"body": "private content", "subject": "private title"}
KEY = "stable-operation-key"


class ApprovalLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "approvals.sqlite3"
        self.ledger = ApprovalLedger(self.path)

    def grant(self, **changes):
        args = dict(action=ACTION, target=TARGET, payload=PAYLOAD, idempotency_key=KEY,
                    decision_id="operator-decision-123", expires_at=NOW + timedelta(minutes=5), now=NOW)
        args.update(changes)
        return self.ledger.issue(**args)

    def consume(self, grant_id, **changes):
        args = dict(action=ACTION, target=TARGET, payload=PAYLOAD, idempotency_key=KEY, now=NOW)
        args.update(changes)
        self.ledger.consume(grant_id, **args)

    def test_exact_one_time_grant_survives_restart_and_contains_no_payload(self):
        grant_id = self.grant()
        self.consume(grant_id)
        with self.assertRaises(ApprovalLedgerError):
            ApprovalLedger(self.path).consume(grant_id, action=ACTION, target=TARGET,
                                               payload=PAYLOAD, idempotency_key=KEY, now=NOW)
        raw = self.path.read_bytes()
        for forbidden in (b"private content", b"private title", TARGET.encode(), KEY.encode(), grant_id.encode()):
            self.assertNotIn(forbidden, raw)

    def test_target_payload_key_action_and_expiry_are_bound(self):
        grant_id = self.grant()
        for changes in ({"target": "other@example.invalid"}, {"payload": {"body": "changed"}},
                        {"idempotency_key": "another-key"}, {"action": "calendar_write"},
                        {"now": NOW + timedelta(minutes=5)}):
            with self.subTest(changes=changes), self.assertRaises(ApprovalLedgerError):
                self.consume(grant_id, **changes)
        self.consume(grant_id)

    def test_operator_decision_cannot_issue_two_grants(self):
        self.grant()
        with self.assertRaisesRegex(ApprovalLedgerError, "decision already used"):
            self.grant(idempotency_key="another-operation-key")

    def test_concurrent_consumption_has_one_winner(self):
        grant_id = self.grant()
        def attempt(_):
            try:
                ApprovalLedger(self.path).consume(grant_id, action=ACTION, target=TARGET,
                                                   payload=PAYLOAD, idempotency_key=KEY, now=NOW)
                return True
            except ApprovalLedgerError:
                return False
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt, range(8))), 1)

    def test_invalid_storage_and_failed_ledger_are_closed(self):
        with self.assertRaises(ApprovalLedgerError):
            ApprovalLedger(Path("relative.sqlite"))
        linked = Path(self.tmp.name) / "linked.sqlite"
        linked.symlink_to(self.path)
        with self.assertRaises(ApprovalLedgerError):
            ApprovalLedger(linked)
        grant_id = self.grant()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("DROP TABLE grants")
            db.commit()
        with self.assertRaises(ApprovalLedgerError):
            self.consume(grant_id)

    def test_corrupt_expiry_fails_closed_without_consumption(self):
        grant_id = self.grant()
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("UPDATE grants SET expires_at='corrupt'")
            db.commit()
        with self.assertRaises(ApprovalLedgerError):
            self.consume(grant_id)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertIsNone(db.execute("SELECT consumed_at FROM grants").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
