"""Bounded extraction from a digitally generated invoice PDF, without OCR or network access."""

from __future__ import annotations

import hashlib
import io
import re
import zlib
from datetime import datetime, timezone
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from adapters.invoice import review_invoice


MAX_PDF_BYTES = 2_000_000
MAX_PAGES = 8
MAX_PAGE_STREAM_BYTES = 1_000_000
MAX_PAGE_TEXT_CHARS = 40_000
MAX_TOTAL_TEXT_CHARS = 120_000
MOCK_PDF_SHA256 = "ed7d87b98562608f03f2b981cde6101faf5afdbba1ca719d1df7fa13521783cd"
MOCK_SUPPLIER = {"source_kind": "independent_supplier_record", "supplier_id": "S-17",
                 "supplier": "Example Supplies GmbH", "iban": "DE89370400440532013000"}

LABELS = {
    "supplier": ("Lieferant", "Supplier"),
    "invoice_number": ("Rechnungsnummer", "Invoice number"),
    "issue_date": ("Rechnungsdatum", "Issue date"),
    "service_period": ("Leistungszeitraum", "Service period"),
    "net": ("Netto", "Net amount"),
    "tax": ("Umsatzsteuer", "Tax amount"),
    "gross": ("Brutto", "Gross amount"),
    "currency": ("Währung", "Currency"),
    "iban": ("IBAN",),
    "bic": ("BIC",),
    "reference": ("Verwendungszweck", "Payment reference"),
    "due_date": ("Fälligkeit", "Due date"),
    "discount_percent": ("Skonto", "Discount"),
    "discount_deadline": ("Skontofrist", "Discount deadline"),
    "discount_base": ("Skontobasis", "Discount base"),
}
REQUIRED = frozenset(("supplier", "invoice_number", "issue_date", "net", "tax", "gross", "currency", "iban", "due_date"))
AMOUNTS = frozenset(("net", "tax", "gross"))
DATES = frozenset(("issue_date", "due_date", "discount_deadline"))
ALIAS = {label.casefold(): key for key, labels in LABELS.items() for label in labels}
LABEL_LINE = re.compile(r"^([^:\n]{2,40}):\s*(.{1,160})$")


class InvoiceDocumentError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _normalize(key: str, value: str) -> str:
    value = value.strip()
    if key in AMOUNTS:
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}", value):
            return value.replace(".", "").replace(",", ".")
        if re.fullmatch(r"\d{1,10}[.,]\d{2}", value):
            return value.replace(",", ".")
        raise InvoiceDocumentError(f"invalid_{key}")
    if key in DATES:
        if re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", value):
            day, month, year = value.split(".")
            return f"{year}-{month}-{day}"
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        raise InvoiceDocumentError(f"invalid_{key}")
    if key == "discount_percent":
        if not re.fullmatch(r"\d{1,3}(?:[,.]\d{1,2})?\s*%", value):
            raise InvoiceDocumentError("invalid_discount_percent")
        return value.rstrip("% ").replace(",", ".")
    if key == "currency":
        return value.upper()
    if key == "discount_base":
        return {"netto": "net", "brutto": "gross"}.get(value.casefold(), value.casefold())
    return value


def extract_invoice_pdf(pdf_bytes: bytes) -> dict[str, Any]:
    """Extract only unique, explicitly labelled lines; PDF bytes remain the source of record."""
    if not isinstance(pdf_bytes, bytes) or not 0 < len(pdf_bytes) <= MAX_PDF_BYTES:
        raise InvoiceDocumentError("invalid_pdf_size")
    if not pdf_bytes.startswith(b"%PDF-"):
        raise InvoiceDocumentError("invalid_pdf")
    document_hash = hashlib.sha256(pdf_bytes).hexdigest()
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes), strict=True)
        if reader.is_encrypted:
            raise InvoiceDocumentError("encrypted_pdf")
        page_count = len(reader.pages)
        if not 0 < page_count <= MAX_PAGES:
            raise InvoiceDocumentError("invalid_page_count")
        candidates: dict[str, list[dict[str, Any]]] = {}
        total_text = 0
        for page_number, page in enumerate(reader.pages, 1):
            contents = page.get_contents()
            if contents is None:
                continue
            # pypdf 6 has its own decompression guard. This second bound limits text parsing.
            stream_bytes = contents.get_data()
            if len(stream_bytes) > MAX_PAGE_STREAM_BYTES:
                raise InvoiceDocumentError("page_stream_too_large")
            page_text = page.extract_text() or ""
            if len(page_text) > MAX_PAGE_TEXT_CHARS:
                raise InvoiceDocumentError("page_text_too_large")
            total_text += len(page_text)
            if total_text > MAX_TOTAL_TEXT_CHARS:
                raise InvoiceDocumentError("document_text_too_large")
            for line_number, raw_line in enumerate(page_text.splitlines(), 1):
                line = raw_line.strip()
                matched = LABEL_LINE.fullmatch(line)
                if not matched:
                    continue
                key = ALIAS.get(matched.group(1).strip().casefold())
                if key:
                    candidates.setdefault(key, []).append({"value": matched.group(2).strip(), "page": page_number,
                                                              "line": line_number, "label": matched.group(1).strip()})
    except InvoiceDocumentError:
        raise
    except (PyPdfError, ValueError, TypeError, KeyError, OSError, OverflowError, zlib.error) as exc:
        raise InvoiceDocumentError("invalid_pdf") from exc
    ambiguous = sorted(key for key, items in candidates.items() if len(items) != 1)
    fields: dict[str, str] = {}
    evidence: dict[str, dict[str, Any]] = {}
    invalid: list[str] = []
    for key, items in candidates.items():
        if len(items) != 1:
            continue
        try:
            fields[key] = _normalize(key, items[0]["value"])
            evidence[key] = {"page": items[0]["page"], "line": items[0]["line"],
                             "label": items[0]["label"]}
        except InvoiceDocumentError:
            invalid.append(key)
    missing = sorted(REQUIRED - fields.keys() - set(ambiguous) - set(invalid))
    return {
        "pdf_sha256": document_hash,
        "page_count": page_count,
        "fields": fields,
        "evidence": evidence,
        "missing": missing,
        "ambiguous": ambiguous,
        "invalid": sorted(invalid),
        "status": "blocked" if ambiguous or invalid else "partial" if missing else "extracted",
        "parser": "pypdf-labelled-lines-v1",
        "sender_authenticated": False,
    }


