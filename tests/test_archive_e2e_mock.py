"""Synthetic E2E6 archive safety and integrity boundaries."""

from hashlib import sha256
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from adapters import archive_e2e_mock as archive
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


class LocalArchiveE2ETests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.source = self.base / "source"
        self.backup = self.base / "backup"
        self.source.mkdir()
        self.backup.mkdir()
        self.payloads = {"a.jpg": b"one", "sub/b.jpg": b"one", "c.png": b"other"}
        for root in (self.source, self.backup):
            (root / "sub").mkdir()
            for relative, data in self.payloads.items():
                (root / relative).write_bytes(data)

    def run_flow(self, **kwargs):
        return archive.run_local_archive_mock(self.source, self.backup,
                                              destination_free_bytes=100, **kwargs)

    def test_real_scan_proposal_stops_at_approval_and_preserves_files(self):
        result = self.run_flow()
        self.assertEqual(result["status"], "waiting_approval", result.get("reason"))
        self.assertEqual(result["inventory"]["count"], 3)
        self.assertEqual(result["inventory"]["bytes"], sum(map(len, self.payloads.values())))
        self.assertEqual(result["duplicate_groups"][0]["ids"], ["f000001", "f000003"])
        self.assertEqual(result["duplicate_groups"][0]["sha256"], sha256(b"one").hexdigest())
        self.assertEqual(result["manifest"]["backup"]["method"],
                         "independent_local_byte_sha256_scan")
        self.assertEqual(result["manifest"]["destination_capacity"],
                         "caller_supplied_for_simulation")
        self.assertFalse(result["approval"]["granted"])
        self.assertFalse(result["proposal"]["executed"])
        self.assertEqual(result["media_integrity"], "unknown_unverified")
        self.assertEqual(result["external_effects"], 0)
        self.assertNotIn("verification", result)
        self.assert_sources_unchanged()

    def test_simulated_grant_rehashes_real_sources_and_copies_in_memory(self):
        result = self.run_flow(simulated_approval=True)
        self.assertEqual(result["status"], "completed", result.get("reason"))
        self.assertEqual(result["approval"]["status"], "simulated_only")
        self.assertFalse(result["approval"]["trusted_host_approval"])
        verification = result["verification"]
        self.assertEqual(verification["scope"], "real_local_input_in_memory_copy")
        self.assertEqual((verification["source_count"], verification["target_count"]), (3, 3))
        self.assertEqual((verification["source_bytes"], verification["target_bytes"]), (11, 11))
        self.assertTrue(verification["sha256_matches"])
        self.assertEqual(result["target_files_written"], 0)
        self.assert_sources_unchanged()

    def test_backup_and_capacity_must_be_independently_known(self):
        (self.backup / "c.png").write_bytes(b"wrong")
        result = self.run_flow()
        self.assertEqual((result["status"], result["reason"]), ("blocked", "backup_unverified"))
        self.assertNotIn("proposal", result)
        (self.backup / "c.png").write_bytes(b"other")
        for capacity, reason in ((None, "capacity_unknown"), (1, "insufficient_capacity")):
            with self.subTest(capacity=capacity):
                result = archive.run_local_archive_mock(self.source, self.backup,
                                                        destination_free_bytes=capacity)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertNotIn("proposal", result)

    def test_partial_scan_never_proposes(self):
        result = self.run_flow(max_files=1)
        self.assertEqual((result["status"], result["reason"]), ("blocked", "incomplete_scan"))
        self.assertNotIn("proposal", result)

    def test_mock_approval_requires_explicit_boolean(self):
        result = self.run_flow(simulated_approval="yes")
        self.assertEqual((result["status"], result["reason"]), ("blocked", "invalid_mock_approval"))
        self.assertNotIn("proposal", result)
        self.assert_sources_unchanged()

    def test_hardlinked_backup_is_not_independent(self):
        target = self.backup / "a.jpg"
        target.unlink()
        try:
            target.hardlink_to(self.source / "a.jpg")
        except (OSError, NotImplementedError):
            self.skipTest("hard links unavailable")
        result = self.run_flow()
        self.assertEqual((result["status"], result["reason"]),
                         ("blocked", "backup_not_independent"))
        self.assertNotIn("proposal", result)

    def test_changed_or_added_source_never_completes(self):
        real_scan = archive.scan_archive
        calls = 0

        def mutate_before_rescan(root, **limits):
            nonlocal calls
            calls += 1
            if calls == 3:
                (self.source / "new.jpg").write_bytes(b"new")
            return real_scan(root, **limits)

        with patch.object(archive, "scan_archive", side_effect=mutate_before_rescan):
            result = self.run_flow()
        self.assertEqual((result["status"], result["reason"]), ("blocked", "source_changed"))
        self.assertNotIn("proposal", result)

    def test_source_change_after_proposal_blocks_mock(self):
        real_scan = archive.scan_archive
        calls = 0

        def mutate_before_approval(root, **limits):
            nonlocal calls
            calls += 1
            if calls == 4:
                (self.source / "a.jpg").write_bytes(b"modified")
            return real_scan(root, **limits)

        with patch.object(archive, "scan_archive", side_effect=mutate_before_approval):
            result = self.run_flow(simulated_approval=True)
        self.assertEqual((result["status"], result["reason"]), ("blocked", "source_changed"))
        self.assertNotIn("verification", result)

    def test_unreadable_source_blocks_before_proposal(self):
        real_open = archive.os.open

        def deny_source(path, flags):
            if Path(path) == self.source / "a.jpg":
                raise PermissionError("controlled denial")
            return real_open(path, flags)

        with patch.object(archive.os, "open", side_effect=deny_source):
            result = self.run_flow()
        self.assertEqual((result["status"], result["reason"]), ("blocked", "incomplete_scan"))
        self.assertNotIn("proposal", result)

    def test_change_after_in_memory_copy_fails_final_scan(self):
        real_scan = archive.scan_archive
        calls = 0

        def mutate_before_final_scan(root, **limits):
            nonlocal calls
            calls += 1
            if calls == 5:
                (self.source / "late.jpg").write_bytes(b"late")
            return real_scan(root, **limits)

        with patch.object(archive, "scan_archive", side_effect=mutate_before_final_scan):
            result = self.run_flow(simulated_approval=True)
        self.assertEqual((result["status"], result["reason"]), ("blocked", "source_changed"))
        self.assertNotIn("verification", result)

    def assert_sources_unchanged(self):
        for root in (self.source, self.backup):
            self.assertEqual({str(path.relative_to(root)).replace("\\", "/"): path.read_bytes()
                              for path in root.rglob("*") if path.is_file()}, self.payloads)
        self.assertEqual(sorted(path.name for path in self.base.iterdir()), ["backup", "source"])


if __name__ == "__main__":
    unittest.main()
