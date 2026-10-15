"""Generate operational JSON-compatible YAML from registry/skills.json."""

from __future__ import annotations

from pathlib import Path
import json
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
CAPABILITIES = {
    "mail.read": ("gmx", "read_only"), "mail.send": ("gmx", "approval_required"),
    "calendar.read": ("caldav", "read_only"), "calendar.write": ("caldav", "approval_required"),
    "contacts.read": ("carddav", "read_only"), "payment.prepare": ("finance", "draft_only"),
    "payment.execute": ("banking", "hard_approval"), "loxone.read": ("loxone", "read_only"),
    "loxone.write": ("loxone", "approval_required"), "weather.read": ("weather", "read_only"),
    "dashboard.write": ("control_api", "approval_required"), "office.render": ("windows_worker", "draft_only"),
    "voice.speak": ("local_voice", "draft_only"),
}
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
                              "capabilities": {name: {"adapter": adapter, "mode": mode,
                                                       "live_available": False, "mock_available": True}
                                               for name, (adapter, mode) in CAPABILITIES.items()}},
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
