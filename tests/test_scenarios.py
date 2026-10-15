import json
import unittest

from shared.scenarios import run_scenario


class ScenarioTests(unittest.TestCase):
    def test_ten_plan_workflows_remain_local(self):
        names = ("important_mail", "invoice", "meeting", "weather", "family_travel",
                 "photo_archive", "powerpoint", "loxone", "austria_tax", "system_outage")
        for name in names:
            with self.subTest(name=name):
                result = run_scenario(name)
                self.assertEqual(result["mode"], "mock")
                self.assertEqual(result["external_effects"], 0)
                self.assertIn(result["status"], {"completed", "partial", "waiting_approval", "blocked"})
                self.assertFalse(any(record["executed"] for record in result["audit"]))

    def test_mail_injection_quarantines_without_draft_or_send_proposal(self):
        result = run_scenario("important_mail", variant="injection")
        self.assertEqual((result["status"], result["quarantine_id"]), ("blocked", "m-injection"))
        self.assertNotIn("draft", result)
        self.assertNotIn("proposal", result)
        self.assertEqual(result["audit"], [])
        self.assertEqual(result["events"][0]["status"], "blocked")
        clean = run_scenario("important_mail")
        self.assertEqual(clean["status"], "waiting_approval")
        self.assertIn("Lieferung", clean["draft"])
        self.assertEqual(clean["proposal"]["action"], "send_message")

    def test_invoice_discount_and_suspicious_invoice(self):
        clean = run_scenario("invoice")
        self.assertEqual(clean["payment_draft"], {"amount": "196.00", "currency": "EUR", "due": "2026-10-30"})
        self.assertEqual(clean["audit"], [])
        suspicious = run_scenario("invoice", variant="suspicious")
        self.assertEqual(suspicious["status"], "blocked")
        self.assertEqual(set(suspicious["reasons"]), {"duplicate_invoice", "bank_details_changed"})
        self.assertNotIn("payment_draft", suspicious)
        self.assertEqual(suspicious["audit"], [])

    def test_invoice_pdf_e2e_composes_real_local_adapters_without_payment_execution(self):
        for variant, amount, discount, applied in (("default", "116.62", "2.38", True),
                                                   ("after_discount_deadline", "119.00", "0.00", False)):
            with self.subTest(variant=variant):
                result = run_scenario("invoice_pdf_to_payment_draft", variant=variant)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["pdf_review"]["status"], "completed")
                self.assertEqual(result["payment_draft"]["amount"], amount)
                self.assertEqual(result["payment_draft"]["discount"], discount)
                self.assertEqual(result["payment_draft"]["currency"], "EUR")
                self.assertEqual(result["payment_draft"]["type"], "non_executable_payment_preview")
                self.assertEqual(result["invoice_facts"]["due_date"], "2026-10-31")
                self.assertEqual(result["invoice_facts"]["discount_deadline"], "2026-10-20")
                self.assertEqual(result["invoice_facts"]["discount_applied"], applied)
                self.assertEqual([event["status"] for event in result["events"]],
                                 ["working", "completed", "working", "completed"])
                self.assertTrue(all(not mapping["publishable"] for mapping in result["dashboard_mapping"]))
                self.assertEqual(result["external_effects"], 0)
                self.assertEqual(result["audit"], [])
                exposed = json.dumps((result["events"], result["audit"], result["payment_draft"]), ensure_ascii=False)
                self.assertNotIn("DE89370400440532013000", exposed)
                self.assertNotIn("Supplier: Example Supplies GmbH", exposed)
                self.assertNotIn("payment.execute", json.dumps(result, ensure_ascii=False))

    def test_invoice_pdf_e2e_blocks_untrusted_document_or_reference_data(self):
        for variant in ("altered_pdf", "duplicate_invoice", "changed_supplier_bank",
                        "missing_invoice_index", "missing_supplier_record"):
            with self.subTest(variant=variant):
                result = run_scenario("invoice_pdf_to_payment_draft", variant=variant)
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["reason"], "invoice_review_incomplete")
                self.assertNotIn("payment_draft", result)
                self.assertEqual([event["status"] for event in result["events"]], ["working", "blocked"])
                self.assertTrue(all(not mapping["publishable"] for mapping in result["dashboard_mapping"]))
                self.assertEqual(result["external_effects"], 0)
                self.assertEqual(result["audit"], [])
                self.assertNotIn("payment.execute", json.dumps(result, ensure_ascii=False))
        self.assertIn("mock_requires_pinned_pdf_and_synthetic_records",
                      run_scenario("invoice_pdf_to_payment_draft", variant="altered_pdf")["pdf_review"]["errors"])

    def test_calendar_timezone_conflict_is_detected_in_utc(self):
        result = run_scenario("meeting", variant="timezone_conflict")
        self.assertEqual(result["starts_at_utc"], "2026-10-15T12:00:00+00:00")
        self.assertEqual(result["conflicts"], ["c-conflict"])
        self.assertEqual(result["status"], "partial")
        self.assertEqual(run_scenario("meeting")["status"], "completed")

    def test_stale_weather_is_not_reported_as_current(self):
        stale = run_scenario("weather", variant="stale")
        self.assertEqual((stale["status"], stale["reason"]), ("partial", "stale_weather"))
        self.assertNotIn("answer", stale)
        clean = run_scenario("weather")
        self.assertEqual(clean["status"], "completed")
        self.assertIn("Wien", clean["answer"])

    def test_stale_travel_quote_does_not_create_booking_proposal(self):
        stale = run_scenario("family_travel", variant="stale_quote")
        self.assertEqual((stale["status"], stale["reason"]), ("partial", "no_current_quote"))
        self.assertNotIn("proposal", stale)
        self.assertEqual(stale["audit"], [])
        clean = run_scenario("family_travel")
        self.assertEqual(clean["proposal"]["payload"]["kind"], "budget")
        self.assertEqual(clean["proposal"]["risk_tier"], 3)

    def test_bad_archive_hash_blocks_migration_proposal(self):
        bad = run_scenario("photo_archive", variant="bad_hash")
        self.assertEqual((bad["status"], bad["invalid_ids"]), ("blocked", ["b"]))
        self.assertNotIn("proposal", bad)
        self.assertEqual(bad["audit"], [])
        clean = run_scenario("photo_archive")
        self.assertEqual(len(clean["duplicate_groups"]), 1)
        self.assertEqual(clean["proposal"]["risk_tier"], 2)
        self.assertEqual(clean["status"], "waiting_approval")

    def test_loxone_readback_failure_never_reports_success(self):
        bad = run_scenario("loxone", variant="readback_failed")
        self.assertEqual((bad["status"], bad["reason"]), ("blocked", "readback_failed"))
        self.assertNotIn("proposal", bad)
        self.assertEqual(bad["audit"], [])
        clean = run_scenario("loxone")
        self.assertEqual(clean["status"], "waiting_approval")
        self.assertEqual(clean["verification"], "not_executed")

    def test_unknown_tax_rule_requires_review_and_cannot_submit(self):
        unknown = run_scenario("austria_tax", variant="unknown_rule")
        self.assertEqual(unknown["missing_or_uncertain"], ["novel_deduction"])
        self.assertTrue(unknown["review_required"])
        self.assertEqual(unknown["status"], "partial")
        self.assertNotIn("proposal", unknown)
        self.assertEqual(unknown["audit"], [])
        self.assertIn("uncertain_law", run_scenario("austria_tax")["missing_or_uncertain"])

    def test_offline_adapter_blocks_and_only_maps_local_warning(self):
        outage = run_scenario("system_outage", variant="offline")
        self.assertEqual(outage["status"], "blocked")
        self.assertEqual(outage["degraded_capability"], "mail")
        self.assertFalse(outage["dashboard_mapping"]["publishable"])
        self.assertNotIn("proposal", outage)
        self.assertEqual(outage["audit"], [])

    def test_unknown_variant_rejected(self):
        with self.assertRaises(ValueError):
            run_scenario("invoice", variant="unrecognized")


if __name__ == "__main__":
    unittest.main()
