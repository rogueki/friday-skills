"""Run offline skill-contract checks and report runtime coverage honestly.

The shared checks validate policy and result contracts. They do not execute a
Hermes model, provider adapter, Dashboard publisher, or individual SKILL.md.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.policy import (PolicyError, action_fingerprint, authorize_action,  # noqa: E402
                           capability_available, risk_tier, validate_result)


NOW = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)

# Section 30 of the implementation plan. PASS means a shared contract was
# exercised. DECLARED means a human-readable routing expectation exists.
# NOT_RUN requires an actual skill runtime/adapter or an independent oracle.
MATRIX = {
    "trigger": {
        "clear": "DECLARED", "other_skill": "DECLARED",
        "ambiguity": "DECLARED", "collision": "DECLARED",
    },
    "functional": {
        "happy_path": "NOT_RUN", "empty_input": "NOT_RUN",
        "missing_capability": "PASS", "adapter_offline": "PASS",
        "partial_data": "NOT_RUN", "invalid_data": "NOT_RUN",
        "timeout": "NOT_RUN", "rate_limit": "PASS",
    },
    "security": {
        "prompt_injection": "NOT_RUN", "secret_extraction": "NOT_RUN",
        "path_traversal": "NOT_RUN", "dangerous_attachment": "NOT_RUN",
        "unauthorized_write": "PASS", "approval_bypass": "PASS",
        "replay_duplicate": "NOT_RUN",
    },
    "policy": {
        "tier": "PASS", "read_only_no_side_effect": "PASS",
        "approval": "PASS", "audit_event": "NOT_RUN",
        "dashboard_event": "NOT_RUN",
    },
    "output": {
        "schema": "PASS", "sources": "NOT_RUN",
        "uncertainty": "NOT_RUN", "no_hallucination": "NOT_RUN",
        "no_unauthorized_data": "NOT_RUN",
    },
}


def _capability(*, mode: str = "mock", status: str = "healthy", synthetic: bool = True,
                rate_limited: bool = False, permissions: list[str] | None = None) -> dict:
    return {
        "mode": mode, "status": status, "authenticated": True,
        "rate_limited": rate_limited, "permissions": permissions or ["read"],
        "checked_at": NOW.isoformat(), "synthetic": synthetic,
        "authorized_workspace": True,
    }


def _result(skill: str, *, status: str = "completed", mode: str = "mock") -> dict:
    result = {
        "status": status, "skill": skill, "mode": mode,
        "summary": "Synthetic contract result; no skill or provider executed.",
        "artifacts": [], "actions_taken": [], "actions_proposed": [],
        "approvals_required": [], "warnings": [], "errors": [],
        "sources": [], "verification": ["Shared result contract checked"],
    }
    if skill == "friday-web-research" and status == "completed":
        result["sources"] = [{"url": "https://example.test/synthetic-source",
                              "retrieved_at": NOW.isoformat()}]
    return result


def check_skill(path: Path) -> list[str]:
    """Return failures for one skill's declared cases and shared contracts."""
    failures: list[str] = []
    data = json.loads(path.read_text(encoding="utf-8"))
    skill = path.parents[1].name
    if data.get("skill") != skill:
        return ["skill/path mismatch"]
    routes = {item.get("id"): item for item in data.get("cases", [])}
    if set(routes) != {"positive", "negative", "collision", "ambiguity"}:
        failures.append("four manual routing expectations required")
    for name, expectation in (("positive", "select"), ("negative", "reject"),
                              ("collision", None), ("ambiguity", "defer")):
        case = routes.get(name, {})
        if not case.get("request") or not case.get("reason"):
            failures.append(f"{name}: request and reason required")
        if expectation and case.get("expected") != expectation:
            failures.append(f"{name}: expected {expectation}")
        if name == "collision" and case.get("expected") not in {"reject", "defer"}:
            failures.append("collision: expected reject or defer")

    contracts = data.get("contract_cases", [])
    if {case.get("id") for case in contracts} != {"mock-result", "missing-capability", "external-write-denied"}:
        failures.append("three executable shared contract cases required")
        return failures
    manifest = json.loads((ROOT / "registry/skill_capabilities.json").read_text(encoding="utf-8"))["skills"].get(skill)
    for case in contracts:
        for key in ("id", "skill", "mode", "input", "capabilities", "expected", "forbidden"):
            if key not in case:
                failures.append(f"{case.get('id')}: missing {key}")
        if case.get("skill") != skill or case.get("mode") != "mock":
            failures.append(f"{case.get('id')}: skill or mode mismatch")
        if not isinstance(case.get("input"), dict) or not isinstance(case.get("capabilities"), dict):
            failures.append(f"{case.get('id')}: input/capabilities must be objects")
        if not isinstance(case.get("forbidden"), list) or not case.get("forbidden"):
            failures.append(f"{case.get('id')}: forbidden actions required")
        declared = case.get("capabilities", {})
        if manifest is None or declared.get("required") != manifest["required"] or declared.get("conditional") != manifest["conditional"]:
            failures.append(f"{case.get('id')}: logical capabilities differ from registry")
        if declared.get("live_available") is not False or declared.get("mock_adapter_available") is not False:
            failures.append(f"{case.get('id')}: test must not claim an available adapter")
    if failures:
        return failures

    cases = {case["id"]: case for case in contracts}
    result_case = cases["mock-result"]
    if result_case["expected"].get("status") != "completed" or result_case["expected"].get("scope") != "result_schema_only":
        failures.append("mock-result: expected completed schema sample only")
    else:
        try:
            validate_result(_result(skill))
        except PolicyError as exc:
            failures.append(f"mock-result: {exc}")
    if "external_write" not in result_case["forbidden"]:
        failures.append("mock-result: external_write must be forbidden")
    modified = _result(skill)
    modified["actions_taken"] = [{"external_write": True}]
    try:
        validate_result(modified)
        failures.append("mock-result: non-live external write was accepted")
    except PolicyError:
        pass

    missing = cases["missing-capability"]
    if missing["expected"].get("status") != "blocked":
        failures.append("missing-capability: expected blocked")
    if capability_available(_capability(synthetic=False), permission="read", mode="mock", now=NOW):
        failures.append("missing-capability: non-synthetic mock capability accepted")
    if capability_available(_capability(status="offline"), permission="read", mode="mock", now=NOW):
        failures.append("missing-capability: offline capability accepted")
    if capability_available(_capability(rate_limited=True), permission="read", mode="mock", now=NOW):
        failures.append("missing-capability: rate-limited capability accepted")
    validate_result(_result(skill, status="blocked"))
    validate_result(_result(skill, status="partial"))
    invalid = _result(skill)
    invalid["verification"] = []
    try:
        validate_result(invalid)
        failures.append("invalid-data: unverified completion accepted")
    except PolicyError:
        pass

    denied = cases["external-write-denied"]
    if denied["expected"].get("status") != "blocked":
        failures.append("external-write-denied: expected blocked")
    action = denied["input"].get("action")
    if action not in {"send_message", "calendar_write", "smart_home_write", "payment", "booking", "tax_submit", "credential_change", "mass_delete"}:
        failures.append("external-write-denied: action must be a known external mutation")
    else:
        tier = risk_tier(action)
        if tier < 2 or denied["expected"].get("risk_tier") != tier:
            failures.append("external-write-denied: risk tier mismatch")
        try:
            authorize_action(action, f"{skill}:synthetic-target", {"synthetic": True},
                             mode="mock", capability=_capability(), now=NOW)
            failures.append("external-write-denied: action authorized in mock mode")
        except PolicyError:
            pass
        # This invokes only the pure policy function; no external write happens.
        target, payload = f"{skill}:synthetic-target", {"synthetic": True}
        live_cap = _capability(mode="live", permissions=["read", "write"])
        approval = {
            "status": "approved", "fingerprint": action_fingerprint(action, target, payload),
            "target": target, "tier": tier,
            "expires_at": (NOW + timedelta(minutes=5)).isoformat(),
            "hard_approval": tier == 3, "second_factor_verified": tier == 3,
        }
        for name, candidate, key in (
            ("missing-approval", None, "unique-key"),
            ("missing-idempotency", approval, None),
            ("changed-payload", {**approval, "fingerprint": action_fingerprint(action, target, {"changed": True})}, "unique-key"),
            ("expired-approval", {**approval, "expires_at": (NOW - timedelta(seconds=1)).isoformat()}, "unique-key"),
            ("missing-second-factor", {**approval, "second_factor_verified": False}, "unique-key") if tier == 3 else ("wrong-target", {**approval, "target": "another-target"}, "unique-key"),
        ):
            try:
                authorize_action(action, target, payload, mode="live", capability=live_cap,
                                 approval=candidate, idempotency_key=key, now=NOW)
                failures.append(f"{name}: policy accepted invalid authorization")
            except PolicyError:
                pass
        try:
            accepted_tier = authorize_action(action, target, payload, mode="live",
                                             capability=live_cap, approval=approval,
                                             idempotency_key="unique-key", now=NOW)
            if accepted_tier != tier:
                failures.append("valid approval: wrong risk tier")
        except PolicyError as exc:
            failures.append(f"valid approval: {exc}")
        try:
            authorize_action(action, f"{skill}:synthetic-target", {"synthetic": True},
                             mode="read_only", capability=_capability(mode="read_only"), now=NOW)
            failures.append("read-only external write authorized")
        except PolicyError:
            pass
    if "external_write" not in denied["forbidden"]:
        failures.append("external-write-denied: external_write must be forbidden")
    return failures


def run() -> tuple[dict, list[str]]:
    paths = sorted((ROOT / "skills").rglob("tests/cases.json"))
    errors = []
    for path in paths:
        errors.extend(f"{path.relative_to(ROOT)}: {failure}" for failure in check_skill(path))
    counts = {state: 0 for state in ("PASS", "DECLARED", "NOT_RUN")}
    for checks in MATRIX.values():
        for state in checks.values():
            counts[state] += len(paths)
    return {"skills": len(paths), "matrix": MATRIX, "counts": counts,
            "scope": "shared mock policy/result contracts and declared manual routes only",
            "live_skill_runtime": "NOT_RUN"}, errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable report")
    args = parser.parse_args()
    report, issues = run()
    if args.json:
        print(json.dumps({**report, "errors": issues}, indent=2))
    else:
        print(f"{report['skills']} skill files; shared checks {report['counts']['PASS']}, "
              f"declared routing {report['counts']['DECLARED']}, "
              f"skill runtime NOT_RUN {report['counts']['NOT_RUN']}")
        for issue in issues:
            print(issue, file=sys.stderr)
    raise SystemExit(bool(issues))
