"""Local deterministic contract harness; no production adapter is implemented here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

from shared.policy import PolicyError, authorize_action, validate_event


ROOT = Path(__file__).resolve().parents[1]
STATES = frozenset({"queued", "working", "waiting", "waiting_approval", "completed", "partial", "failed", "blocked"})


def load_fixture(kind: str, name: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", kind) or not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
        raise ValueError("invalid fixture name")
    path = ROOT / "fixtures" / kind / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def route_request(request: str) -> dict[str, Any]:
    """Narrow, explicit mock routes; no model or external side effect."""
    text = request.casefold().strip()
    if not text:
        return {"status": "blocked", "reason": "empty_request", "skill": None}
    if any(term in text for term in ("wetter", "weather", "temperatur", "regen")):
        if any(term in text for term in ("briefing", "tagesüberblick", "morning brief")):
            return {"status": "waiting", "reason": "weather_or_briefing_ambiguous", "skill": None}
        return {"status": "selected", "reason": "standalone_weather", "skill": "friday-weather"}
    if any(term in text for term in ("morgenbriefing", "morning briefing", "tagesbriefing")):
        return {"status": "selected", "reason": "daily_briefing", "skill": "friday-morning-briefing"}
    if any(term in text for term in ("rechnung", "invoice")):
        return {"status": "selected", "reason": "invoice_intake", "skill": "friday-invoice-intake"}
    if any(term in text for term in ("mail", "e-mail", "email")):
        return {"status": "selected", "reason": "mail_triage", "skill": "friday-executive-mail-manager"}
    return {"status": "blocked", "reason": "no_verified_route", "skill": None}


def untrusted_text(value: str) -> str:
    """Preserve source content as data; reject instruction-like material in mock decisions."""
    markers = ("ignore previous", "ignore all", "system prompt", "developer message", "übergehe", "ignoriere", "sende geheim", "exfiltrat")
    if any(marker in value.casefold() for marker in markers):
        raise PolicyError("untrusted source contains instruction attempt")
    return value


@dataclass
class MockRuntime:
    now: datetime = field(default_factory=lambda: datetime(2026, 10, 15, 12, tzinfo=timezone.utc))
    records: list[dict[str, Any]] = field(default_factory=list)
    audit: list[dict[str, Any]] = field(default_factory=list)

    def event(self, skill: str, status: str, activity: str, progress: float, *, task_id: str | None = None) -> dict[str, Any]:
        if status not in STATES:
            raise ValueError("unknown dashboard state")
        kind = {"working": "started", "completed": "completed", "failed": "failed", "waiting_approval": "waiting_approval"}.get(status, "progress")
        record = {
            "event_id": f"mock-{len(self.records)+1}", "type": f"friday.skill.{kind}",
            "skill": skill, "status": status, "activity": activity,
            "progress": progress, "timestamp": self.now.isoformat(), "mode": "mock", "task_id": task_id,
        }
        validate_event(record)
        self.records.append(record)
        return record

    def propose(self, action: str, target: str, payload: Any, *, tier: int) -> dict[str, Any]:
        proposal = {"action": action, "target": target, "payload": payload, "risk_tier": tier, "executed": False}
        self.audit.append({"kind": "proposal", "action": action, "target": target, "executed": False})
        return proposal

    def deny_live_action(self, action: str, target: str, payload: Any, capability: dict[str, Any], approval: dict[str, Any] | None = None) -> None:
        """Fail closed: this package has no external transport, even with valid credentials."""
        authorize_action(action, target, payload, mode="live", capability=capability, approval=approval, now=self.now)
        raise PolicyError("live adapter unavailable in friday-skills")


def dashboard_mapping(record: dict[str, Any]) -> dict[str, Any]:
    """Return an intended parent contract operation, never publish it."""
    validate_event(record)
    status = record["status"]
    if status not in STATES:
        raise PolicyError("unsupported dashboard state")
    return {
        "publishable": False,
        "parent_contract": "jarvis.task.*" if record.get("task_id") else "jarvis.activity.appended",
        "task_id": record.get("task_id"),
        "status": status,
        "activity": record["activity"],
        "requires_verified_adapter": True,
    }
