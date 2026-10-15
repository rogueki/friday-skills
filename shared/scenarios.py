"""Executable local examples for the ten plan workflows. All data is synthetic."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any

from shared.runtime import MockRuntime, load_fixture, route_request, untrusted_text, dashboard_mapping
from shared.policy import PolicyError


def run_scenario(name: str) -> dict[str, Any]:
    runtime = MockRuntime()
    trace: list[str] = []
    result: dict[str, Any] = {"scenario": name, "mode": "mock", "external_effects": 0}

    if name == "important_mail":
        mail = next(x for x in load_fixture("mail", "messages")["messages"] if x["kind"] == "delivery_problem")
        assert mail["priority"] == "P1"
        untrusted_text(mail["body"])
        trace += ["mail_received", "classified_P1", "thread_summary", "calendar_context"]
        runtime.event("friday-executive-mail-manager", "working", "Mail eingegangen", 0.1, task_id="mock-task-1")
        trace.append("dashboard_alert")
        draft = f"Antwortentwurf auf {mail['subject']}"
        trace.append("reply_draft")
        runtime.event("friday-mail-draft-writer", "waiting_approval", "Antwortentwurf wartet", 0.7, task_id="mock-task-1")
        trace.append("approval_required")
        result["proposal"] = runtime.propose("send_message", "synthetic-recipient", draft, tier=2)
        trace += ["mock_send_proposal", "audit"]
        result["status"] = "waiting_approval"
    elif name == "invoice":
        invoice = next(x for x in load_fixture("invoices", "cases")["invoices"] if x["kind"] == "skonto")
        amount = Decimal(invoice["amount"])
        discount = amount * Decimal(invoice["discount_percent"]) / 100
        trace += ["invoice_loaded", "amount_extracted", "skonto_calculated", "due_date_checked", "payment_draft"]
        result["payment_draft"] = {"amount": str(amount - discount), "currency": invoice["currency"], "due": invoice["due"]}
        runtime.event("friday-invoice-intake", "completed", "Rechnung vorbereitet", 1)
        trace += ["dashboard_local_record", "no_payment"]
        result["status"] = "completed"
    elif name == "meeting":
        meeting = next(x for x in load_fixture("calendar", "events")["events"] if x["kind"] == "soon")
        relevant_mail = next(x for x in load_fixture("mail", "messages")["messages"] if x["kind"] == "meeting_question")
        trace += ["calendar_read", "meeting_briefing", "related_mail", "open_tasks_checked", "result"]
        result["summary"] = f"{meeting['starts_at']}: {relevant_mail['subject']}"
        result["status"] = "completed"
    elif name == "weather":
        route = route_request("Wie wird das Wetter?")
        weather = load_fixture("weather", "current")
        assert route["skill"] == "friday-weather"
        trace += ["weather_route", "default_location", "mock_weather", "local_voice_text", "no_briefing"]
        result["answer"] = f"{weather['location']}: {weather['temperature_c']} °C, {weather['condition']} (Mock)"
        result["status"] = "completed"
    elif name == "family_travel":
        travel = load_fixture("travel", "cases")
        available = [x for x in travel["options"] if x["available"]]
        best = min(available, key=lambda x: x["price_eur"])
        trace += ["profile", "mock_research", "comparison", "itinerary", "booking_draft", "hard_approval_required", "no_booking"]
        result["party"] = travel["party"]
        result["proposal"] = runtime.propose("booking", "synthetic-trip", best, tier=3)
        result["status"] = "waiting_approval"
    elif name == "photo_archive":
        files = load_fixture("media", "cases")["files"]
        counts = Counter(x["hash"] for x in files if x["valid"])
        groups = [hash_ for hash_, count in counts.items() if count > 1]
        trace += ["read_only_scan", "inventory", "duplicate_groups", "reorganization_plan", "approval_required", "mock_migration_plan", "integrity_check"]
        result["duplicate_hashes"] = groups
        result["proposal"] = runtime.propose("mass_action", "synthetic-archive", groups, tier=3)
        result["status"] = "waiting_approval"
    elif name == "powerpoint":
        brief = load_fixture("presentations", "brief")
        trace += ["brief", "mock_research", "storyline", "deck_outline", "windows_worker_mock", "render_fixture", "qa"]
        result["slides"] = brief["slides"] if brief["rendered"] and brief["worker"] == "mock" else 0
        result["status"] = "completed" if result["slides"] else "blocked"
    elif name == "loxone":
        device = load_fixture("loxone", "status")
        trace += ["status_read", "state_answer", "switch_request", "policy_review", "approval_required", "mock_write_proposal", "readback_unchanged"]
        result["original_state"] = device["state"]
        result["proposal"] = runtime.propose("smart_home_write", device["device"], {"state": "on"}, tier=2)
        result["status"] = "waiting_approval"
    elif name == "austria_tax":
        cases = load_fixture("tax", "cases")["cases"]
        missing = [x["kind"] for x in cases if x.get("document_present") is False or x.get("source_date") is None]
        trace += ["receipts_read", "categories", "missing_documents", "finanzonline_draft", "human_review", "no_submission"]
        result["missing_or_uncertain"] = missing
        result["status"] = "partial"
    elif name == "system_outage":
        adapters = load_fixture("system", "adapters")
        assert adapters["mail"]["status"] == "offline"
        trace += ["adapter_offline", "capability_degraded", "skill_blocked"]
        event = runtime.event("friday-capability-and-health-check", "blocked", "Mail-Adapter offline", 0)
        result["dashboard_mapping"] = dashboard_mapping(event)
        trace += ["dashboard_warning_local", "recovery_plan"]
        result["status"] = "blocked"
    else:
        raise ValueError(f"unknown scenario: {name}")

    result["trace"] = trace
    result["events"] = runtime.records
    result["audit"] = runtime.audit
    return result
