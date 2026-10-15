"""Offline funding eligibility contract example; no official program or adapter is implied."""

from datetime import date
import unittest

from shared.runtime import load_fixture


def assess_synthetic_case(program: dict, applicant: dict, as_of: date) -> str:
    """Apply only the synthetic fixture's explicit rules, with uncertainty fail closed."""
    if program["availability"] != "synthetic_open":
        return "undetermined"
    if not program.get("source_url") or not program.get("source_retrieved_at"):
        return "undetermined"
    if not (date.fromisoformat(program["rules_effective_from"]) <= as_of <= date.fromisoformat(program["rules_effective_until"])):
        return "undetermined"
    if applicant["region"] not in program["regions"]:
        return "ineligible"
    if applicant["type"] not in program["applicant_types"]:
        return "ineligible"
    if applicant["project_type"] not in program["project_types"]:
        return "ineligible"
    if applicant["eligible_cost_eur"] < program["minimum_eligible_cost_eur"]:
        return "ineligible"
    if not set(program["required_evidence"]).issubset(applicant["evidence"]):
        return "undetermined"
    if program["application_before_order"]:
        if not applicant["order_date"] or not applicant["application_date"]:
            return "undetermined"
        if date.fromisoformat(applicant["order_date"]) <= date.fromisoformat(applicant["application_date"]):
            return "ineligible"
    return "potential_fit"


class SyntheticGrantsFixtureTests(unittest.TestCase):
    def setUp(self):
        self.fixture = load_fixture("grants", "heat_pump_cases")
        self.program = self.fixture["program"]
        self.as_of = date.fromisoformat(self.fixture["as_of"])

    def test_cases_enforce_region_order_and_missing_evidence(self):
        self.assertTrue(self.fixture["synthetic"])
        self.assertEqual(self.program["source_url"].split("/")[2], "example.invalid")
        for case in self.fixture["cases"]:
            with self.subTest(case=case["id"]):
                self.assertEqual(
                    assess_synthetic_case(self.program, case["applicant"], self.as_of),
                    case["expected"],
                )
        self.assertEqual({case["expected"] for case in self.fixture["cases"]},
                         {"potential_fit", "ineligible", "undetermined"})

    def test_stale_or_unavailable_rules_cannot_yield_positive_fit(self):
        applicant = self.fixture["cases"][0]["applicant"]
        self.assertEqual(assess_synthetic_case(self.program, applicant, date(2028, 1, 1)), "undetermined")
        self.assertEqual(assess_synthetic_case({**self.program, "source_retrieved_at": None}, applicant, self.as_of),
                         "undetermined")
        self.assertEqual(assess_synthetic_case({**self.program, "availability": "unknown"}, applicant, self.as_of),
                         "undetermined")


if __name__ == "__main__":
    unittest.main()
