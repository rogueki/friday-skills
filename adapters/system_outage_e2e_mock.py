"""E2E10: deterministic synthetic outage and recovery evidence, without service I/O."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any

from shared.policy import capability_available
from shared.runtime import MockRuntime, dashboard_mapping, load_fixture


SOURCE = "synthetic:fixtures/system/recovery_timelines.json"
VARIANTS = frozenset({
    "default", "offline", "recovered", "stale_health", "flapping", "no_post_check",
    "missing_adapter", "malformed_initial", "unknown_status", "stale_recovery",
    "unordered_recovery", "wrong_source", "wrong_adapter",
})


def _fresh_probe(probe: Any, runtime: MockRuntime, previous: datetime) -> datetime | None:
    if not isinstance(probe, dict) or probe.get("source") != SOURCE or probe.get("adapter_id") != "synthetic-mail":
        return None
    observed = probe.get("observed_at")
    if not isinstance(observed, str):
        return None
    try:
        instant = datetime.fromisoformat(observed.replace("Z", "+00:00"))
    except ValueError:
        return None
    if instant.tzinfo is None or instant.utcoffset().total_seconds() != 0 or instant <= previous:
        return None
    capability = probe.get("capability")
    if not isinstance(capability, dict) or capability.get("adapter_id") != "synthetic-mail":
        return None
    if capability.get("checked_at") != observed or capability.get("name") != "mail.read":
        return None
    if not capability_available(capability, permission="read", mode="mock", now=runtime.now):
        return None
    return instant


def run_system_outage_mock(runtime: MockRuntime, result: dict[str, Any], trace: list[str], *, variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"unknown system_outage variant: {variant}")

    fixture_name = "adapters" if variant == "default" else "offline"
    initial = load_fixture("system", fixture_name)
    mail = initial.get("mail")
    if variant == "missing_adapter":
        mail = None
    elif variant == "malformed_initial":
        mail = "unparseable"
    elif variant == "unknown_status" and isinstance(mail, dict):
        mail = {**mail, "status": "unknown"}
    elif variant == "stale_health" and isinstance(mail, dict):
        mail = {**mail, "status": "healthy", "authenticated": True, "checked_at": "2026-10-15T11:40:00Z"}

    available = isinstance(mail, dict) and capability_available(mail, permission="read", mode="mock", now=runtime.now)
    if available:
        raise ValueError("outage fixture unexpectedly permits the blocked mail operation")

    event = runtime.event("friday-capability-and-health-check", "blocked", "Synthetic mail read capability unavailable", 0)
    trace.extend(["adapter_offline" if isinstance(mail, dict) and mail.get("status") == "offline"
                  else "adapter_unavailable", "capability_degraded", "mail_skill_blocked",
                  "dashboard_warning_local"])
    result.update(
        status="blocked", degraded_capability="mail", capability_available=False,
        initial_health={"source": f"synthetic:fixtures/system/{fixture_name}.json",
                        "status": mail.get("status", "unknown") if isinstance(mail, dict) else "unknown",
                        "checked_at": mail.get("checked_at") if isinstance(mail, dict) else None},
        blocked_skill="friday-executive-mail-manager", blocked_action="mail.read",
        blocked_action_executed=False, requires_fresh_request=True,
        dashboard_mapping=dashboard_mapping(event),
        recovery_plan={
            "mode": "mock", "kind": "non_executable_plan", "target": "synthetic-mail",
            "steps": ["inspect_trusted_health", "verify_readiness_twice", "request_mail_task_again"],
            "service_action_taken": False,
        },
        recovery_status="not_verified",
    )

    timelines = load_fixture("system", "recovery_timelines")
    probes = deepcopy(timelines.get("recovered", [])) if variant in {
        "recovered", "flapping", "no_post_check", "stale_recovery",
        "unordered_recovery", "wrong_source", "wrong_adapter",
    } else []
    if variant == "flapping":
        probes[1]["capability"]["status"] = "offline"
    elif variant == "no_post_check":
        probes.pop()
    elif variant == "stale_recovery":
        probes[0]["observed_at"] = "2026-10-15T11:40:00Z"
        probes[0]["capability"]["checked_at"] = "2026-10-15T11:40:00Z"
    elif variant == "unordered_recovery":
        probes.reverse()
    elif variant == "wrong_source":
        probes[0]["source"] = "untrusted"
    elif variant == "wrong_adapter":
        probes[0]["adapter_id"] = "other-service"
    baseline = datetime.fromisoformat("2026-10-15T11:58:00+00:00")
    accepted: list[str] = []
    for probe in probes:
        instant = _fresh_probe(probe, runtime, baseline)
        if instant is None:
            accepted.clear()
            result["recovery_reason"] = "invalid_or_unhealthy_post_check"
            break
        baseline = instant
        accepted.append(instant.isoformat())
    result["readiness_probes_verified"] = accepted
    if len(accepted) == 2 and len(probes) == 2:
        result.update(status="partial", recovery_status="mock_verified", recovery_reason="two_fresh_ordered_readiness_probes")
        trace.append("synthetic_recovery_readiness_verified")
        runtime.event("friday-service-recovery", "completed", "Synthetic readiness verified; no service action or mail retry", 1)
    else:
        result.setdefault("recovery_reason", "insufficient_post_checks")
        trace.append("recovery_not_verified")
