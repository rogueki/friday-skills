"""Synthetic E2E10 outage boundary and recovery evidence."""

import unittest

from shared.scenarios import run_scenario


class SystemOutageMockTests(unittest.TestCase):
    def test_outage_blocks_mail_before_proposal_and_only_maps_local_warning(self):
        for variant in ("default", "offline"):
            with self.subTest(variant=variant):
                result = run_scenario("system_outage", variant=variant)
                self.assertEqual(result["status"], "blocked")
                self.assertFalse(result["capability_available"])
                self.assertEqual(result["blocked_skill"], "friday-executive-mail-manager")
                self.assertFalse(result["blocked_action_executed"])
                self.assertNotIn("proposal", result)
                self.assertEqual(result["audit"], [])
                self.assertEqual(result["external_effects"], 0)
                self.assertEqual(result["events"][0]["status"], "blocked")
                self.assertFalse(result["dashboard_mapping"]["publishable"])
                self.assertEqual(result["recovery_plan"]["kind"], "non_executable_plan")
                self.assertFalse(result["recovery_plan"]["service_action_taken"])
                self.assertEqual(result["recovery_status"], "not_verified")

    def test_two_ordered_fresh_readiness_probes_only_verify_synthetic_recovery(self):
        result = run_scenario("system_outage", variant="recovered")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["recovery_status"], "mock_verified")
        self.assertEqual(len(result["readiness_probes_verified"]), 2)
        self.assertLess(*result["readiness_probes_verified"])
        self.assertEqual([event["status"] for event in result["events"]], ["blocked", "completed"])
        self.assertTrue(result["requires_fresh_request"])
        self.assertFalse(result["blocked_action_executed"])
        self.assertEqual(result["audit"], [])
        self.assertNotIn("proposal", result)
        self.assertEqual(result["external_effects"], 0)

    def test_missing_stale_flapping_or_untrusted_evidence_never_verifies_recovery(self):
        for variant in ("stale_health", "flapping", "no_post_check", "missing_adapter",
                        "malformed_initial", "unknown_status", "stale_recovery",
                        "unordered_recovery", "wrong_source", "wrong_adapter"):
            with self.subTest(variant=variant):
                result = run_scenario("system_outage", variant=variant)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["recovery_status"], "not_verified")
                self.assertFalse(result["blocked_action_executed"])
                self.assertNotIn("proposal", result)
                self.assertEqual(result["audit"], [])
                self.assertEqual(result["external_effects"], 0)
                self.assertFalse(result["dashboard_mapping"]["publishable"])
                self.assertNotIn("synthetic_recovery_readiness_verified", result["trace"])
                if variant == "stale_health":
                    self.assertIn("adapter_unavailable", result["trace"])
                    self.assertNotIn("adapter_offline", result["trace"])

    def test_unrecognized_variant_is_rejected(self):
        with self.assertRaises(ValueError):
            run_scenario("system_outage", variant="live_restart")


if __name__ == "__main__":
    unittest.main()
