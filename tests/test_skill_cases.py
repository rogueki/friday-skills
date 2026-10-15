"""Contract tests for the offline per-skill test declarations."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from scripts.run_skill_cases import MATRIX, ROOT, check_skill, run


class SkillCaseTests(unittest.TestCase):
    def test_all_skill_contracts_and_matrix(self):
        report, errors = run()
        self.assertEqual(errors, [])
        self.assertEqual(report["skills"], 105)
        self.assertEqual({category: len(checks) for category, checks in MATRIX.items()},
                         {"trigger": 4, "functional": 8, "security": 7,
                          "policy": 5, "output": 5})
        self.assertEqual(sum(report["counts"].values()), 105 * 29)
        self.assertGreater(report["counts"]["NOT_RUN"], report["counts"]["PASS"])
        self.assertEqual(report["live_skill_runtime"], "NOT_RUN")

    def test_high_risk_skills_use_relevant_denied_mutations(self):
        registry = json.loads((ROOT / "registry/skills.json").read_text(encoding="utf-8"))
        high_risk = [item for item in registry["skills"] if item["max_risk_tier"] >= 2]
        self.assertGreaterEqual(len(high_risk), 10)
        for item in high_risk:
            path = ROOT / item["path"]
            cases = json.loads((path.parent / "tests/cases.json").read_text(encoding="utf-8"))
            denial = next(case for case in cases["contract_cases"] if case["id"] == "external-write-denied")
            with self.subTest(skill=item["name"]):
                self.assertGreaterEqual(denial["expected"]["risk_tier"], item["max_risk_tier"])
                self.assertIn(denial["input"]["action"], denial["forbidden"])
                self.assertEqual(check_skill(path.parent / "tests/cases.json"), [])

    def test_changed_capability_manifest_is_rejected(self):
        path = ROOT / "skills/finance/friday-invoice-intake/tests/cases.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        altered = copy.deepcopy(data)
        altered["contract_cases"][0]["capabilities"]["required"] = []
        original = Path.read_text

        def read_selected(file, *args, **kwargs):
            if file == path:
                return json.dumps(altered)
            return original(file, *args, **kwargs)

        with patch.object(Path, "read_text", read_selected):
            self.assertIn("mock-result: logical capabilities differ from registry", check_skill(path))

    def test_claimed_live_adapter_is_rejected(self):
        path = ROOT / "skills/core/friday-approval-policy/tests/cases.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["contract_cases"][0]["capabilities"]["live_available"] = True
        original = Path.read_text

        def read_selected(file, *args, **kwargs):
            if file == path:
                return json.dumps(data)
            return original(file, *args, **kwargs)

        with patch.object(Path, "read_text", read_selected):
            self.assertIn("mock-result: test must not claim an available adapter", check_skill(path))


if __name__ == "__main__":
    unittest.main()
