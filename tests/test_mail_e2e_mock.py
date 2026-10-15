"""E2E1 local composition; no provider transport or real operator approval."""

from datetime import timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import adapters.mail_e2e_mock as flow
from adapters.caldav_calendar import list_events
from adapters.gmx_mail import MailAdapterError, read_message
from shared.approval_ledger import ApprovalLedger, ApprovalLedgerError
from shared.policy import capability_available
from shared.runtime import MockRuntime
from shared.scenarios import run_scenario


class ImportantMailE2ETests(unittest.TestCase):
    def test_parsers_run_and_unapproved_flow_waits_without_transport(self):
        with patch.object(flow, "read_message", wraps=read_message) as mail_reader, \
             patch.object(flow, "list_events", wraps=list_events) as calendar_reader, \
             patch("adapters.gmx_mail.send_message", side_effect=AssertionError("SMTP path called")):
            result = run_scenario("important_mail_e2e")
        mail_reader.assert_called_once_with("INBOX", "71", mode="mock", mock_fixture="e2e_important")
        self.assertEqual(calendar_reader.call_count, 1)
        self.assertEqual(calendar_reader.call_args.kwargs["mode"], "mock")
        self.assertEqual(result["status"], "waiting_approval")
        self.assertEqual(result["classification"]["priority"], "P1")
        self.assertEqual(result["thread_summary"]["source_uid"], "71")
        self.assertEqual(result["thread_summary"]["thread_id"], "<briefing-71@example.invalid>")
        self.assertEqual(result["thread_summary"]["request"],
                         "Please confirm whether you can attend the briefing today at 12:00 UTC.")
        self.assertEqual(result["thread_summary"]["received_at"], "2026-10-15T10:15:00+00:00")
        self.assertEqual(result["calendar_context"]["starts_at"], "2026-10-15T12:00:00+00:00")
        self.assertEqual(result["proposal"]["payload"], result["draft"])
        self.assertNotIn("mock_send", result)
        self.assertEqual(result["external_effects"], 0)
        self.assertTrue(all(not mapping["publishable"] for mapping in result["dashboard_mapping"]))

    def test_approved_synthetic_grant_only_simulates_delivery(self):
        with patch("adapters.gmx_mail.send_message", side_effect=AssertionError("SMTP path called")):
            result = run_scenario("important_mail_e2e", variant="approved")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mock_send"]["transport"], "none")
        self.assertFalse(result["mock_send"]["delivered"])
        self.assertEqual(result["external_effects"], 0)
        self.assertEqual(result["mock_send"]["fingerprint"], result["approval_preview"]["fingerprint"])
        self.assertTrue(all(not entry["executed"] for entry in result["audit"]))
        self.assertTrue(all(not mapping["publishable"] for mapping in result["dashboard_mapping"]))

    def test_injection_and_missing_calendar_stop_before_proposal(self):
        for variant, reason in (("injection", "untrusted_mail"),
                                ("calendar_unavailable", "capability_unavailable")):
            with self.subTest(variant=variant):
                with patch.object(flow, "capability_available", wraps=capability_available) as capability_check, \
                     patch.object(flow, "list_events", wraps=list_events) as calendar_reader:
                    result = run_scenario("important_mail_e2e", variant=variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertNotIn("proposal", result)
                self.assertNotIn("mock_send", result)
                self.assertEqual(result["external_effects"], 0)
                if variant == "calendar_unavailable":
                    capability_check.assert_called_once()
                    self.assertEqual(result["calendar_capability"]["available"], False)
                    self.assertIn("calendar_mock_capability_checked", result["trace"])
                    calendar_reader.assert_not_called()

    def test_message_id_and_date_must_come_from_parsed_rfc822(self):
        for changed, reason in (({"message_id": "<other@example.invalid>"}, "untrusted_mail"),
                                ({"date": "invalid"}, "untrusted_mail")):
            with self.subTest(changed=changed):
                def altered_reader(*args, **kwargs):
                    return {**read_message(*args, **kwargs), **changed}

                with patch.object(flow, "read_message", side_effect=altered_reader):
                    result = run_scenario("important_mail_e2e")
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertNotIn("proposal", result)

    def test_invalid_approval_binding_stops_simulation(self):
        for variant in ("forged_approval", "expired_approval", "changed_recipient", "changed_draft"):
            with self.subTest(variant=variant):
                result = run_scenario("important_mail_e2e", variant=variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", "mock_approval_invalid"))
                self.assertNotIn("mock_send", result)
                self.assertEqual(result["external_effects"], 0)

    def test_grant_cannot_be_replayed_and_mock_fixture_is_allowlisted(self):
        runtime = MockRuntime()
        pending = run_scenario("important_mail_e2e")
        draft = pending["draft"]
        with TemporaryDirectory() as temp:
            ledger = ApprovalLedger(Path(temp) / "grant.sqlite")
            grant = ledger.issue(action="send_message", target=draft["recipient"], payload=draft,
                                 idempotency_key="synthetic-mail-replay", decision_id="synthetic-replay-decision",
                                 expires_at=runtime.now + timedelta(minutes=5), now=runtime.now)
            ledger.consume(grant, action="send_message", target=draft["recipient"], payload=draft,
                           idempotency_key="synthetic-mail-replay", now=runtime.now)
            with self.assertRaises(ApprovalLedgerError):
                ledger.consume(grant, action="send_message", target=draft["recipient"], payload=draft,
                               idempotency_key="synthetic-mail-replay", now=runtime.now)
        with self.assertRaises(MailAdapterError):
            read_message("INBOX", "71", mode="mock", mock_fixture="../../sensitive")


if __name__ == "__main__":
    unittest.main()
