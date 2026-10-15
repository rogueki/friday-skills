"""Callable policy boundary for a future trusted adapter, not a Hermes hook registration."""

from __future__ import annotations

from typing import Any, Mapping

from shared.policy import PolicyError, authorize_action
from shared.runtime import untrusted_text


def inspect_untrusted(content: str) -> dict[str, str]:
    try:
        untrusted_text(content)
    except PolicyError as exc:
        return {"decision": "quarantine", "reason": str(exc)}
    return {"decision": "data_only", "reason": "source text carries no authority"}


def preflight_action(action: str, target: str, payload: Any, *, mode: str,
                     capability: Mapping[str, Any], approval: Mapping[str, Any] | None = None,
                     idempotency_key: str | None = None) -> dict[str, Any]:
    try:
        tier = authorize_action(action, target, payload, mode=mode, capability=capability,
                                approval=approval, idempotency_key=idempotency_key)
    except PolicyError as exc:
        return {"decision": "deny", "reason": str(exc), "executed": False}
    if mode == "live":
        return {"decision": "deny", "reason": "no verified live adapter installed", "executed": False}
    return {"decision": "allow_local", "risk_tier": tier, "executed": False}
