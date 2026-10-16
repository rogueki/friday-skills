"""Generate operational JSON-compatible YAML from registry/skills.json."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry"

INTENTS = {
    "friday-weather": ["weather_current", "weather_today", "weather_tomorrow"],
    "friday-morning-briefing": ["morning_briefing"],
    "friday-executive-mail-manager": ["mail_triage"],
    "friday-mail-draft-writer": ["mail_reply_draft"],
    "friday-invoice-intake": ["invoice_extract"],
    "friday-payment-preparation": ["payment_prepare"],
}
INTENT_RISK = {
    "friday-weather": 0, "friday-morning-briefing": 0,
    "friday-executive-mail-manager": 0, "friday-mail-draft-writer": 1,
    "friday-invoice-intake": 1, "friday-payment-preparation": 1,
}
# Logical interface catalogue, not a report of installed or healthy adapters.
# The per-skill requirements live in registry/skill_capabilities.json.
CAPABILITIES = {
    "adapter.health.read": ("adapter_registry", "read_only"),
    "alert.read": ("alerts", "read_only"),
    "approval.read": ("approval_store", "read_only"),
    "approval.write": ("approval_store", "approval_required"),
    "audit.read": ("audit_store", "read_only"),
    "audit.write": ("audit_store", "approval_required"),
    "backup.read": ("backup", "read_only"),
    "backup.write": ("backup", "approval_required"),
    "calendar.read": ("caldav", "read_only"),
    "calendar.write": ("caldav", "approval_required"),
    "contact.read": ("carddav", "read_only"),
    "contacts.read": ("carddav", "read_only"),
    "dashboard.write": ("control_api", "approval_required"),
    "document.read": ("document_parser", "read_only"),
    "document.write": ("document_worker", "draft_only"),
    "energy.telemetry.read": ("energy_telemetry", "read_only"),
    "file.read": ("scoped_filesystem", "read_only"),
    "file.write": ("scoped_filesystem", "approval_required"),
    "finance.expense-ledger.read": ("finance", "read_only"),
    "finance.invoice-ledger.read": ("finance", "read_only"),
    "finance.receipt-index.read": ("finance", "read_only"),
    "finance.subscription-ledger.read": ("finance", "read_only"),
    "finanzonline.submit": ("finanzonline", "hard_approval"),
    "home.telemetry.read": ("home_telemetry", "read_only"),
    "loxone.read": ("loxone", "read_only"),
    "loxone.write": ("loxone", "approval_required"),
    "mail.read": ("imap_smtp_mail", "read_only"),
    "mail.send": ("imap_smtp_mail", "approval_required"),
    "media.read": ("media_worker", "read_only"),
    "media.render": ("media_worker", "draft_only"),
    "memory.read": ("memory_store", "read_only"),
    "memory.write": ("memory_store", "approval_required"),
    "messaging.read": ("messaging_gateway", "read_only"),
    "messaging.send": ("messaging_gateway", "approval_required"),
    "meter.read": ("meter", "read_only"),
    "model.inventory.read": ("model_registry", "read_only"),
    "notification.deliver": ("notification_gateway", "approval_required"),
    "notification.send": ("notification_gateway", "approval_required"),
    "office.render": ("windows_worker", "draft_only"),
    "official-web.read": ("official_web_fetch", "read_only"),
    "payment.execute": ("banking", "hard_approval"),
    "payment.prepare": ("finance", "draft_only"),
    "profile.read": ("profile_store", "read_only"),
    "profile.write": ("profile_store", "approval_required"),
    "reminder.write": ("reminder_store", "approval_required"),
    "scheduler.run": ("scheduler", "approval_required"),
    "service.health.read": ("service_probes", "read_only"),
    "service.restart": ("service_control", "hard_approval"),
    "storage.read": ("storage_probe", "read_only"),
    "tariff.read": ("tariff_source", "read_only"),
    "task.read": ("task_store", "read_only"),
    "task.write": ("task_store", "approval_required"),
    "telegram.receive": ("telegram_gateway", "read_only"),
    "telegram.send": ("telegram_gateway", "approval_required"),
    "telephony.call": ("telephony", "approval_required"),
    "voice.hear": ("local_voice", "read_only"),
    "voice.speak": ("local_voice", "draft_only"),
    "voice.verify-speaker": ("local_voice", "read_only"),
    "weather.read": ("weather", "read_only"),
    "weather.warning.read": ("official_weather", "read_only"),
    "web.read": ("web_fetch", "read_only"),
    "whatsapp.receive": ("whatsapp_gateway", "read_only"),
    "whatsapp.send": ("whatsapp_gateway", "approval_required"),
}

READ_MODES = {"read_only"}
WRITE_MODES = {"draft_only", "approval_required", "hard_approval"}
CAPABILITY_VERBS = {"read", "write", "send", "receive", "prepare", "execute",
                    "submit", "run", "call", "deliver", "render", "restart",
                    "speak", "hear"}


def load_skill_capabilities(names: set[str], entries: list[dict]) -> dict:
    if any(mode not in READ_MODES | WRITE_MODES for _, mode in CAPABILITIES.values()):
        raise ValueError("capability catalogue contains an unknown permission mode")
    manifest = json.loads((REGISTRY / "skill_capabilities.json").read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or set(manifest.get("skills", {})) != names:
        raise ValueError("skill capability manifest must cover exactly the registered skills")
    for skill, record in manifest["skills"].items():
        if set(record) != {"required", "conditional"}:
            raise ValueError(f"{skill}: expected required and conditional capability lists")
        seen = set()
        for field in ("required", "conditional"):
            if not isinstance(record[field], list):
                raise ValueError(f"{skill}: {field} must be a list")
            for capability_id in record[field]:
                if capability_id not in CAPABILITIES or capability_id in seen:
                    raise ValueError(f"{skill}: unknown or duplicate capability {capability_id}")
                seen.add(capability_id)
                if field == "required" and CAPABILITIES[capability_id][1] not in READ_MODES:
                    raise ValueError(f"{skill}: side-effect capability {capability_id} cannot be unconditional")
    for entry in entries:
        text = (ROOT / entry["path"]).read_text(encoding="utf-8")
        references = re.findall(r"(?<![\w/])(?:[a-z][a-z0-9-]*\.)+[a-z][a-z0-9-]*(?![\w/])", text)
        unknown = {item for item in references if item.rsplit(".", 1)[-1] in CAPABILITY_VERBS
                   and not item.startswith(("friday.", "jarvis.")) and item not in CAPABILITIES}
        if unknown:
            raise ValueError(f"{entry['name']}: unknown capability IDs in procedure: {sorted(unknown)}")
    return manifest["skills"]
AUTOMATIONS = {
    "morning_briefing": "friday-morning-briefing", "evening_briefing": "friday-evening-briefing",
    "mail_priority_watch": "friday-executive-mail-manager", "calendar_meeting_prep": "friday-meeting-briefing",
    "follow_up_watch": "friday-follow-up-manager", "invoice_due_watch": "friday-skonto-and-due-date-monitor",
    "skonto_watch": "friday-skonto-and-due-date-monitor", "tax_deadline_watch": "friday-tax-deadline-monitor-at",
    "funding_scan": "friday-austria-funding-scout", "tariff_review": "friday-energy-tariff-scout",
    "weather_warning_watch": "friday-weather-alerts", "loxone_anomaly_watch": "friday-home-anomaly-monitor",
    "storage_watch": "friday-storage-monitor", "backup_check": "friday-backup-manager",
    "skill_health_review": "friday-capability-and-health-check",
}


def build() -> dict[str, dict]:
    entries = json.loads((REGISTRY / "skills.json").read_text(encoding="utf-8"))["skills"]
    names = {entry["name"] for entry in entries}
    skill_capabilities = load_skill_capabilities(names, entries)
    roadmap = json.loads((REGISTRY / "roadmap.json").read_text(encoding="utf-8"))["skills"]
    known = {item["plan_name"].replace("jarvis-", "friday-", 1) for item in roadmap}
    missing = set(AUTOMATIONS.values()) - known
    if missing:
        raise ValueError(f"automations reference unknown skills: {sorted(missing)}")
    routes = []
    dashboards = {}
    for entry in sorted(entries, key=lambda x: x["name"]):
        name = entry["name"]
        category = entry["category"]
        route_id = name.removeprefix("friday-")
        routes.append({"id": route_id, "intents": INTENTS.get(name, [route_id.replace("-", "_")]),
                       "skills": [name], "preferred_model": "local" if category in {"weather", "core"} else "configured",
                       "risk_tier": INTENT_RISK.get(name, entry["max_risk_tier"]), "status": entry["status"],
                       "trigger": entry.get("trigger", "")})
        dashboards[name] = {"category": category, "icon": category, "default_orb_mode": "working",
                            "progress_strategy": "indeterminate", "detail_route": "/tasks/{task_id}"}
    all_intents = [intent for route in routes for intent in route["intents"]]
    if not all(route["intents"] for route in routes) or len(all_intents) != len(set(all_intents)):
        raise ValueError("routing intents must be nonempty and globally unique")
    automation_records = []
    for automation_id, skill in AUTOMATIONS.items():
        automation_records.append({"id": automation_id, "enabled": False, "schedule": None,
                                   "timezone": "Europe/Vienna", "skill": skill, "skill_installed": skill in names,
                                   "profile": "mock", "input": {}, "deliver": "local_preview",
                                   "quiet_hours": ["22:00", "07:00"], "risk_tier": 0,
                                   "failure_policy": "record_and_stop", "deduplication_window": "24h"})
    return {
        "routing.yaml": {"version": 1, "product": "F.R.I.D.A.Y.", "routes": routes},
        "capabilities.yaml": {"version": 1, "product": "F.R.I.D.A.Y.",
                              "status": "logical_contract_only",
                              "requirement_semantics": {
                                  "required": "Read interface for the primary adapter-backed path; a skill may explicitly accept supplied verified evidence instead.",
                                  "conditional": "Check separately before optional retrieval, persistence, delivery, or other live action; absence blocks that branch.",
                              },
                              "capabilities": {name: {"adapter": adapter, "mode": mode,
                                                       "permission": "read" if mode in READ_MODES else "write",
                                                       "live_available": False, "mock_available": False}
                                               for name, (adapter, mode) in sorted(CAPABILITIES.items())},
                              "skill_requirements": skill_capabilities},
        "approval-tiers.yaml": {"version": 1, "tiers": {
            "0": {"scope": "observe/search/analyze", "approval": "none"},
            "1": {"scope": "draft/local reversible", "approval": "workspace_bound"},
            "2": {"scope": "external communication/calendar/home write", "approval": "bound_expiring"},
            "3": {"scope": "payment/purchase/booking/tax/critical", "approval": "bound_expiring_hard_second_factor"}}},
        "automations.yaml": {"version": 1, "automations": automation_records},
        "dashboard.yaml": {"version": 1, "delivery": "local_only", "states": ["queued", "working", "waiting", "waiting_approval", "completed", "partial", "failed", "blocked"],
                           "skills": dashboards},
    }


def main() -> int:
    artifacts = build()
    changed = []
    for filename, value in artifacts.items():
        path = REGISTRY / filename
        expected = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if path.exists() and path.read_text(encoding="utf-8") == expected:
            continue
        changed.append(filename)
        if "--apply" in sys.argv:
            path.write_text(expected, encoding="utf-8")
    if changed:
        print(("updated: " if "--apply" in sys.argv else "outdated: ") + ", ".join(changed))
        return 0 if "--apply" in sys.argv else 1
    print("registry current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
