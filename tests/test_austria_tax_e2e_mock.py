"""E2E9 local tax preparation contract; no real tax data or filing."""

import copy
import unittest

from adapters.austria_tax_e2e_mock import run_tax_mock
from shared.runtime import MockRuntime, load_fixture
from shared.scenarios import run_scenario


class AustriaTaxE2EMockTests(unittest.TestCase):
    def test_synthetic_chain_produces_only_a_review_checklist(self):
        result = run_scenario("austria_tax")
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["trace"], ["receipts_read", "categories", "missing_documents",
                                           "finanzonline_draft", "human_review"])
        self.assertEqual(result["evidence_total_eur"], "250.00")
        self.assertEqual(len(result["candidates"]), 5)
        self.assertEqual(set(result["missing_or_uncertain"]), {"uncertain_law", "missing_receipt"})
        self.assertTrue(all(item["eligibility"] == "undetermined" and item["claim_amount_eur"] is None
                            for item in result["candidates"]))
        self.assertTrue(all(item["evidence_id"].startswith("synthetic-") for item in result["candidates"]))
        draft = result["finanzonline_draft"]
        self.assertEqual(draft["filing_status"], "NOT_FILED")
        self.assertIsNone(draft["values_for_filing"])
        self.assertIsNone(draft["field_ids"])
        self.assertEqual(result["submission"], "NOT_ATTEMPTED")
        self.assertTrue(result["review_required"])
        self.assertEqual(result["audit"], [])
        self.assertNotIn("proposal", result)
        self.assertEqual(result["external_effects"], 0)
        self.assertTrue(all(not item["publishable"] for item in result["dashboard_mapping"]))

    def test_negative_variants_fail_closed(self):
        expected = {"missing_receipt": "missing_receipt", "duplicate": "duplicate_document",
                    "changed_hash": "changed_hash", "year_mismatch": "year_mismatch",
                    "stale_rule": "rule_source_stale_or_unknown", "schema_uncertain": "form_schema_uncertain",
                    "sum_mismatch": "evidence_sum_mismatch", "injected_submit": "untrusted_submit_instruction",
                    "unknown_rule": "taxonomy_unverified"}
        for variant, code in expected.items():
            with self.subTest(variant=variant):
                result = run_scenario("austria_tax", variant=variant)
                self.assertIn(code, {issue["code"] for issue in result["issues"]})
                self.assertEqual(result["status"], "partial")
                self.assertEqual(result["submission"], "NOT_ATTEMPTED")
                self.assertEqual(result["audit"], [])
                self.assertEqual(result["external_effects"], 0)
                self.assertNotIn("proposal", result)

    def test_mutated_evidence_cannot_be_treated_as_verified(self):
        data = copy.deepcopy(load_fixture("tax", "cases"))
        data["documents"][0]["sha256"] = "0" * 64
        result, runtime = {}, MockRuntime()
        run_tax_mock(runtime, result, [], context=data)
        self.assertIn("changed_hash", {issue["code"] for issue in result["issues"]})
        self.assertNotIn("family_bonus", {item["kind"] for item in result["candidates"]})
        self.assertEqual(runtime.audit, [])

    def test_unknown_variant_rejected(self):
        with self.assertRaises(ValueError):
            run_scenario("austria_tax", variant="file_now")


if __name__ == "__main__":
    unittest.main()
