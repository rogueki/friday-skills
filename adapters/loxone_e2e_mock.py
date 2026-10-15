"""E2E8: synthetic status, gated light proposal, and isolated in-memory readback."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta
from typing import Any

from adapters.loxone_status import LoxoneStatusError, read_status
from shared.policy import action_fingerprint, capability_available, risk_tier
from shared.runtime import MockRuntime, dashboard_mapping, load_fixture


SOURCE = "synthetic:fixtures/loxone/e2e_status.json"
CONTROL_ID = "ctrl-light-office"
CONTROLLER_ID = "synthetic-controller-1"
VARIANTS = frozenset({
    "default", "status_only", "mock_approved", "readback_failed", "readback_stale",
    "stale_status", "offline", "unknown_control", "unsafe_control", "missing_read_capability",
    "missing_write_capability", "denied_approval", "mismatched_approval", "expired_approval",
    "replayed_approval", "approval_bypass", "failed_write", "unknown_outcome",
})
SIMULATED_GRANT_VARIANTS = frozenset({
    "mock_approved", "readback_failed", "readback_stale", "denied_approval",
    "mismatched_approval", "expired_approval", "replayed_approval", "approval_bypass",
    "failed_write", "unknown_outcome",
})


class LoxoneMockError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _capability(now: datetime, *, name: str, healthy: bool = True) -> dict[str, Any]:
    return {"name": name, "mode": "mock", "status": "healthy" if healthy else "offline",
            "synthetic": True, "authenticated": True, "rate_limited": False,
            "permissions": ["read"] if name == "loxone.read" else ["write"],
            "checked_at": now.isoformat(), "controller_id": CONTROLLER_ID}


def _control(reading: dict[str, Any], control_id: str) -> dict[str, Any]:
    matches = [row for row in reading["controls"] if row["id"] == control_id]
    if len(matches) != 1:
        raise LoxoneMockError("unknown_control")
    return matches[0]


def _synthetic_write_capability(capability: dict[str, Any], now: datetime) -> bool:
    """Check mock eligibility without misrepresenting it as a live write capability."""
    try:
        checked = datetime.fromisoformat(capability["checked_at"])
    except (KeyError, TypeError, ValueError):
        return False
    return (capability.get("name") == "loxone.write" and capability.get("mode") == "mock"
            and capability.get("status") == "healthy" and capability.get("synthetic") is True
            and capability.get("authenticated") is True and capability.get("rate_limited") is False
            and capability.get("permissions") == ["write"]
            and capability.get("controller_id") == CONTROLLER_ID and checked.tzinfo is not None
            and timedelta(0) <= now - checked <= timedelta(minutes=5))


def _grant(proposal: dict[str, Any], now: datetime, variant: str) -> dict[str, Any]:
    digest = action_fingerprint(proposal["action"], proposal["target"], proposal["payload"])
    grant = {"kind": "simulated_test_grant_only", "status": "approved", "fingerprint": digest,
             "target": proposal["target"], "tier": 2, "controller_id": CONTROLLER_ID,
             "idempotency_key": proposal["idempotency_key"],
             "expires_at": (now + timedelta(minutes=5)).isoformat(), "used": False}
    if variant == "denied_approval":
        grant["status"] = "denied"
    elif variant == "mismatched_approval":
        grant["fingerprint"] = "0" * 64
    elif variant == "expired_approval":
        grant["expires_at"] = (now - timedelta(seconds=1)).isoformat()
    elif variant == "replayed_approval":
        grant["used"] = True
    elif variant == "approval_bypass":
        grant = {}
    return grant


def _consume_grant(grant: dict[str, Any], proposal: dict[str, Any], now: datetime) -> None:
    digest = action_fingerprint(proposal["action"], proposal["target"], proposal["payload"])
    if (grant.get("kind") != "simulated_test_grant_only" or grant.get("status") != "approved"
            or grant.get("fingerprint") != digest or grant.get("target") != proposal["target"]
            or grant.get("tier") != risk_tier("smart_home_write")
            or grant.get("controller_id") != CONTROLLER_ID
            or grant.get("idempotency_key") != proposal["idempotency_key"]):
        raise LoxoneMockError("mock_approval_mismatch")
    if grant.get("used") is not False:
        raise LoxoneMockError("mock_approval_replayed")
    try:
        expiry = datetime.fromisoformat(grant["expires_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise LoxoneMockError("mock_approval_mismatch") from exc
    if expiry.tzinfo is None or expiry <= now:
        raise LoxoneMockError("mock_approval_expired")
    grant["used"] = True


def _read(snapshot: dict[str, Any], runtime: MockRuntime) -> dict[str, Any]:
    reading = read_status([CONTROL_ID], mode="mock", now=runtime.now, mock_snapshot=snapshot)
    if reading["source"] != "synthetic:injected-mock-snapshot" or reading["synthetic"] is not True:
        raise LoxoneMockError("untrusted_read_source")
    return reading


def run_loxone_mock(runtime: MockRuntime, result: dict[str, Any], trace: list[str], *, variant: str) -> None:
    if variant not in VARIANTS:
        raise ValueError(f"unknown loxone variant: {variant}")
    snapshot = load_fixture("loxone", "e2e_status")
    requested_id = "ctrl-unknown" if variant == "unknown_control" else CONTROL_ID
    if variant == "unsafe_control":
        snapshot["controls"][0].update(kind="alarm", value=False, unit="boolean")
    if variant == "stale_status":
        old = (runtime.now - timedelta(minutes=6)).isoformat()
        snapshot["observed_at"] = old
        snapshot["controls"][0]["updated_at"] = old
    read_capability = _capability(runtime.now, name="loxone.read", healthy=variant != "missing_read_capability")
    write_capability = _capability(runtime.now, name="loxone.write", healthy=variant != "missing_write_capability")
    runtime.event("friday-loxone-status", "working", "Synthetic Loxone status read started", 0)
    try:
        if variant == "offline":
            raise LoxoneMockError("controller_offline")
        if not capability_available(read_capability, permission="read", mode="mock", now=runtime.now):
            raise LoxoneMockError("read_capability_unavailable")
        reading = _read(snapshot, runtime)
        control = _control(reading, requested_id)
        trace.append("read_status_mock")
        result["reading"] = {"controller_id": CONTROLLER_ID, "control": control,
                             "observed_at": reading["observed_at"], "source": SOURCE,
                             "synthetic": True, "live_state_verified": False}
        result["original_state"] = "off" if control["value"] == 0 else "on"
        result["answer"] = (f"Simulation ({SOURCE}): {control['id']} in {control['room_id']} "
                            f"meldet {control['value']} {control['unit']} "
                            f"(Stand {control['updated_at']}).")
        trace.append("source_bound_status_answer")
        if variant == "status_only":
            result.update(status="completed", verification={"scope": "synthetic_status_only",
                                                           "control_id": control["id"], "observed_at": reading["observed_at"]})
            return
        if control["id"] != CONTROL_ID or control["kind"] != "light" or control["unit"] != "%":
            raise LoxoneMockError("unsafe_control")
        if not (isinstance(control["value"], float) and control["value"] == 0.0):
            raise LoxoneMockError("unsafe_prestate")
        if not _synthetic_write_capability(write_capability, runtime.now):
            raise LoxoneMockError("write_capability_unavailable")
        payload = {"controller_id": CONTROLLER_ID, "control_id": CONTROL_ID,
                   "kind": "light", "before": 0.0, "desired": 100.0, "unit": "%",
                   "prestate_observed_at": reading["observed_at"]}
        proposal = runtime.propose("smart_home_write", CONTROL_ID, payload,
                                   tier=risk_tier("smart_home_write"))
        digest = action_fingerprint("smart_home_write", CONTROL_ID, payload)
        proposal["fingerprint"] = digest
        proposal["idempotency_key"] = f"synthetic-{digest[:16]}"
        result.update(status="waiting_approval", proposal=proposal, verification="not_executed",
                      approval={"status": "required", "tier": 2, "granted": False,
                                "trusted_host_approval": False, "bound_fingerprint": digest})
        trace.extend(["safe_single_light_policy", "tier_2_exact_approval_required"])
        if variant not in SIMULATED_GRANT_VARIANTS:
            return
        grant = _grant(proposal, runtime.now, variant)
        _consume_grant(grant, proposal, runtime.now)
        result["approval"] = {"status": "simulated_only", "tier": 2, "granted": True,
                              "trusted_host_approval": False, "bound_fingerprint": digest,
                              "consumed": grant["used"]}
        trace.append("one_shot_simulated_grant")
        if variant == "failed_write":
            raise LoxoneMockError("simulated_write_failed")
        after = deepcopy(snapshot)
        after["controls"][0]["value"] = 0 if variant == "readback_failed" else 100
        after["observed_at"] = (runtime.now - timedelta(seconds=1)).isoformat()
        after["controls"][0]["updated_at"] = after["observed_at"]
        result["simulation"] = {"in_memory_only": True, "external_write": False,
                                "control_id": CONTROL_ID, "idempotency_key": proposal["idempotency_key"]}
        trace.append("in_memory_mock_write")
        if variant == "unknown_outcome":
            result.update(status="partial", reason="unknown_simulated_outcome", verification="unconfirmed")
            return
        if variant == "readback_stale":
            old = (runtime.now - timedelta(minutes=6)).isoformat()
            after["observed_at"] = old
            after["controls"][0]["updated_at"] = old
        readback = _read(after, runtime)
        confirmed = _control(readback, CONTROL_ID)
        if (confirmed["kind"] != "light" or confirmed["unit"] != "%"
                or confirmed["value"] != payload["desired"]
                or datetime.fromisoformat(confirmed["updated_at"]) <= datetime.fromisoformat(control["updated_at"])):
            raise LoxoneMockError("readback_failed")
        result.update(status="completed", verification={"scope": "synthetic_in_memory_only",
                                                       "control_id": confirmed["id"], "value": confirmed["value"],
                                                       "unit": confirmed["unit"],
                                                       "observed_at": readback["observed_at"],
                                                       "source": readback["source"],
                                                       "live_device_verified": False})
        trace.append("read_status_mock_readback_verified")
    except (LoxoneStatusError, LoxoneMockError) as exc:
        code = exc.code
        result.update(status="blocked", reason=code)
        if "proposal" in result:
            result["verification"] = "unconfirmed" if "simulation" in result else "not_executed"
        if "reading" not in result:
            result.pop("answer", None)
    finally:
        status = result["status"]
        runtime.event("friday-loxone-control" if "proposal" in result else "friday-loxone-status",
                      status, f"Synthetic Loxone flow {status}",
                      1 if status == "completed" else 0.8 if status == "waiting_approval" else 0)
        result["dashboard_mapping"] = [dashboard_mapping(record) for record in runtime.records]
