"""Offline E2E8 assertions over the real local status normalizer."""

from __future__ import annotations

import unittest

from shared.scenarios import run_scenario


class LoxoneE2EMockTests(unittest.TestCase):
    def test_status_answer_is_exact_and_synthetic(self):
        result = run_scenario("loxone", variant="status_only")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["reading"]["control"]["id"], "ctrl-light-office")
        self.assertEqual(result["reading"]["control"]["value"], 0.0)
        self.assertEqual(result["reading"]["source"], "synthetic:fixtures/loxone/e2e_status.json")
        self.assertIn("Simulation", result["answer"])
        self.assertEqual(result["verification"]["scope"], "synthetic_status_only")
        self.assertNotIn("proposal", result)
        self.assertEqual(result["audit"], [])

    def test_default_command_requires_exact_tier_two_approval(self):
        result = run_scenario("loxone")
        self.assertEqual(result["status"], "waiting_approval")
        self.assertEqual(result["verification"], "not_executed")
        self.assertEqual(result["proposal"]["action"], "smart_home_write")
        self.assertEqual(result["proposal"]["target"], "ctrl-light-office")
        self.assertEqual(result["proposal"]["risk_tier"], 2)
        self.assertEqual(result["proposal"]["payload"]["before"], 0.0)
        self.assertEqual(result["proposal"]["payload"]["desired"], 100.0)
        self.assertFalse(result["approval"]["granted"])
        self.assertNotIn("simulation", result)

    def test_separate_simulated_grant_uses_one_shot_in_memory_readback(self):
        result = run_scenario("loxone", variant="mock_approved")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["verification"]["value"], 100.0)
        self.assertEqual(result["verification"]["control_id"], "ctrl-light-office")
        self.assertEqual(result["verification"]["source"], "synthetic:injected-mock-snapshot")
        self.assertFalse(result["verification"]["live_device_verified"])
        self.assertTrue(result["approval"]["consumed"])
        self.assertFalse(result["approval"]["trusted_host_approval"])
        self.assertTrue(result["simulation"]["in_memory_only"])
        self.assertFalse(result["simulation"]["external_write"])
        self.assertIn("read_status_mock_readback_verified", result["trace"])

    def test_bad_read_capability_status_or_target_never_proposes(self):
        reasons = {"offline": "controller_offline", "stale_status": "stale_status",
                   "unknown_control": "unknown_control", "unsafe_control": "unsafe_control",
                   "missing_read_capability": "read_capability_unavailable",
                   "missing_write_capability": "write_capability_unavailable"}
        for variant, reason in reasons.items():
            with self.subTest(variant=variant):
                result = run_scenario("loxone", variant=variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertNotIn("proposal", result)
                self.assertNotIn("simulation", result)

    def test_bad_synthetic_grant_cannot_change_simulated_state(self):
        reasons = {"denied_approval": "mock_approval_mismatch",
                   "mismatched_approval": "mock_approval_mismatch",
                   "expired_approval": "mock_approval_expired",
                   "replayed_approval": "mock_approval_replayed",
                   "approval_bypass": "mock_approval_mismatch"}
        for variant, reason in reasons.items():
            with self.subTest(variant=variant):
                result = run_scenario("loxone", variant=variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertNotIn("simulation", result)
                self.assertNotEqual(result["verification"], "synthetic_in_memory_only")

    def test_failed_write_mismatch_stale_readback_and_unknown_outcome_never_confirm(self):
        reasons = {"failed_write": "simulated_write_failed", "readback_failed": "readback_failed",
                   "readback_stale": "stale_status", "unknown_outcome": "unknown_simulated_outcome"}
        for variant, reason in reasons.items():
            with self.subTest(variant=variant):
                result = run_scenario("loxone", variant=variant)
                expected = "partial" if variant == "unknown_outcome" else "blocked"
                self.assertEqual((result["status"], result["reason"]), (expected, reason))
                self.assertNotEqual(result["verification"], "synthetic_in_memory_only")
                self.assertNotIn("read_status_mock_readback_verified", result["trace"])

    def test_every_variant_has_no_external_effect_or_publishable_mapping(self):
        from adapters.loxone_e2e_mock import VARIANTS

        for variant in VARIANTS:
            with self.subTest(variant=variant):
                result = run_scenario("loxone", variant=variant)
                self.assertEqual(result["external_effects"], 0)
                self.assertTrue(all(not record["executed"] for record in result["audit"]))
                self.assertTrue(all(not mapping["publishable"] for mapping in result["dashboard_mapping"]))
        with self.assertRaises(ValueError):
            run_scenario("loxone", variant="unknown")


if __name__ == "__main__":
    unittest.main()
