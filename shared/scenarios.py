"""Executable local examples for the ten plan workflows. All data is synthetic."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from shared.runtime import MockRuntime, load_fixture, untrusted_text, dashboard_mapping
from shared.policy import PolicyError


def _instant(value: str) -> datetime:
    instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if instant.tzinfo is None:
        raise ValueError("fixture timestamp must include a timezone")
    return instant.astimezone(timezone.utc)


def _fixture(kind: str, default_name: str, variant: str, allowed: set[str]) -> dict[str, Any]:
    if variant not in allowed | {"default"}:
        raise ValueError(f"unknown {kind} variant: {variant}")
    return load_fixture(kind, default_name if variant == "default" else variant)


def _invoice_pdf_to_payment_draft(runtime: MockRuntime, result: dict[str, Any], trace: list[str], variant: str) -> None:
    """Compose the real local PDF and payment adapters over pinned synthetic inputs."""
    allowed = {"default", "after_discount_deadline", "altered_pdf", "duplicate_invoice",
               "changed_supplier_bank", "missing_invoice_index", "missing_supplier_record"}
    if variant not in allowed:
        raise ValueError(f"unknown invoice_pdf_to_payment_draft variant: {variant}")

    # pypdf is an optional dependency; other scenarios must remain importable without it.
    try:
        from adapters.invoice_document import InvoiceDocumentError, review_invoice_pdf
    except ModuleNotFoundError as exc:
        if exc.name != "pypdf":
            raise
        result.update(status="blocked", reason="pdf_parser_unavailable")
        event = runtime.event("friday-invoice-intake", "blocked", "Local PDF parser unavailable", 0)
        result["dashboard_mapping"] = [dashboard_mapping(event)]
        return
    from adapters.invoice import duplicate_key, prepare_payment

    source = load_fixture("invoices", "adapter_invoice")
    supplier = dict(source["trusted_supplier"])
    prior_keys = set(source["prior_invoice_keys"])
    if variant == "changed_supplier_bank":
        supplier["iban"] = "DE75512108001245126199"
    elif variant == "missing_supplier_record":
        supplier = None
    if variant == "duplicate_invoice":
        independent_invoice = source["invoice"]
        prior_keys.add(duplicate_key(independent_invoice["supplier_id"], independent_invoice["invoice_number"]))
    elif variant == "missing_invoice_index":
        prior_keys = None

    pdf_bytes = (Path(__file__).resolve().parents[1] / "fixtures" / "invoices" / "valid-skonto.pdf").read_bytes()
    if variant == "altered_pdf":
        pdf_bytes += b"\n% altered-copy\n"
    trace.extend(["original_pdf_bytes_loaded", "independent_synthetic_records_loaded"])
    runtime.event("friday-invoice-intake", "working", "Local invoice PDF review started", 0)
    try:
        review = review_invoice_pdf(pdf_bytes, supplier_id=source["invoice"]["supplier_id"],
                                    trusted_supplier=supplier, prior_invoice_keys=prior_keys,
                                    mode="mock", now=runtime.now)
    except InvoiceDocumentError as exc:
        result.update(status="blocked", reason=exc.code)
        runtime.event("friday-invoice-intake", "blocked", "Local invoice PDF review blocked", 0)
        result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
        return

    extraction = review["artifacts"][0]
    result["pdf_review"] = {"status": review["status"], "pdf_sha256": extraction["pdf_sha256"],
                            "page_count": extraction["page_count"], "errors": review["errors"],
                            "warnings": review["warnings"]}
    if review["status"] != "completed":
        result.update(status="blocked", reason="invoice_review_incomplete")
        runtime.event("friday-invoice-intake", "blocked", "Local invoice PDF review blocked", 0)
        trace.append("pdf_review_blocked")
        result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
        return

    # The payment adapter receives fields extracted from the reviewed PDF, not from the structured fixture.
    fields = dict(extraction["fields"])
    fields.update(supplier_id=source["invoice"]["supplier_id"], synthetic=True)
    trace.extend(["pdf_extracted", "invoice_review_completed"])
    runtime.event("friday-invoice-intake", "completed", "Local invoice PDF review completed", 1)
    runtime.event("friday-payment-preparation", "working", "Local payment preview started", 0)
    intended_date = "2026-10-21" if variant == "after_discount_deadline" else "2026-10-15"
    payment = prepare_payment(fields, trusted_supplier=supplier, prior_invoice_keys=prior_keys,
                              intended_date=intended_date, mode="mock", now=runtime.now)
    if payment["status"] != "completed" or payment["actions_proposed"] or payment["approvals_required"]:
        result.update(status="blocked", reason="payment_preview_incomplete", payment_errors=payment["errors"])
        runtime.event("friday-payment-preparation", "blocked", "Local payment preview blocked", 0)
    else:
        draft = payment["artifacts"][0]
        if draft["type"] != "non_executable_payment_preview":
            raise ValueError("payment adapter returned an unexpected artifact")
        discount = review["artifacts"][1]["review"]["artifacts"][0]["discount"]
        result.update(status="completed", payment_draft=draft,
                      invoice_facts={"due_date": fields["due_date"], "discount_deadline": discount["deadline"],
                                     "discount_percent": discount["percent"], "discount_base": discount["base"],
                                     "discount_applied": draft["discount"] != "0.00"})
        trace.extend(["skonto_checked", "due_date_checked", "masked_payment_draft"])
        runtime.event("friday-payment-preparation", "completed", "Local masked payment preview completed", 1)
    result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]


def run_scenario(name: str, *, variant: str = "default") -> dict[str, Any]:
    runtime = MockRuntime()
    trace: list[str] = []
    result: dict[str, Any] = {"scenario": name, "variant": variant, "mode": "mock", "external_effects": 0}

    if name == "important_mail_e2e":
        from adapters.mail_e2e_mock import run_important_mail_e2e

        run_important_mail_e2e(runtime, result, trace, variant)
    elif name == "important_mail":
        data = _fixture("mail", "messages", variant, {"injection"})
        mail = data["messages"][0] if variant != "default" else next(x for x in data["messages"] if x["kind"] == "delivery_problem")
        trace.append("mail_received")
        try:
            untrusted_text(mail["body"])
        except PolicyError:
            result.update(status="blocked", quarantine_id=mail["id"], reason="untrusted_instruction")
            runtime.event("friday-executive-mail-manager", "blocked", "Mail quarantined", 0)
        else:
            if mail["priority"] != "P1":
                result.update(status="partial", reason="not_priority_one")
            else:
                trace += ["classified_P1", "thread_summary", "calendar_context", "dashboard_alert"]
                draft = f"Antwortentwurf auf {mail['subject']}"
                result["proposal"] = runtime.propose("send_message", "synthetic-recipient", draft, tier=2)
                runtime.event("friday-mail-draft-writer", "waiting_approval", "Antwortentwurf wartet", 0.7, task_id="mock-task-1")
                result.update(status="waiting_approval", draft=draft)
    elif name == "invoice":
        data = _fixture("invoices", "cases", variant, {"suspicious"})
        invoice = data["invoices"][0] if variant != "default" else next(x for x in data["invoices"] if x["kind"] == "skonto")
        trace.append("invoice_loaded")
        known_ids = {x["id"] for x in load_fixture("invoices", "cases")["invoices"]}
        reasons = []
        if invoice.get("duplicate_of") in known_ids:
            reasons.append("duplicate_invoice")
        if invoice.get("iban_changed"):
            reasons.append("bank_details_changed")
        if not invoice.get("due"):
            reasons.append("missing_due_date")
        try:
            amount = Decimal(invoice["amount"])
            discount = Decimal(str(invoice.get("discount_percent", 0)))
            if amount <= 0 or not 0 <= discount <= 100:
                reasons.append("invalid_amount_or_discount")
            if "line_sum" in invoice and Decimal(invoice["line_sum"]) != amount:
                reasons.append("total_mismatch")
        except (InvalidOperation, KeyError):
            reasons.append("invalid_amount")
        if reasons:
            result.update(status="blocked", reasons=reasons)
            runtime.event("friday-invoice-intake", "blocked", "Invoice requires review", 0)
        else:
            net = (amount * (Decimal(100) - discount) / 100).quantize(Decimal("0.01"))
            result["payment_draft"] = {"amount": str(net), "currency": invoice["currency"], "due": invoice["due"]}
            trace += ["amount_extracted", "skonto_calculated", "due_date_checked", "payment_draft"]
            runtime.event("friday-invoice-intake", "completed", "Rechnung vorbereitet", 1)
            result["status"] = "completed"
    elif name == "invoice_pdf_to_payment_draft":
        _invoice_pdf_to_payment_draft(runtime, result, trace, variant)
    elif name == "meeting":
        if variant == "timezone_conflict":
            data = load_fixture("calendar", "timezone_conflict")
            meeting = data["meeting"]
            start, end = _instant(meeting["starts_at"]), _instant(meeting["ends_at"])
            conflicts = [item["id"] for item in data["events"] if start < _instant(item["ends_at"]) and _instant(item["starts_at"]) < end]
            result.update(status="partial" if conflicts else "completed", starts_at_utc=start.isoformat(), conflicts=conflicts)
            trace.append("calendar_read")
        else:
            from adapters.meeting_briefing_mock import run_meeting_mock

            run_meeting_mock(runtime, result, trace, variant)
    elif name == "weather":
        from adapters.weather_e2e_mock import run_weather_mock

        run_weather_mock(runtime, result, trace, variant=variant)
    elif name == "family_travel":
        from adapters.travel_e2e_mock import run_travel_mock

        run_travel_mock(runtime, result, trace, variant=variant)
    elif name == "photo_archive":
        from adapters.archive_e2e_mock import run_archive_mock

        run_archive_mock(runtime, result, trace, variant=variant)
    elif name == "powerpoint":
        from adapters.presentation_mock import run_mock

        brief = load_fixture("presentations", "brief")
        trace += ["brief", "synthetic_storyline", "pptx_built", "ooxml_checked"]
        presentation = run_mock(brief)
        result.update(presentation)
        if presentation.get("rendered"):
            trace += ["office_cli_render", "all_pdf_pages_rasterized", "nonblank_pages_checked"]
    elif name == "loxone":
        from adapters.loxone_e2e_mock import run_loxone_mock

        run_loxone_mock(runtime, result, trace, variant=variant)
    elif name == "austria_tax":
        cases = _fixture("tax", "cases", variant, {"unknown_rule"})["cases"]
        missing = [x["kind"] for x in cases if x.get("document_present") is False or not x.get("source_date") or x.get("rule_known") is False]
        trace += ["receipts_read", "categories", "missing_documents", "finanzonline_draft", "human_review"]
        result.update(missing_or_uncertain=missing, status="partial" if missing else "completed", review_required=bool(missing))
    elif name == "system_outage":
        adapters = _fixture("system", "adapters", variant, {"offline"})
        mail_status = adapters["mail"]["status"]
        if mail_status != "healthy":
            event = runtime.event("friday-capability-and-health-check", "blocked", f"Mail-Adapter {mail_status}", 0)
            result.update(status="blocked", degraded_capability="mail", dashboard_mapping=dashboard_mapping(event), recovery_plan="inspect_adapter")
            trace += ["adapter_offline", "capability_degraded", "skill_blocked", "dashboard_warning_local"]
        else:
            result["status"] = "completed"
    else:
        raise ValueError(f"unknown scenario: {name}")

    result["trace"] = trace
    result["events"] = runtime.records
    result["audit"] = runtime.audit
    return result