def review_invoice_pdf(
    pdf_bytes: bytes, *, supplier_id: str, trusted_supplier: dict[str, Any] | None = None,
    prior_invoice_keys: set[str] | None = None, mode: str = "read_only", now: datetime | None = None,
) -> dict[str, Any]:
    """Combine PDF field evidence with independent data; complete only for the pinned mock fixture."""
    if mode not in {"mock", "read_only"}:
        raise InvoiceDocumentError("invalid_mode")
    extraction = extract_invoice_pdf(pdf_bytes)
    at = now or datetime.now(timezone.utc)
    if at.tzinfo is None:
        raise InvoiceDocumentError("invalid_time")
    at = at.astimezone(timezone.utc)
    source = {"url": f"urn:sha256:{extraction['pdf_sha256']}", "retrieved_at": at.isoformat(),
              "title": "original supplied PDF bytes; sender not authenticated"}
    result: dict[str, Any] = {
        "skill": "friday-invoice-intake", "mode": mode, "status": "blocked",
        "summary": "Invoice PDF requires review", "artifacts": [{"type": "invoice_pdf_extraction", **extraction}],
        "actions_taken": [], "actions_proposed": [], "approvals_required": [],
        "warnings": [], "errors": [], "sources": [source], "verification": ["original_pdf_bytes_sha256", "page_label_evidence_recorded"],
    }
    result["warnings"].extend(f"missing:{name}" for name in extraction["missing"])
    result["errors"].extend(f"ambiguous:{name}" for name in extraction["ambiguous"])
    result["errors"].extend(f"invalid:{name}" for name in extraction["invalid"])
    result["artifacts"][0]["extracted"] = {
        "currency": extraction["fields"].get("currency"),
        "has_skonto": all(key in extraction["fields"] for key in ("discount_percent", "discount_deadline", "discount_base")),
    }
    if mode == "mock":
        fixture_matched = (extraction["pdf_sha256"] == MOCK_PDF_SHA256 and supplier_id == "S-17"
                           and trusted_supplier == MOCK_SUPPLIER and prior_invoice_keys == set())
        if not fixture_matched:
            result["errors"].append("mock_requires_pinned_pdf_and_synthetic_records")
            return result
        result["verification"].append("pinned_synthetic_fixture_and_records_checked")
    if extraction["status"] != "extracted":
        result["status"] = "blocked" if result["errors"] else "partial"
        return result
    fields = dict(extraction["fields"])
    fields["supplier_id"] = supplier_id
    if mode == "mock":
        fields["synthetic"] = True
    review = review_invoice(fields, trusted_supplier=trusted_supplier, prior_invoice_keys=prior_invoice_keys,
                            mode=mode, now=at)
    if mode == "read_only" and review["status"] == "completed":
        review["status"] = "partial"
        review["summary"] = "Structured PDF text checked; document authenticity remains unverified"
        review["warnings"].append("document_authenticity_unverified")
    result["artifacts"].append({"type": "structured_invoice_review", "review": review})
    result["warnings"].extend(review["warnings"])
    if mode == "read_only":
        result["warnings"].append("pdf_text_and_sender_authenticity_require_human_review")
    result["errors"].extend(review["errors"])
    result["verification"].extend(review["verification"])
    result["status"] = review["status"]
    if mode == "mock" and result["status"] == "completed":
        result["summary"] = "Pinned synthetic invoice fixture checked; no payment executed"
    return result
