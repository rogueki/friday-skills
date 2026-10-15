"""Regression tests for independent offline adapter evidence."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import os
import unittest
from unittest.mock import patch

from scripts.evaluate_skill_adapters import ROOT, evaluate
from shared.scenarios import run_scenario


class SkillAdapterEvaluationTests(unittest.TestCase):
    def _assert_counts(self, report: dict, other_pass: int, **extra: int) -> None:
        presentation = next(x for x in report["cases"] if x["case_id"] == "presentation-deck-render")
        allowed = {"PASS"} if os.environ.get("FRIDAY_REQUIRE_PRESENTATION_RENDER") == "1" else {"PASS", "PARTIAL"}
        self.assertIn(presentation["status"], allowed)
        expected = {"PASS": other_pass, **extra}
        actual = Counter(x["status"] for x in report["cases"] if x["case_id"] != "presentation-deck-render")
        self.assertEqual(dict(actual), expected)

    def test_real_local_workflows_and_negative_paths_execute(self):
        report = evaluate()
        self.assertEqual(report["evidence_kind"], "offline_adapter_execution")
        self._assert_counts(report, 106)
        self.assertEqual(len({x["scenario"] for x in report["cases"]}), 10)
        self.assertEqual(report["coverage_gaps"], {})
        for scenario, coverage in report["scenario_coverage"].items():
            self.assertEqual(coverage["source_variants"], coverage["declared"])
            self.assertEqual(coverage["passed"], coverage["declared"] if scenario != "powerpoint" else
                             int(next(x for x in report["cases"] if x["scenario"] == "powerpoint")["status"] == "PASS"))
        self.assertEqual(report["hermes_routing"], "NOT_RUN")
        self.assertEqual(report["individual_skill_runtime"], "NOT_RUN")
        for record in report["cases"]:
            with self.subTest(case=record["case_id"]):
                self.assertIn(record["status"], {"PASS", "PARTIAL"})
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
        self._assert_counts(report, 105, FAIL=1)
        self.assertEqual(next(x for x in report["cases"] if x["case_id"] == "mail-draft")["reason"],
                         "executed audit action")

    def test_changed_artifact_fails_even_if_status_and_trace_match(self):
        def altered(name, *, variant):
            result = deepcopy(run_scenario(name, variant=variant))
            if name == "invoice_pdf_to_payment_draft" and variant == "default":
                result["payment_draft"]["amount"] = "0.00"
            return result

        report = evaluate(ROOT, runner=altered)
        self._assert_counts(report, 105, FAIL=1)
        self.assertEqual(next(x for x in report["cases"] if x["case_id"] == "invoice-preview")["reason"],
                         "masked discount preview")

    def test_missing_optional_parser_is_explicit_skip(self):
        def no_parser(name, *, variant):
            if name == "invoice_pdf_to_payment_draft":
                return {"scenario": name, "variant": variant, "reason": "pdf_parser_unavailable"}
            return run_scenario(name, variant=variant)

        report = evaluate(ROOT, runner=no_parser)
        self._assert_counts(report, 99, SKIP=7)
        self.assertEqual(report["individual_skill_runtime"], "NOT_RUN")

    def test_unexpected_adapter_error_is_recorded(self):
        def broken(name, *, variant):
            if name == "weather" and variant == "stale":
                raise RuntimeError("adapter failed")
            return run_scenario(name, variant=variant)

        report = evaluate(ROOT, runner=broken)
        self._assert_counts(report, 105, ERROR=1)
        self.assertIn("RuntimeError", next(x for x in report["cases"] if x["case_id"] == "weather-stale")["reason"])

    def test_rejected_grant_cannot_report_mock_delivery(self):
        def altered(name, *, variant):
            result = deepcopy(run_scenario(name, variant=variant))
            if name == "important_mail_e2e" and variant == "forged_approval":
                result["mock_send"] = {"transport": "none", "delivered": False}
            return result

        report = evaluate(ROOT, runner=altered)
        self._assert_counts(report, 105, FAIL=1)
        record = next(x for x in report["cases"] if x["case_id"] == "important-mail-forged-approval")
        self.assertIn("forbidden artifact", record["reason"])

    def test_tax_injection_must_remain_visible_as_issue(self):
        def altered(name, *, variant):
            result = deepcopy(run_scenario(name, variant=variant))
            if name == "austria_tax" and variant == "injected_submit":
                result["issues"] = [x for x in result["issues"] if x["code"] != "untrusted_submit_instruction"]
            return result

        report = evaluate(ROOT, runner=altered)
        self._assert_counts(report, 105, FAIL=1)
        record = next(x for x in report["cases"] if x["case_id"] == "austria-tax-injected-submit")
        self.assertIn("missing issue", record["reason"])

    def test_new_source_variant_is_reported_as_coverage_gap(self):
        from scripts.evaluate_skill_adapters import _declared_variants

        def extra(source, scenario):
            variants = _declared_variants(source, scenario)
            return variants | {"new_unbound_variant"} if scenario == "weather" else variants

        with patch("scripts.evaluate_skill_adapters._declared_variants", side_effect=extra):
            report = evaluate(ROOT)
        self._assert_counts(report, 106)
        self.assertEqual(report["coverage_gaps"]["weather"]["untested_variants"], ["new_unbound_variant"])

    def test_missing_presentation_renderer_is_partial_only_when_optional(self):
        with patch("adapters.presentation_mock.find_renderer", return_value=None):
            optional = evaluate(ROOT, require_presentation_render=False)
            required = evaluate(ROOT, require_presentation_render=True)
        optional_case = next(x for x in optional["cases"] if x["case_id"] == "presentation-deck-render")
        required_case = next(x for x in required["cases"] if x["case_id"] == "presentation-deck-render")
        self.assertEqual(optional_case["status"], "PARTIAL")
        self.assertEqual(optional_case["observed_status"], "partial")
        self.assertEqual(required_case["status"], "FAIL")
        self.assertEqual(required_case["reason"], "presentation renderer required")

    def test_presentation_hash_mutation_fails_even_with_matching_trace(self):
        def altered(name, *, variant):
            result = run_scenario(name, variant=variant)
            if name == "powerpoint":
                result["deck_sha256"] = "0" * 64
            return result

        with patch("adapters.presentation_mock.find_renderer", return_value=None):
            report = evaluate(ROOT, runner=altered, require_presentation_render=False)
        record = next(x for x in report["cases"] if x["case_id"] == "presentation-deck-render")
        self.assertEqual(record["status"], "FAIL")
        self.assertEqual(record["reason"], "presentation deck hash")

    def test_failed_presentation_render_is_not_optional_success(self):
        from adapters.presentation_mock import PresentationMockError

        with patch("adapters.presentation_mock.render_deck", side_effect=PresentationMockError("render_failed")):
            report = evaluate(ROOT, require_presentation_render=False)
        record = next(x for x in report["cases"] if x["case_id"] == "presentation-deck-render")
        self.assertEqual(record["status"], "FAIL")
        self.assertEqual(record["reason"], "presentation renderer failed rather than unavailable")


if __name__ == "__main__":
    unittest.main()
