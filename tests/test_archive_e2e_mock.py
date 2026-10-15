"""Synthetic E2E6 archive safety and integrity boundaries."""

import unittest

from shared.policy import action_fingerprint, risk_tier
from shared.scenarios import run_scenario


class ArchiveE2ETests(unittest.TestCase):
    def test_default_stops_at_exact_tier_two_approval(self):
        result = run_scenario("photo_archive")
        self.assertEqual(result["status"], "waiting_approval")
        self.assertEqual(result["inventory"]["count"], 3)
        self.assertEqual(result["inventory"]["bytes"], 36)
        self.assertEqual(result["duplicate_groups"][0]["ids"], ["a", "b"])
        self.assertEqual(result["duplicate_groups"][0]["method"], "byte_sha256")
        manifest = result["manifest"]
        self.assertEqual(manifest["file_count"], 3)
        self.assertEqual(manifest["source_bytes"], 36)
        self.assertEqual(manifest["required_free_bytes"], 72)
        self.assertTrue(all(entry["rollback"]["source_preserved"] for entry in manifest["entries"]))
        self.assertEqual(len({entry["target"].casefold() for entry in manifest["entries"]}), 3)
        self.assertFalse(manifest["overwrite"] or manifest["delete_originals"])
        proposal = result["proposal"]
        self.assertEqual((proposal["action"], proposal["risk_tier"]), ("archive_copy", 2))
        self.assertEqual(proposal["manifest_hash"], action_fingerprint("archive_copy", "archive", manifest))
        self.assertEqual(proposal["idempotency_key"], f"synthetic-{proposal['manifest_hash'][:16]}")
        self.assertFalse(proposal["executed"])
        self.assertFalse(result["approval"]["granted"])
        self.assertFalse(result["approval"]["trusted_host_approval"])
        self.assertEqual(result["external_effects"], 0)
        self.assertTrue(all(not item["publishable"] for item in result["dashboard_mapping"]))
        self.assertNotIn("verification", result)

    def test_explicit_mock_approval_copies_only_in_memory_and_rehashes(self):
        result = run_scenario("photo_archive", variant="mock_approved")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["approval"]["status"], "simulated_only")
        self.assertFalse(result["approval"]["trusted_host_approval"])
        self.assertEqual(result["verification"], {
            "scope": "full_synthetic_in_memory", "expected_count": 3, "source_count": 3,
            "target_count": 3, "expected_bytes": 36, "source_bytes": 36,
            "target_bytes": 36, "bad_ids": [], "source_preserved": True,
            "sha256_matches": True,
        })
        self.assertEqual(result["external_effects"], 0)
        self.assertFalse(any(record["executed"] for record in result["audit"]))
        self.assertTrue(all(not item["publishable"] for item in result["dashboard_mapping"]))

    def test_bad_source_or_plan_blocks_before_proposal(self):
        cases = {
            "bad_hash": ("integrity_failure", ["b"]),
            "missing_source": ("integrity_failure", ["b"]),
            "unreadable_source": ("integrity_failure", ["b"]),
            "path_escape": ("unsafe_path", None),
            "collision": ("target_collision", None),
            "insufficient_capacity": ("insufficient_capacity", None),
            "missing_backup": ("backup_unverified", None),
        }
        for variant, (reason, invalid_ids) in cases.items():
            with self.subTest(variant=variant):
                result = run_scenario("photo_archive", variant=variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                if invalid_ids is not None:
                    self.assertEqual(result["invalid_ids"], invalid_ids)
                self.assertNotIn("proposal", result)
                self.assertEqual(result["audit"], [])
                self.assertEqual(result["external_effects"], 0)

    def test_mock_grant_failures_never_complete(self):
        reasons = {"stale_approval": "mock_approval_expired",
                   "mismatched_approval": "mock_approval_mismatch",
                   "denied_approval": "mock_approval_mismatch",
                   "replayed_approval": "mock_approval_replayed",
                   "corrupt_target": "post_copy_integrity_failure",
                   "partial_copy": "post_copy_integrity_failure"}
        for variant, reason in reasons.items():
            with self.subTest(variant=variant):
                result = run_scenario("photo_archive", variant=variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertTrue(result["simulation_failed"])
                self.assertNotIn("verification", result)
                self.assertEqual(result["external_effects"], 0)
                self.assertTrue(all(not item["publishable"] for item in result["dashboard_mapping"]))

    def test_policy_preserves_generic_mass_action_tier_three(self):
        self.assertEqual(risk_tier("archive_copy"), 2)
        self.assertEqual(risk_tier("mass_action"), 3)
        self.assertEqual(risk_tier("mass_delete"), 3)


if __name__ == "__main__":
    unittest.main()
