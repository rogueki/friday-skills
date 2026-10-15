"""Deterministic, fail-closed checks for adapters that explicitly call this module."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Mapping
from urllib.parse import urlsplit


MODES = frozenset({"mock", "read_only", "live"})
RESULT_STATUSES = frozenset({"completed", "partial", "blocked", "failed", "waiting_approval"})
RISK_TIERS = {
    "observe": 0, "analyze": 0, "search": 0,
    "draft": 1, "local_reversible_write": 1,
    "send_message": 2, "calendar_write": 2, "contact_external": 2,
    "smart_home_write": 2, "delete_single": 2,
    "payment": 3, "purchase": 3, "booking": 3, "contract": 3,
    "tax_submit": 3, "credential_change": 3, "mass_action": 3,
    "security_critical_change": 3, "mass_delete": 3,
}
INTERNAL_SKILL_EVENT_TYPES = frozenset({
    "friday.skill.started", "friday.skill.progress", "friday.skill.waiting_approval",
    "friday.skill.completed", "friday.skill.failed",
})


class PolicyError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PolicyError(message)


def _utc(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise PolicyError("invalid ISO-8601 timestamp") from exc
    _require(parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed), "timestamp must be UTC")
    return parsed


def action_fingerprint(action: str, target: str, payload: Any) -> str:
    _require(bool(action and target), "action and target required")
    encoded = json.dumps({"action": action, "target": target, "payload": payload}, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


def risk_tier(action: str) -> int:
    return RISK_TIERS.get(action, 3)


def capability_available(capability: Mapping[str, Any], *, permission: str, mode: str, now: datetime | None = None) -> bool:
    if mode not in MODES or permission not in {"read", "write"}:
        return False
    if capability.get("mode") != mode or capability.get("status") != "healthy":
        return False
    public_weather = False
    if permission == "read" and mode in {"read_only", "live"} and capability.get("public_read") is True:
        source = capability.get("source")
        if isinstance(source, str):
            try:
                parsed = urlsplit(source)
                public_weather = (
                    capability.get("name") == "weather.read"
                    and capability.get("adapter_id") == "geosphere-weather"
                    and parsed.scheme == "https"
                    and parsed.hostname == "dataset.api.hub.geosphere.at"
                    and parsed.port is None
                    and parsed.path == "/v1/timeseries/forecast/nwp-v2-1h-1km"
                    and parsed.username is None and parsed.password is None
                )
            except ValueError:
                return False
    if not (capability.get("authenticated") is True or public_weather) or capability.get("rate_limited") is not False:
        return False
    if permission not in capability.get("permissions", []):
        return False
    if permission == "write" and mode != "live":
        return False
    if permission == "read" and mode == "mock" and capability.get("synthetic") is not True:
        return False
    try:
        checked = _utc(capability["checked_at"])
    except (KeyError, PolicyError):
        return False
    current = now or datetime.now(timezone.utc)
    return 0 <= (current - checked).total_seconds() <= 300


def authorize_action(action: str, target: str, payload: Any, *, mode: str, capability: Mapping[str, Any], approval: Mapping[str, Any] | None = None, idempotency_key: str | None = None, now: datetime | None = None) -> int:
    tier = risk_tier(action)
    local = action in {"draft", "local_reversible_write"}
    permission = "read" if tier == 0 or local else "write"
    _require(capability_available(capability, permission=permission, mode=mode, now=now), "capability unavailable for mode or permission")
    if local:
        _require(bool(capability.get("authorized_workspace")), "authorized workspace required")
        if mode == "mock" and action == "local_reversible_write":
            raise PolicyError("mock mode cannot write real workspace files")
    if tier >= 2:
        _require(bool(idempotency_key), "idempotency key required")
        _require(approval is not None, "approval required")
        _require(approval.get("status") == "approved", "approval not approved")
        _require(approval.get("fingerprint") == action_fingerprint(action, target, payload), "approval bound to different action")
        approved_tier = approval.get("tier")
        _require(approval.get("target") == target and type(approved_tier) is int and approved_tier >= tier, "approval target or tier mismatch")
        current = now or datetime.now(timezone.utc)
        _require(isinstance(approval.get("expires_at"), str), "approval expiry missing")
        _require(_utc(approval["expires_at"]) > current, "approval expired")
        if tier == 3:
            _require(approval.get("hard_approval") is True and approval.get("second_factor_verified") is True, "hard approval and second factor required")
    return tier


def validate_result(result: Mapping[str, Any]) -> None:
    _require(result.get("status") in RESULT_STATUSES, "invalid result status")
    _require(isinstance(result.get("skill"), str) and result["skill"].startswith("friday-"), "invalid skill")
    _require(result.get("mode") in MODES, "invalid mode")
    _require(isinstance(result.get("summary"), str) and bool(result["summary"].strip()), "summary required")
    for key in ("artifacts", "actions_taken", "actions_proposed", "approvals_required", "warnings", "errors", "sources", "verification"):
        _require(isinstance(result.get(key), list), f"{key} must be a list")
    if result["status"] == "completed":
        _require(bool(result["verification"]), "completed requires verification")
        _require(not result["approvals_required"] and not result["errors"], "completed cannot have pending approval or errors")
    if result["status"] == "waiting_approval":
        _require(bool(result["approvals_required"]), "waiting_approval requires approval request")
    if result["status"] == "completed" and result["skill"] == "friday-web-research":
        _require(bool(result["sources"]), "completed web research requires sources")
        for source in result["sources"]:
            _require(isinstance(source, Mapping) and isinstance(source.get("url"), str) and source["url"].startswith(("http://", "https://")), "source URL required")
            _utc(source.get("retrieved_at"))
    if result["mode"] != "live":
        _require(not any(isinstance(a, Mapping) and a.get("external_write") for a in result["actions_taken"]), "non-live result claims external write")


def validate_event(event: Mapping[str, Any]) -> None:
    """Validate a local lifecycle record; this is not a rogue-friday AsyncAPI event."""
    _require(event.get("type") in INTERNAL_SKILL_EVENT_TYPES, "invalid internal skill event type")
    _require(bool(event.get("event_id")) and isinstance(event.get("skill"), str) and event["skill"].startswith("friday-"), "event identity required")
    _require(event.get("mode") in MODES, "invalid event mode")
    _require(isinstance(event.get("progress"), (int, float)) and not isinstance(event.get("progress"), bool) and 0 <= event["progress"] <= 1, "progress must be 0..1")
    _utc(event.get("timestamp"))
    if event["type"] == "friday.skill.completed":
        _require(event.get("status") == "completed" and event["progress"] == 1, "completed event inconsistent")
