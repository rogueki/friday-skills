import unittest
from datetime import datetime, timedelta, timezone

from shared.policy import (
    PolicyError, action_fingerprint, authorize_action, capability_available,
    risk_tier, validate_event, validate_result,
)


NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)


def capability(mode="live", permissions=None, **changes):
    record = {
        "name": "test.adapter", "mode": mode, "status": "healthy",
        "authenticated": True, "rate_limited": False,
        "permissions": permissions or ["read", "write"],
        "checked_at": NOW.isoformat(), "synthetic": mode == "mock",
        "authorized_workspace": True,
    }
    record.update(changes)
    return record


def approval(action, target, payload, tier=2, **changes):
    record = {
        "status": "approved", "fingerprint": action_fingerprint(action, target, payload),
        "target": target, "tier": tier,
        "expires_at": (NOW + timedelta(minutes=5)).isoformat(),
        "hard_approval": tier == 3, "second_factor_verified": tier == 3,
    }
    record.update(changes)
    return record


class PolicyTests(unittest.TestCase):
    def test_unknown_action_is_hard_tier(self):
        self.assertEqual(risk_tier("surprise_new_mutation"), 3)

    def test_stale_or_degraded_capability_fails_closed(self):
        self.assertFalse(capability_available(capability(checked_at=(NOW - timedelta(minutes=6)).isoformat()), permission="write", mode="live", now=NOW))
        self.assertFalse(capability_available(capability(status="degraded"), permission="read", mode="live", now=NOW))
        self.assertFalse(capability_available(capability(rate_limited=True), permission="read", mode="live", now=NOW))

    def test_mock_requires_synthetic_and_cannot_write(self):
        self.assertFalse(capability_available(capability("mock", synthetic=False), permission="read", mode="mock", now=NOW))
        with self.assertRaises(PolicyError):
            authorize_action("send_message", "person", "hi", mode="mock", capability=capability("mock"), now=NOW)

    def test_read_only_local_draft_is_allowed(self):
        self.assertEqual(authorize_action("draft", "workspace/report.md", "text", mode="read_only", capability=capability("read_only", permissions=["read"]), now=NOW), 1)
        with self.assertRaises(PolicyError):
            authorize_action("local_reversible_write", "workspace/report.md", "text", mode="mock", capability=capability("mock", permissions=["read"]), now=NOW)

    def test_external_write_needs_bound_approval_and_idempotency(self):
        action, target, payload = "send_message", "user@example.test", "hello"
        with self.assertRaises(PolicyError):
            authorize_action(action, target, payload, mode="live", capability=capability(), now=NOW)
        with self.assertRaises(PolicyError):
            authorize_action(action, target, payload, mode="live", capability=capability(), approval=approval(action, target, "changed"), idempotency_key="same", now=NOW)
        self.assertEqual(authorize_action(action, target, payload, mode="live", capability=capability(), approval=approval(action, target, payload), idempotency_key="same", now=NOW), 2)

    def test_tier_three_requires_second_factor_and_expiry(self):
        action, target, payload = "payment", "invoice-7", {"amount": "10.00"}
        with self.assertRaises(PolicyError):
            authorize_action(action, target, payload, mode="live", capability=capability(), approval=approval(action, target, payload, 3, second_factor_verified=False), idempotency_key="p-7", now=NOW)
        with self.assertRaises(PolicyError):
            authorize_action(action, target, payload, mode="live", capability=capability(), approval=approval(action, target, payload, 3, expires_at=(NOW - timedelta(seconds=1)).isoformat()), idempotency_key="p-7", now=NOW)

    def test_completed_requires_verification_and_no_pending_approval(self):
        result = {"status": "completed", "skill": "friday-web-research", "mode": "read_only", "summary": "done", "artifacts": [], "actions_taken": [], "actions_proposed": [], "approvals_required": [], "warnings": [], "errors": [], "sources": [], "verification": []}
        with self.assertRaises(PolicyError):
            validate_result(result)
        result["verification"] = ["source checked"]
        result["sources"] = [{"url": "https://example.com", "retrieved_at": NOW.isoformat()}]
        validate_result(result)
        result["actions_taken"] = [{"external_write": True}]
        with self.assertRaises(PolicyError):
            validate_result(result)

    def test_completed_event_requires_progress_one(self):
        event = {"event_id": "e1", "type": "friday.skill.completed", "skill": "friday-web-research", "status": "completed", "activity": "done", "progress": .8, "timestamp": NOW.isoformat(), "mode": "mock"}
        with self.assertRaises(PolicyError):
            validate_event(event)
        event["progress"] = 1
        validate_event(event)

    def test_internal_record_rejects_rogue_friday_event_names(self):
        event = {"event_id": "e2", "type": "jarvis.task.completed", "skill": "friday-web-research", "status": "completed", "activity": "done", "progress": 1, "timestamp": NOW.isoformat(), "mode": "mock"}
        with self.assertRaises(PolicyError):
            validate_event(event)
        event["type"] = "jarvis.skill.completed"
        with self.assertRaises(PolicyError):
            validate_event(event)

    def test_malformed_approval_fails_closed(self):
        action, target, payload = "send_message", "person", "hello"
        with self.assertRaises(PolicyError):
            authorize_action(action, target, payload, mode="live", capability=capability(), approval=approval(action, target, payload, tier=None), idempotency_key="m-1", now=NOW)
        with self.assertRaises(PolicyError):
            authorize_action(action, target, payload, mode="live", capability=capability(), approval=approval(action, target, payload, expires_at=None), idempotency_key="m-1", now=NOW)


if __name__ == "__main__":
    unittest.main()
