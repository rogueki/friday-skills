"""Offline invoice arithmetic, provenance, identity and preparation checks."""

import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adapters.invoice import InvoiceAdapterError, duplicate_key, prepare_payment, review_invoice


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "invoices" / "adapter_invoice.json"
NOW = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)


def sample():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class InvoiceAdapterTests(unittest.TestCase):
    def test_valid_invoice_and_discount_deadline(self):
        data = sample()
        review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), now=NOW)
        self.assertEqual(review["status"], "completed")
        self.assertEqual(review["artifacts"][0]["iban_masked"], "DE89…3000")
        self.assertEqual(review["sources"][0]["url"].split(":")[0], "urn")
        early = prepare_payment(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), intended_date="2026-10-20", now=NOW)
        late = prepare_payment(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), intended_date="2026-10-21", now=NOW)
        self.assertEqual((early["status"], early["artifacts"][0]["amount"]), ("completed", "116.62"))
        self.assertEqual(late["artifacts"][0]["amount"], "119.00")
        self.assertNotIn("iban", early["artifacts"][0])
        self.assertEqual(early["actions_taken"], ["local_masked_preview_created"])

    def test_duplicate_and_changed_bank_details_block(self):
        data = sample()
        key = duplicate_key("S-17", "RE-2026-0042")
        review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys={key}, now=NOW)
        self.assertEqual((review["status"], review["errors"]), ("blocked", ["duplicate_invoice"]))
        data["trusted_supplier"]["iban"] = "DE75512108001245126199"
        review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), now=NOW)
        self.assertEqual((review["status"], review["errors"]), ("blocked", ["bank_details_changed"]))
        preview = prepare_payment(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), intended_date="2026-10-20", now=NOW)
        self.assertEqual((preview["status"], preview["artifacts"], preview["actions_taken"]), ("blocked", [], []))
        data = sample()
        data["trusted_supplier"]["supplier"] = "Other Company"
        review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), now=NOW)
        self.assertIn("supplier_name_mismatch", review["errors"])

    def test_arithmetic_tax_iban_and_dates_fail_closed(self):
        for field, replacement, code in [
            ("gross", "118.99", "total_mismatch"), ("tax", "18.99", "total_mismatch"),
            ("tax_rate_percent", "7", "tax_mismatch"), ("iban", "DE89370400440532013001", "invalid_iban"),
            ("due_date", "2026-09-30", "due_before_issue"), ("discount_deadline", "2026-11-01", "invalid_discount"),
        ]:
            with self.subTest(field=field):
                data = sample()
                data["invoice"][field] = replacement
                review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), now=NOW)
                self.assertEqual(review["status"], "blocked")
                self.assertIn(code, review["errors"])

    def test_missing_independent_sources_is_partial_and_cannot_prepare(self):
        data = sample()
        review = review_invoice(data["invoice"], now=NOW)
        self.assertEqual(review["status"], "partial")
        self.assertEqual(set(review["warnings"]), {"duplicate_index_unavailable", "trusted_supplier_unavailable"})
        preview = prepare_payment(data["invoice"], trusted_supplier=None, prior_invoice_keys=None, intended_date="2026-10-20", now=NOW)
        self.assertEqual((preview["status"], preview["actions_taken"]), ("blocked", []))

    def test_date_before_issue_blocks_preview_and_source_time_is_utc(self):
        data = sample()
        local_time = datetime(2026, 10, 15, 14, tzinfo=timezone(timedelta(hours=2)))
        invalid = prepare_payment(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), intended_date="2026-09-30", now=local_time)
        self.assertEqual((invalid["status"], invalid["errors"], invalid["artifacts"], invalid["actions_taken"]), ("blocked", ["intended_date_before_issue"], [], []))
        self.assertTrue(all(source["retrieved_at"] == "2026-10-15T12:00:00+00:00" for source in invalid["sources"]))

    def test_provenance_and_mode_are_explicit(self):
        data = sample()
        data["trusted_supplier"]["source_kind"] = "invoice"
        review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), now=NOW)
        self.assertIn("untrusted_supplier_record", review["errors"])
        self.assertEqual(review_invoice(data["invoice"], mode="read_only", now=NOW)["status"], "blocked")
        real_fields = copy.deepcopy(data["invoice"])
        real_fields.pop("synthetic")
        self.assertEqual(review_invoice(real_fields, mode="mock", now=NOW)["status"], "blocked")
        with self.assertRaises(InvoiceAdapterError):
            review_invoice(real_fields, mode="live", now=NOW)

    def test_malformed_input_does_not_echo_sensitive_text(self):
        data = sample()
        data["invoice"]["iban"] = "SECRET-BANK-DATA"
        review = review_invoice(data["invoice"], trusted_supplier=data["trusted_supplier"], prior_invoice_keys=set(), now=NOW)
        self.assertEqual(review["errors"], ["invalid_iban"])
        self.assertNotIn("SECRET-BANK-DATA", json.dumps(review))
        data["invoice"].pop("supplier")
        review = review_invoice(data["invoice"], now=NOW)
        self.assertEqual(review["errors"], ["missing_required_fields"])


if __name__ == "__main__":
    unittest.main()
