"""Opt-in Hermes tools backed solely by the F.R.I.D.A.Y. mock runtime."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any


FIXTURES = frozenset({
    ("weather", "current"), ("travel", "cases"), ("tax", "cases"),
    ("system", "adapters"), ("presentations", "brief"), ("media", "cases"),
    ("mail", "messages"), ("loxone", "status"), ("invoices", "cases"),
    ("calendar", "events"),
})


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "parameters": {
            "type": "object", "properties": properties, "required": required,
            "additionalProperties": False,
        },
    }


SCHEMAS = {
    "friday_policy_preflight": _schema(
        "friday_policy_preflight",
        "Evaluate a proposed F.R.I.D.A.Y. action against local mock policy. Returns a decision only; never executes the action.",
        {"action": {"type": "string"}, "target": {"type": "string"},
         "payload": {"description": "JSON-compatible proposed payload"},
         "mode": {"type": "string", "enum": ["mock", "read_only", "live"]}},
        ["action", "target", "payload"],
    ),
    "friday_fixture_read": _schema(
        "friday_fixture_read",
        "Read one allowlisted synthetic F.R.I.D.A.Y. fixture from the local skill package.",
        {"kind": {"type": "string"}, "name": {"type": "string"}},
        ["kind", "name"],
    ),
    "friday_mock_propose": _schema(
        "friday_mock_propose",
        "Record an action proposal in memory. It cannot execute, send, publish, or write the action.",
        {"action": {"type": "string"}, "target": {"type": "string"},
         "payload": {"description": "JSON-compatible proposal payload"}},
        ["action", "target", "payload"],
    ),
    "friday_activity_record": _schema(
        "friday_activity_record",
        "Create a local, nonpublishable F.R.I.D.A.Y. lifecycle record in memory.",
        {"skill": {"type": "string"},
         "status": {"type": "string", "enum": ["queued", "working", "waiting", "waiting_approval", "completed", "partial", "failed", "blocked"]},
         "message": {"type": "string"}, "progress": {"type": "number", "minimum": 0, "maximum": 1},
         "task_id": {"type": "string"}},
        ["skill", "status", "message", "progress"],
    ),
}


def _response(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _package_root() -> Path:
    configured = os.environ.get("FRIDAY_SKILLS_ROOT")
    if not configured:
        raise RuntimeError("FRIDAY_SKILLS_ROOT must point to the friday-skills repository")
    root = Path(configured).resolve(strict=True)
    if not (root / "shared" / "policy.py").is_file() or not (root / "fixtures").is_dir():
        raise RuntimeError("FRIDAY_SKILLS_ROOT lacks shared policy or synthetic fixtures")
    return root


def register(ctx) -> None:
    """Register mock-only handlers; the caller must opt in to this plugin."""
    root = _package_root()
    # PYTHONPATH is set by the operator before Hermes starts. Do not mutate sys.path.
    from shared.hooks import preflight_action
    from shared.policy import risk_tier
    from shared.runtime import MockRuntime, dashboard_mapping, load_fixture

    shared_file = Path(__import__("shared").__file__).resolve()
    if root not in shared_file.parents:
        raise RuntimeError("shared package was imported from outside FRIDAY_SKILLS_ROOT")

    runtime = MockRuntime(now=datetime.now(timezone.utc))

    def policy_preflight(params: dict, **_kwargs) -> str:
        action, target = params.get("action"), params.get("target")
        mode = params.get("mode", "mock")
        if mode != "mock":
            return _response({"decision": "deny", "reason": "this plugin accepts mock mode only", "executed": False})
        if not isinstance(action, str) or not action.strip() or not isinstance(target, str) or not target.strip():
            return _response({"decision": "deny", "reason": "action and target required", "executed": False})
        capability = {
            "mode": "mock", "status": "healthy", "authenticated": True,
            "rate_limited": False, "permissions": ["read"], "synthetic": True,
            "authorized_workspace": True, "checked_at": datetime.now(timezone.utc).isoformat(),
        }
        decision = preflight_action(action, target, params.get("payload"), mode="mock", capability=capability)
        decision["mode"] = "mock"
        decision["publishable"] = False
        return _response(decision)

    def fixture_read(params: dict, **_kwargs) -> str:
        key = (params.get("kind"), params.get("name"))
        if not all(isinstance(part, str) for part in key) or key not in FIXTURES:
            return _response({"error": "fixture not allowlisted", "synthetic": True, "external_effect": False})
        try:
            data = load_fixture(*key)
        except (OSError, ValueError) as exc:
            return _response({"error": str(exc), "synthetic": True, "external_effect": False})
        return _response({"fixture": {"kind": key[0], "name": key[1]}, "data": data,
                          "synthetic": True, "external_effect": False})

    def mock_propose(params: dict, **_kwargs) -> str:
        action, target = params.get("action"), params.get("target")
        if not isinstance(action, str) or not action.strip() or not isinstance(target, str) or not target.strip():
            return _response({"error": "action and target required", "executed": False})
        proposal = runtime.propose(action, target, params.get("payload"), tier=risk_tier(action))
        return _response({"proposal": proposal, "requires_approval": proposal["risk_tier"] >= 2,
                          "mode": "mock", "publishable": False})

    def activity_record(params: dict, **_kwargs) -> str:
        skill, status = params.get("skill"), params.get("status")
        message, progress = params.get("message"), params.get("progress")
        if not isinstance(message, str) or not message.strip():
            return _response({"error": "message required", "delivered": False})
        try:
            runtime.now = datetime.now(timezone.utc)
            record = runtime.event(skill, status, message, progress, task_id=params.get("task_id"))
            mapping = dashboard_mapping(record)
        except (TypeError, ValueError) as exc:
            return _response({"error": str(exc), "delivered": False})
        return _response({"local_record": record, "intended_mapping": mapping, "delivered": False})

    for name, handler in (
        ("friday_policy_preflight", policy_preflight),
        ("friday_fixture_read", fixture_read),
        ("friday_mock_propose", mock_propose),
        ("friday_activity_record", activity_record),
    ):
        ctx.register_tool(name=name, toolset="friday_local", schema=SCHEMAS[name], handler=handler)
