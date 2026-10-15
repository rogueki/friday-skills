"""Independent behavior checks for the bounded synthetic §22 composition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from adapters.research_e2e_mock import FIXTURES, run_research_mock


class ResearchE2EMockTests(unittest.TestCase):
    def test_conflicting_independent_primary_quotes_prevent_a_winner(self):
        result = run_research_mock()
        self.assertEqual((result["status"], result["reason"]),
                         ("partial", "material_conflict_and_missing_criteria"))
        self.assertEqual(result["mode"], "mock")
        self.assertEqual((result["network_calls"], result["provider_calls"], result["external_effects"]),
                         (0, 0, 0))
        self.assertEqual(result["audit"], [])
        claims = {row["claim_id"]: row for row in result["claim_ledger"]}
        self.assertEqual(claims["local_cost"]["status"], "mixed")
        self.assertEqual(set(claims["local_cost"]["values"]), {120, 150})
        self.assertEqual(claims["local_cost"]["independent_groups"], ["finance-team", "local-team"])
        self.assertEqual(claims["hosted_cost"]["values"], [90])
        self.assertEqual(claims["hosted_cost"]["independent_groups"], ["hosted-vendor"])
        self.assertTrue(any("#local-cost" in locator for locator in claims["local_cost"]["supporting_passages"]))
        self.assertEqual(len(claims["hosted_cost"]["excluded_passages"]), 1)
        self.assertIn("old-syndication", claims["hosted_cost"]["source_ids"])
        self.assertEqual(len(result["source_ledger"]), 4)
        self.assertTrue(all(row["authenticity"] == "unverified_synthetic" for row in result["source_ledger"]))
        brief = result["brief"]
        self.assertFalse(brief["decision_ready"])
        self.assertIsNone(brief["recommendation"])
        self.assertIsNone(brief["owner_priorities"])
        self.assertFalse(brief["external_action_authorized"])
        self.assertEqual([option["id"] for option in brief["options"]], ["local", "hosted", "status_quo"])
        self.assertEqual(brief["options"][0]["annual_cost_eur"], [120, 150])
        self.assertEqual(brief["options"][1]["annual_cost_eur"], [90])
        self.assertIsNone(brief["options"][2]["annual_cost_eur"])
        self.assertIn("cost", brief["next_reversible_step"])

    def test_manifest_hashes_pin_the_source_bytes(self):
        case = json.loads((FIXTURES / "case.json").read_text(encoding="utf-8"))
        for source in case["sources"]:
            with self.subTest(source=source["id"]):
                self.assertEqual(hashlib.sha256((FIXTURES / source["file"]).read_bytes()).hexdigest(),
                                 source["sha256"])
        self.assertLess(Path(FIXTURES / "local_cost.html").stat().st_size, 1024)

    def test_changed_hash_and_instruction_text_fail_before_brief(self):
        for variant, reason in (("changed_hash", "source_hash_changed"), ("injection", "PolicyError")):
            with self.subTest(variant=variant):
                result = run_research_mock(variant)
                self.assertEqual((result["status"], result["reason"]), ("blocked", reason))
                self.assertNotIn("brief", result)
                self.assertEqual((result["network_calls"], result["provider_calls"], result["external_effects"]),
                                 (0, 0, 0))
                self.assertEqual(result["audit"], [])

    def test_missing_or_stale_primary_blocks_current_price_comparison(self):
        for variant in ("missing_primary", "stale_primary"):
            with self.subTest(variant=variant):
                result = run_research_mock(variant)
                self.assertEqual((result["status"], result["reason"]),
                                 ("blocked", "current_primary_missing"))
                self.assertNotIn("brief", result)
                self.assertEqual(result["external_effects"], 0)

    def test_incompatible_period_is_not_compared_as_an_annual_price(self):
        result = run_research_mock("incompatible_period")
        self.assertEqual((result["status"], result["reason"]),
                         ("blocked", "incompatible_comparison_period"))
        self.assertNotIn("brief", result)
        self.assertEqual(result["external_effects"], 0)

    def test_unknown_variant_has_no_side_effect(self):
        with self.assertRaises(ValueError):
            run_research_mock("live")


if __name__ == "__main__":
    unittest.main()
