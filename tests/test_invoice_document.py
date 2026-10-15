"""Offline original-PDF intake checks with actual pypdf parsing."""

import hashlib
import io
import unittest
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from adapters.invoice import duplicate_key
from adapters.invoice_document import InvoiceDocumentError, extract_invoice_pdf, review_invoice_pdf


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "invoices" / "valid-skonto.pdf"
NOW = datetime(2026, 10, 15, 12, tzinfo=timezone.utc)
SUPPLIER = {"source_kind": "independent_supplier_record", "supplier_id": "S-17",
            "supplier": "Example Supplies GmbH", "iban": "DE89370400440532013000"}
LINES = [
    "Supplier: Example Supplies GmbH", "Invoice number: RE-2026-0042", "Issue date: 2026-10-01",
    "Net amount: 100.00", "Tax amount: 19.00", "Gross amount: 119.00", "Currency: EUR",
    "IBAN: DE89370400440532013000", "Due date: 2026-10-31", "Discount: 2%",
    "Discount deadline: 2026-10-20", "Discount base: gross",
]


def pdf_with_lines(lines, *, encrypted=False, altered_metadata=False):
    writer = PdfWriter()
    page = writer.add_blank_page(width=595, height=842)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    escaped = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in lines]
    stream = DecodedStreamObject()
    stream.set_data(("BT /F1 11 Tf 42 800 Td 15 TL\n" + "\n".join(f"({line}) Tj T*" for line in escaped) + "\nET").encode("ascii"))
    page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("test-only")
    if altered_metadata:
        writer.add_metadata({"/Producer": "distinct synthetic document"})
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


class InvoiceDocumentTests(unittest.TestCase):
    def test_plan_section_31_pinned_mock_is_completed_without_payment(self):
        original = FIXTURE.read_bytes()
        result = review_invoice_pdf(original, supplier_id="S-17", trusted_supplier=SUPPLIER,
                                    prior_invoice_keys=set(), mode="mock", now=NOW)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["artifacts"][0]["extracted"], {"currency": "EUR", "has_skonto": True})
        self.assertEqual(result["artifacts"][1]["review"]["status"], "completed")
        self.assertEqual(result["actions_taken"], [])
        self.assertEqual(result["actions_proposed"], [])
        self.assertEqual(result["approvals_required"], [])
        self.assertNotIn("payment.execute", str(result))
        same_labels = PdfReader(io.BytesIO(original)).pages[0].extract_text().splitlines()
        rebuilt = pdf_with_lines(same_labels, altered_metadata=True)
        self.assertNotEqual(rebuilt, original)
        self.assertEqual(extract_invoice_pdf(rebuilt)["fields"], extract_invoice_pdf(original)["fields"])
        rejected = review_invoice_pdf(rebuilt, supplier_id="S-17", trusted_supplier=SUPPLIER,
                                      prior_invoice_keys=set(), mode="mock", now=NOW)
        self.assertEqual(rejected["status"], "blocked")
        self.assertIn("mock_requires_pinned_pdf_and_synthetic_records", rejected["errors"])
        missing_record = review_invoice_pdf(original, supplier_id="S-17", trusted_supplier=None,
                                            prior_invoice_keys=set(), mode="mock", now=NOW)
        self.assertEqual(missing_record["status"], "blocked")

    def test_original_fixture_extracts_page_evidence_and_stays_partial(self):
        original = FIXTURE.read_bytes()
        extracted = extract_invoice_pdf(original)
        self.assertEqual(extracted["pdf_sha256"], hashlib.sha256(original).hexdigest())
        self.assertEqual(extracted["fields"]["gross"], "119.00")
        self.assertEqual(extracted["fields"]["discount_percent"], "2")
        self.assertEqual(extracted["evidence"]["iban"]["page"], 1)
        result = review_invoice_pdf(original, supplier_id="S-17", trusted_supplier=SUPPLIER,
                                    prior_invoice_keys=set(), now=NOW)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["artifacts"][1]["review"]["status"], "partial")
        self.assertEqual(result["actions_taken"], [])
        self.assertEqual(result["actions_proposed"], [])
        self.assertIn("sender not authenticated", result["sources"][0]["title"])
        self.assertNotIn("payment.execute", str(result))

    def test_duplicate_and_independent_bank_change_block(self):
        original = FIXTURE.read_bytes()
        duplicate = review_invoice_pdf(original, supplier_id="S-17", trusted_supplier=SUPPLIER,
                                       prior_invoice_keys={duplicate_key("S-17", "RE-2026-0042")}, now=NOW)
        self.assertEqual(duplicate["status"], "blocked")
        self.assertIn("duplicate_invoice", duplicate["errors"])
        changed = dict(SUPPLIER, iban="DE75512108001245126199")
        review = review_invoice_pdf(original, supplier_id="S-17", trusted_supplier=changed,
                                    prior_invoice_keys=set(), now=NOW)
        self.assertIn("bank_details_changed", review["errors"])

    def test_missing_and_ambiguous_labels_never_guess(self):
        missing = extract_invoice_pdf(pdf_with_lines([line for line in LINES if not line.startswith("IBAN:")]))
        self.assertEqual(missing["status"], "partial")
        self.assertIn("iban", missing["missing"])
        ambiguous = review_invoice_pdf(pdf_with_lines(LINES + ["IBAN: DE75512108001245126199"]),
                                       supplier_id="S-17", trusted_supplier=SUPPLIER, prior_invoice_keys=set(), now=NOW)
        self.assertEqual(ambiguous["status"], "blocked")
        self.assertIn("ambiguous:iban", ambiguous["errors"])
        self.assertNotIn("iban", ambiguous["artifacts"][0]["fields"])

    def test_image_only_invalid_encrypted_and_oversized_fail_closed(self):
        image_only = extract_invoice_pdf(pdf_with_lines([]))
        self.assertEqual(image_only["status"], "partial")
        self.assertIn("invoice_number", image_only["missing"])
        for document, code in [(b"%PDF-this is not a PDF", "invalid_pdf"),
                               (pdf_with_lines(LINES, encrypted=True), "encrypted_pdf"),
                               (b"%PDF-" + b"x" * 2_000_000, "invalid_pdf_size")]:
            with self.subTest(code=code), self.assertRaises(InvoiceDocumentError) as raised:
                extract_invoice_pdf(document)
            self.assertEqual(raised.exception.code, code)

    def test_decoded_page_stream_limit(self):
        oversized_stream = pdf_with_lines(["x" * 1_000_001])
        self.assertLess(len(oversized_stream), 2_000_000)
        with self.assertRaises(InvoiceDocumentError) as raised:
            extract_invoice_pdf(oversized_stream)
        self.assertEqual(raised.exception.code, "page_stream_too_large")


if __name__ == "__main__":
    unittest.main()
