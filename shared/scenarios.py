"""Executable local examples for the ten plan workflows. All data is synthetic."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from shared.runtime import MockRuntime, load_fixture, route_request, untrusted_text, dashboard_mapping
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


def run_scenario(name: str, *, variant: str = "default") -> dict[str, Any]:
    runtime = MockRuntime()
    trace: list[str] = []
    result: dict[str, Any] = {"scenario": name, "variant": variant, "mode": "mock", "external_effects": 0}

    if name == "important_mail":
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
    elif name == "meeting":
        data = _fixture("calendar", "events", variant, {"timezone_conflict"})
        if variant == "default":
            meeting = next(x for x in data["events"] if x["kind"] == "soon")
            relevant_mail = next(x for x in load_fixture("mail", "messages")["messages"] if x["kind"] == "meeting_question")
            result.update(status="completed", summary=f"{meeting['starts_at']}: {relevant_mail['subject']}")
            trace += ["calendar_read", "meeting_briefing", "related_mail", "open_tasks_checked"]
        else:
            meeting = data["meeting"]
            start, end = _instant(meeting["starts_at"]), _instant(meeting["ends_at"])
            conflicts = [item["id"] for item in data["events"] if start < _instant(item["ends_at"]) and _instant(item["starts_at"]) < end]
            result.update(status="partial" if conflicts else "completed", starts_at_utc=start.isoformat(), conflicts=conflicts)
            trace.append("calendar_read")
    elif name == "weather":
        route = route_request("Wie wird das Wetter?")
        weather = _fixture("weather", "current", variant, {"stale"})
        if route["skill"] != "friday-weather":
            result.update(status="blocked", reason="routing_failed")
        elif runtime.now - _instant(weather["observed_at"]) > timedelta(hours=2):
            result.update(status="partial", reason="stale_weather", location=weather["location"])
        else:
            result.update(status="completed", answer=f"{weather['location']}: {weather['temperature_c']} °C, {weather['condition']} (Mock)")
            trace += ["weather_route", "default_location", "mock_weather", "local_voice_text"]
    elif name == "family_travel":
        travel = _fixture("travel", "cases", variant, {"stale_quote"})
        available = [x for x in travel["options"] if x["available"]]
        result["party"] = travel["party"]
        fresh = [x for x in available if "quoted_at" not in x or runtime.now - _instant(x["quoted_at"]) <= timedelta(hours=24)]
        if not fresh:
            result.update(status="partial", reason="no_current_quote")
        else:
            best = min(fresh, key=lambda x: x["price_eur"])
            result["proposal"] = runtime.propose("booking", "synthetic-trip", best, tier=3)
            result["status"] = "waiting_approval"
            trace += ["profile", "mock_research", "comparison", "itinerary", "booking_draft", "hard_approval_required"]
    elif name == "photo_archive":
        files = _fixture("media", "cases", variant, {"bad_hash"})["files"]
        trace += ["read_only_scan", "inventory"]
        invalid = [item["id"] for item in files if item.get("planned_for_migration") and (not item["valid"] or item.get("actual_hash", item["hash"]) != item["hash"])]
        if invalid:
            result.update(status="blocked", reason="integrity_failure", invalid_ids=invalid)
        else:
            counts = Counter(item["hash"] for item in files if item["valid"])
            groups = sorted(hash_ for hash_, count in counts.items() if count > 1)
            result["duplicate_hashes"] = groups
            result["proposal"] = runtime.propose("mass_action", "synthetic-archive", groups, tier=3)
            result["status"] = "waiting_approval"
            trace += ["duplicate_groups", "reorganization_plan", "approval_required", "mock_migration_plan"]
    elif name == "powerpoint":
        brief = load_fixture("presentations", "brief")
        trace += ["brief", "mock_research", "storyline", "deck_outline", "windows_worker_mock", "render_fixture", "qa"]
        result["slides"] = brief["slides"] if brief["rendered"] and brief["worker"] == "mock" else 0
        result["status"] = "completed" if result["slides"] else "blocked"
    elif name == "loxone":
        device = _fixture("loxone", "status", variant, {"readback_failed"})
        trace.append("status_read")
        result["original_state"] = device["state"]
        if not device["online"] or device.get("readback_ok") is False:
            result.update(status="blocked", reason="readback_failed")
        elif device["allow_mock_write"]:
            result["proposal"] = runtime.propose("smart_home_write", device["device"], {"state": "on"}, tier=2)
            result.update(status="waiting_approval", verification="not_executed")
            trace += ["state_answer", "switch_request", "policy_review", "approval_required", "mock_write_proposal"]
        else:
            result.update(status="blocked", reason="write_not_allowed")
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
