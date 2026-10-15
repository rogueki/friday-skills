"""Offline review of structured invoice fields and non-executable payment previews."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


class InvoiceAdapterError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)  # Never include untrusted invoice contents in diagnostics.
        self.code = code


IBAN_LENGTHS = {"AT": 20, "BE": 16, "CH": 21, "DE": 22, "ES": 24, "FR": 27, "GB": 22, "IT": 27, "LU": 20, "NL": 18, "PL": 28}
CENT = Decimal("0.01")
FIELDS = ("supplier_id", "supplier", "invoice_number", "issue_date", "net", "tax", "gross", "currency", "due_date", "iban")


def _text(value: Any, field: str, limit: int = 160) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 for c in value):
        raise InvoiceAdapterError(f"invalid_{field}")
    return value.strip()


def _money(value: Any, field: str) -> Decimal:
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,10}\.\d{2}", value):
        raise InvoiceAdapterError(f"invalid_{field}")
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise InvoiceAdapterError(f"invalid_{field}") from exc
    return amount


def _date(value: Any, field: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise InvoiceAdapterError(f"invalid_{field}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise InvoiceAdapterError(f"invalid_{field}") from exc


def _iban(value: Any) -> str:
    iban = re.sub(r"\s+", "", _text(value, "iban", 64)).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]+", iban) or len(iban) != IBAN_LENGTHS.get(iban[:2]):
        raise InvoiceAdapterError("invalid_iban")
    remainder = 0
    for char in iban[4:] + iban[:4]:
        digits = char if char.isdigit() else str(ord(char) - 55)
        for digit in digits:
            remainder = (remainder * 10 + int(digit)) % 97
    if remainder != 1:
        raise InvoiceAdapterError("invalid_iban")
    return iban


def _digest(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def duplicate_key(supplier_id: str, invoice_number: str) -> str:
    """Stable key for the same supplier and invoice number; supplied index must be independent."""
    return _digest([_text(supplier_id, "supplier_id"), _text(invoice_number, "invoice_number")])


def _base(skill: str, mode: str, source_hash: str, at: datetime) -> dict[str, Any]:
    return {
        "skill": skill, "mode": mode, "status": "blocked", "summary": "Invoice review blocked",
        "artifacts": [], "actions_taken": [], "actions_proposed": [], "approvals_required": [],
        "warnings": [], "errors": [], "sources": [{"url": f"urn:sha256:{source_hash}", "retrieved_at": at.isoformat()}],
        "verification": [],
    }


def review_invoice(
    fields: dict[str, Any], *, trusted_supplier: dict[str, Any] | None = None,
    prior_invoice_keys: set[str] | None = None, mode: str = "mock", now: datetime | None = None,
) -> dict[str, Any]:
    """Review caller-supplied fields. No PDF/OCR, ledger lookup, bank or network access."""
    if mode not in {"mock", "read_only"}:
        raise InvoiceAdapterError("invalid_mode")
    if not isinstance(fields, dict) or len(json.dumps(fields, default=str)) > 16_384:
        raise InvoiceAdapterError("invalid_input")
    if prior_invoice_keys is not None and (not isinstance(prior_invoice_keys, set) or not all(isinstance(item, str) for item in prior_invoice_keys)):
        raise InvoiceAdapterError("invalid_prior_index")
    at = now or datetime.now(timezone.utc)
    if at.tzinfo is None:
        raise InvoiceAdapterError("invalid_time")
    at = at.astimezone(timezone.utc)
    result = _base("friday-invoice-intake", mode, _digest(fields), at)
    result["sources"][0]["title"] = "caller-supplied structured invoice fields"
    if isinstance(trusted_supplier, dict):
        result["sources"].append({"url": f"urn:sha256:{_digest(trusted_supplier)}", "retrieved_at": at.isoformat(), "title": "caller-supplied supplier record"})
    if isinstance(prior_invoice_keys, set):
        result["sources"].append({"url": f"urn:sha256:{_digest(sorted(prior_invoice_keys))}", "retrieved_at": at.isoformat(), "title": "caller-supplied invoice-key index"})
    if mode == "mock" and fields.get("synthetic") is not True:
        result["errors"].append("mock_requires_synthetic_input")
        return result
    if mode == "read_only" and fields.get("synthetic") is True:
        result["errors"].append("synthetic_input_in_read_only_mode")
        return result
    missing = sorted(set(FIELDS) - fields.keys())
    if missing:
        result["errors"].append("missing_required_fields")
        result["warnings"].extend(f"missing:{name}" for name in missing)
        return result
    try:
        supplier_id = _text(fields["supplier_id"], "supplier_id")
        supplier = _text(fields["supplier"], "supplier")
        number = _text(fields["invoice_number"], "invoice_number")
        issued = _date(fields["issue_date"], "issue_date")
        due = _date(fields["due_date"], "due_date")
        net, tax, gross = (_money(fields[name], name) for name in ("net", "tax", "gross"))
        currency = _text(fields["currency"], "currency")
        iban = _iban(fields["iban"])
    except InvoiceAdapterError as exc:
        result["errors"].append(exc.code)
        return result
    if currency != "EUR":
        result["errors"].append("unsupported_currency")
    if due < issued:
        result["errors"].append("due_before_issue")
    if net + tax != gross:
        result["errors"].append("total_mismatch")
    if "tax_rate_percent" in fields:
        try:
            rate = Decimal(_text(fields["tax_rate_percent"], "tax_rate_percent", 8))
            if not 0 <= rate <= 100 or (net * rate / 100).quantize(CENT) != tax:
                result["errors"].append("tax_mismatch")
        except (InvalidOperation, InvoiceAdapterError):
            result["errors"].append("invalid_tax_rate")
    key = duplicate_key(supplier_id, number)
    if prior_invoice_keys is None:
        result["warnings"].append("duplicate_index_unavailable")
    elif key in prior_invoice_keys:
        result["errors"].append("duplicate_invoice")
    if trusted_supplier is None:
        result["warnings"].append("trusted_supplier_unavailable")
    elif not isinstance(trusted_supplier, dict) or trusted_supplier.get("source_kind") != "independent_supplier_record":
        result["errors"].append("untrusted_supplier_record")
    else:
        try:
            trusted_id = _text(trusted_supplier.get("supplier_id"), "trusted_supplier_id")
            trusted_name = _text(trusted_supplier.get("supplier"), "trusted_supplier_name")
            trusted_iban = _iban(trusted_supplier.get("iban"))
            if trusted_id != supplier_id:
                result["errors"].append("supplier_id_mismatch")
            if trusted_name != supplier:
                result["errors"].append("supplier_name_mismatch")
            if trusted_iban != iban:
                result["errors"].append("bank_details_changed")
            result["verification"].append("bank_details_compared_to_caller_supplied_independent_record")
        except InvoiceAdapterError as exc:
            result["errors"].append(exc.code)
    discount = None
    if any(name in fields for name in ("discount_percent", "discount_base", "discount_deadline")):
        try:
            rate = Decimal(_text(fields.get("discount_percent"), "discount_percent", 8))
            base = _text(fields.get("discount_base"), "discount_base")
            deadline = _date(fields.get("discount_deadline"), "discount_deadline")
            if not 0 <= rate <= 100 or base not in {"net", "gross"} or not issued <= deadline <= due:
                raise InvoiceAdapterError("invalid_discount")
            discount = {"percent": str(rate), "base": base, "deadline": deadline.isoformat()}
        except (InvalidOperation, InvoiceAdapterError):
            result["errors"].append("invalid_discount")
    result["artifacts"].append({
        "type": "invoice_review", "supplier_id": supplier_id, "supplier": supplier,
        "invoice_number": number, "issue_date": issued.isoformat(), "due_date": due.isoformat(),
        "net": str(net), "tax": str(tax), "gross": str(gross), "currency": currency,
        "iban_masked": iban[:4] + "…" + iban[-4:], "duplicate_key": key, "discount": discount,
        "provenance": "caller_supplied_structured_fields; no OCR or original-document verification",
    })
    result["verification"].extend(["iban_mod97_and_country_length_checked", "net_plus_tax_equals_gross_checked", "dates_checked"])
    result["status"] = "blocked" if result["errors"] else "partial" if result["warnings"] else "completed"
    result["summary"] = {"blocked": "Invoice review found blocking discrepancies", "partial": "Invoice fields checked; independent evidence incomplete", "completed": "Structured invoice fields checked"}[result["status"]]
    return result


def prepare_payment(
    fields: dict[str, Any], *, trusted_supplier: dict[str, Any] | None,
    prior_invoice_keys: set[str] | None, intended_date: str, mode: str = "mock", now: datetime | None = None,
) -> dict[str, Any]:
    """Create a masked local preview only; never a bank-ready instruction or transfer."""
    review = review_invoice(fields, trusted_supplier=trusted_supplier, prior_invoice_keys=prior_invoice_keys, mode=mode, now=now)
    at = now or datetime.now(timezone.utc)
    result = _base("friday-payment-preparation", mode, _digest(fields), at.astimezone(timezone.utc))
    result["sources"] = list(review["sources"])
    result["warnings"] = list(review["warnings"])
    result["errors"] = list(review["errors"])
    result["verification"] = list(review["verification"])
    if review["status"] != "completed":
        result["summary"] = "Payment preview blocked by incomplete invoice review"
        return result
    try:
        transfer_date = _date(intended_date, "intended_date")
    except InvoiceAdapterError as exc:
        result["errors"].append(exc.code)
        return result
    invoice = review["artifacts"][0]
    if transfer_date < date.fromisoformat(invoice["issue_date"]):
        result["errors"].append("intended_date_before_issue")
        result["summary"] = "Payment preview blocked by invalid intended date"
        return result
    if transfer_date > date.fromisoformat(invoice["due_date"]):
        result["warnings"].append("intended_date_after_due")
    gross = Decimal(invoice["gross"])
    reduction = Decimal("0.00")
    discount = invoice["discount"]
    if discount and transfer_date <= date.fromisoformat(discount["deadline"]):
        base = Decimal(invoice[discount["base"]])
        reduction = (base * Decimal(discount["percent"]) / 100).quantize(CENT)
    amount = gross - reduction
    result["artifacts"].append({
        "type": "non_executable_payment_preview", "beneficiary": invoice["supplier"],
        "iban_masked": invoice["iban_masked"], "reference": invoice["invoice_number"],
        "currency": "EUR", "gross": str(gross), "discount": str(reduction), "amount": str(amount),
        "intended_date": transfer_date.isoformat(), "discount_formula": "base * percent / 100, rounded to cents",
        "provenance": "reviewed caller-supplied structured fields and independent supplier record",
    })
    result["actions_taken"] = ["local_masked_preview_created"]
    result["verification"].append("discount_and_payment_amount_recomputed")
    result["status"] = "partial" if result["warnings"] else "completed"
    result["summary"] = "Local masked payment preview prepared; no banking action"
    return result
