"""Offline tests of the routing-evaluation harness, never model-routing claims."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.evaluate_hermes_routing import evaluate, load_cases


class RoutingEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "registry").mkdir()
        names = [("friday-a", "jarvis-a"), ("friday-b", "jarvis-b")]
        records = []
        for name, legacy in names:
            folder = self.root / "skills" / name
            (folder / "tests").mkdir(parents=True)
            (folder / "SKILL.md").write_text("---\nname: " + name + "\n---\n", encoding="utf-8")
            (folder / "tests/cases.json").write_text(json.dumps({
                "skill": name,
                "cases": [{"id": case_id, "request": f"Request {name} {case_id}",
                           "expected": expected} for case_id, expected in (
                               ("positive", "select"), ("negative", "reject"),
                               ("collision", "defer"), ("ambiguity", "defer"))],
            }), encoding="utf-8")
            records.append({"name": name, "legacy_plan_name": legacy,
                            "path": f"skills/{name}/SKILL.md", "trigger": f"Trigger {name}"})
        (self.root / "registry/skills.json").write_text(json.dumps({"skills": records}), encoding="utf-8")

    def test_no_provider_does_not_invoke_or_mark_cases(self):
        report = evaluate(self.root)
        self.assertEqual(report["case_total"], 8)
        self.assertEqual(report["attempted"], 0)
        self.assertEqual(report["counts"], {"PASS": 0, "FAIL": 0, "NOT_RUN": 8})

    def test_explicit_cap_and_synthetic_match_are_not_model_pass(self):
        seen = []

        def scripted(inputs):
            seen.append(inputs)
            return {"decision": "select", "selected_skills": ["jarvis-a"],
                    "evidence": {"kind": "synthetic"}}

        report = evaluate(self.root, route_decision=scripted, max_cases=1)
        self.assertEqual(len(seen), 1)
        self.assertNotIn("expected", seen[0])
        self.assertNotIn("case_id", seen[0])
        self.assertEqual(report["counts"], {"PASS": 0, "FAIL": 0, "NOT_RUN": 8})
        self.assertTrue(report["cases"][0]["synthetic_match"])
        self.assertEqual(report["cases"][0]["selected_skills"], ["friday-a"])

    def test_claimed_model_evidence_scores_decisions_and_collision(self):
        answers = iter(("select", "reject", "defer"))

        def claimed_model(inputs):
            decision = next(answers)
            selected = [inputs["candidate_skill"]] if decision == "select" else []
            return {"decision": decision, "selected_skills": selected,
                    "evidence": {"kind": "model_inference_claimed", "provider": "local",
                                 "model": "openrouter/~test-model", "response_id": "trace-123"}}

        report = evaluate(self.root, route_decision=claimed_model, max_cases=3)
        self.assertEqual(report["counts"], {"PASS": 3, "FAIL": 0, "NOT_RUN": 5})
        self.assertEqual(report["cases"][2]["actual"], "defer")

    def test_mismatch_fails_and_invalid_selected_candidate_does_not_pass(self):
        def mismatch(inputs):
            return {"decision": "reject", "selected_skills": [],
                    "evidence": {"kind": "model_inference_claimed", "provider": "local",
                                 "model": "test-model", "response_id": "trace-123"}}

        report = evaluate(self.root, route_decision=mismatch, max_cases=1)
        self.assertEqual(report["counts"], {"PASS": 0, "FAIL": 1, "NOT_RUN": 7})

        def inconsistent(inputs):
            return {"decision": "select", "selected_skills": ["friday-b"]}

        report = evaluate(self.root, route_decision=inconsistent, max_cases=1)
        self.assertEqual(report["cases"][0]["error_type"], "ValueError")
        self.assertEqual(report["counts"]["PASS"], 0)

    def test_error_message_and_raw_request_are_not_in_evidence(self):
        def failing(inputs):
            raise RuntimeError("secret-provider-token")

        report = evaluate(self.root, route_decision=failing, max_cases=1)
        rendered = json.dumps(report)
        self.assertNotIn("secret-provider-token", rendered)
        self.assertNotIn("Request friday-a positive", rendered)
        self.assertEqual(report["cases"][0]["error_type"], "RuntimeError")

    def test_cap_and_catalog_validation(self):
        with self.assertRaises(ValueError):
            evaluate(self.root, route_decision=lambda _: {}, max_cases=None)
        with self.assertRaises(ValueError):
            evaluate(self.root, route_decision=lambda _: {}, max_cases=0)
        with self.assertRaises(ValueError):
            evaluate(self.root, route_decision=lambda _: {}, max_cases=9)
        with self.assertRaises(ValueError):
            evaluate(self.root, max_cases=1)
        cases, catalog, aliases = load_cases(self.root)
        self.assertEqual(len(cases), 8)
        self.assertEqual(len(catalog), 2)
        self.assertEqual(aliases["jarvis-b"], "friday-b")


if __name__ == "__main__":
    unittest.main()
