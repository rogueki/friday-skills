"""Regression tests for independent offline adapter evidence."""

from __future__ import annotations

from copy import deepcopy
import unittest

from scripts.evaluate_skill_adapters import ROOT, evaluate
from shared.scenarios import run_scenario


class SkillAdapterEvaluationTests(unittest.TestCase):
    def test_real_local_workflows_and_negative_paths_execute(self):
        report = evaluate()
        self.assertEqual(report["evidence_kind"], "offline_adapter_execution")
        self.assertEqual(report["counts"], {"PASS": 18})
        self.assertEqual(len({x["scenario"] for x in report["cases"]}), 9)
        self.assertEqual(report["hermes_routing"], "NOT_RUN")
        self.assertEqual(report["individual_skill_runtime"], "NOT_RUN")
        for record in report["cases"]:
            with self.subTest(case=record["case_id"]):
                self.assertEqual(record["status"], "PASS")
                self.assertEqual(len(record["trace_sha256"]), 64)
                self.assertTrue(any(path.endswith("SKILL.md") for path in record["source_sha256"]))
                self.assertTrue(any(path.startswith("fixtures/") for path in record["source_sha256"]))

    def test_completed_workflow_with_unapproved_effect_fails(self):
        def altered(name, *, variant):
            result = deepcopy(run_scenario(name, variant=variant))
            if name == "important_mail_e2e" and variant == "default":
                result["audit"][0]["executed"] = True
            return result

        report = evaluate(ROOT, runner=altered)
        self.assertEqual(report["counts"], {"FAIL": 1, "PASS": 17})
        self.assertEqual(report["cases"][0]["reason"], "executed audit action")

    def test_changed_artifact_fails_even_if_status_and_trace_match(self):
        def altered(name, *, variant):
            result = deepcopy(run_scenario(name, variant=variant))
            if name == "invoice_pdf_to_payment_draft" and variant == "default":
                result["payment_draft"]["amount"] = "0.00"
            return result

        report = evaluate(ROOT, runner=altered)
        self.assertEqual(report["counts"], {"FAIL": 1, "PASS": 17})
        self.assertEqual(next(x for x in report["cases"] if x["case_id"] == "invoice-preview")["reason"],
                         "masked discount preview")

    def test_missing_optional_parser_is_explicit_skip(self):
        def no_parser(name, *, variant):
            if name == "invoice_pdf_to_payment_draft":
                return {"scenario": name, "variant": variant, "reason": "pdf_parser_unavailable"}
            return run_scenario(name, variant=variant)

        report = evaluate(ROOT, runner=no_parser)
        self.assertEqual(report["counts"], {"SKIP": 2, "PASS": 16})
        self.assertEqual(report["individual_skill_runtime"], "NOT_RUN")

    def test_unexpected_adapter_error_is_recorded(self):
        def broken(name, *, variant):
            if name == "weather" and variant == "stale":
                raise RuntimeError("adapter failed")
            return run_scenario(name, variant=variant)

        report = evaluate(ROOT, runner=broken)
        self.assertEqual(report["counts"], {"ERROR": 1, "PASS": 17})
        self.assertIn("RuntimeError", next(x for x in report["cases"] if x["case_id"] == "weather-stale")["reason"])


if __name__ == "__main__":
    unittest.main()
