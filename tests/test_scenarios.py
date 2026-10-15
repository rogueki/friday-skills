import unittest

from shared.scenarios import run_scenario


class ScenarioTests(unittest.TestCase):
    def test_all_ten_plan_workflows_are_mock_only(self):
        names = ("important_mail", "invoice", "meeting", "weather", "family_travel",
                 "photo_archive", "powerpoint", "loxone", "austria_tax", "system_outage")
        for name in names:
            with self.subTest(name=name):
                result = run_scenario(name)
                self.assertEqual(result["mode"], "mock")
                self.assertEqual(result["external_effects"], 0)
                self.assertGreaterEqual(len(result["trace"]), 5)
                self.assertFalse(any(item.get("executed") for item in result["audit"]))

    def test_invoice_extracts_discount_but_never_pays(self):
        result = run_scenario("invoice")
        self.assertEqual(result["payment_draft"]["amount"], "196.00")
        self.assertIn("no_payment", result["trace"])
        self.assertNotIn("payment_execute", result["trace"])

    def test_high_risk_flows_remain_proposals(self):
        for name in ("family_travel", "photo_archive", "loxone"):
            with self.subTest(name=name):
                result = run_scenario(name)
                self.assertEqual(result["status"], "waiting_approval")
                self.assertFalse(result["proposal"]["executed"])
        self.assertEqual(run_scenario("family_travel")["proposal"]["risk_tier"], 3)
        self.assertEqual(run_scenario("photo_archive")["proposal"]["risk_tier"], 3)

    def test_tax_does_not_submit_and_outage_blocks(self):
        tax = run_scenario("austria_tax")
        self.assertIn("no_submission", tax["trace"])
        self.assertIn("uncertain_law", tax["missing_or_uncertain"])
        outage = run_scenario("system_outage")
        self.assertEqual(outage["status"], "blocked")
        self.assertFalse(outage["dashboard_mapping"]["publishable"])


if __name__ == "__main__":
    unittest.main()
