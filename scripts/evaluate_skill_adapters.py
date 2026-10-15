"""Run pinned offline adapter workflows; never count these as Hermes skill runs."""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from shared.scenarios import run_scenario  # noqa: E402


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _artifact_oracle(kind: str, result: dict[str, Any]) -> None:
    proposal = result.get("proposal", {})
    if kind == "mail_draft":
        _require(result["classification"]["priority"] == "P1", "P1 classification")
        _require(proposal.get("action") == "send_message" and proposal.get("risk_tier") == 2, "Tier-2 mail proposal")
        _require(result["draft"]["recipient"].endswith("@example.invalid"), "synthetic recipient")
    elif kind == "mail_injection":
        _require(result.get("reason") == "untrusted_mail", "injection blocked")
        _require("draft" not in result and "proposal" not in result, "no draft or send proposal")
    elif kind == "invoice_preview":
        draft = result["payment_draft"]
        _require(result["pdf_review"]["status"] == "completed", "PDF reviewed")
        _require((draft["type"], draft["amount"], draft["discount"]) ==
                 ("non_executable_payment_preview", "116.62", "2.38"), "masked discount preview")
        _require(result["invoice_facts"]["discount_applied"] is True, "discount checked")
        _require("iban" not in draft or "iban_masked" in draft, "no full IBAN field")
    elif kind == "invoice_altered":
        _require(result.get("reason") == "invoice_review_incomplete", "altered PDF blocked")
        _require("mock_requires_pinned_pdf_and_synthetic_records" in result["pdf_review"]["errors"], "pin failed")
        _require("payment_draft" not in result, "no payment draft")
    elif kind == "meeting_brief":
        _require({x["kind"] for x in result["sources"]} == {"calendar", "mail", "task_snapshot"}, "three sources")
        _require(len(result["briefing"]["open_points"]) == 2, "open tasks carried into briefing")
    elif kind == "meeting_missing":
        _require(result.get("reason") == "message_unavailable", "missing mail blocked")
        _require("briefing" not in result, "no fabricated briefing")
    elif kind == "weather_forecast":
        _require(result["forecast"]["source"].startswith("synthetic:"), "forecast provenance")
        _require(result["location"]["name"] == "Wien", "configured location")
        _require(result["voice_playback"]["played"] is False, "no voice playback")
    elif kind == "weather_stale":
        _require(result.get("reason") == "stale_weather" and "answer" not in result, "stale forecast withheld")
    elif kind == "travel_draft":
        draft = result["booking_draft"]
        _require(draft["reservation_status"] == "NOT_RESERVED", "booking not made")
        _require(draft["travelers"]["names"] == "REDACTED_NOT_COLLECTED", "names redacted")
        _require(result["approval"]["tier"] == 3 and not result["approval"]["granted"], "hard approval required")
        _require(proposal.get("action") == "booking" and not proposal.get("executed"), "booking proposal only")
    elif kind == "travel_stale":
        _require(result.get("reason") == "no_current_quote", "stale quote rejected")
        _require("booking_draft" not in result and "proposal" not in result, "no booking path")
    elif kind == "archive_manifest":
        _require(result["inventory"]["read_only"] and result["inventory"]["count"] == 3, "read-only inventory")
        _require(result["duplicate_groups"][0]["ids"] == ["a", "b"], "hash-based duplicate group")
        _require(all(x["operation"] == "copy_only_no_overwrite" and x["rollback"]["source_preserved"]
                     for x in result["manifest"]["entries"]), "reversible copy manifest")
        _require(proposal.get("action") == "archive_copy" and not proposal.get("executed"), "copy proposal only")
    elif kind == "archive_bad_hash":
        _require(result.get("reason") == "integrity_failure" and result.get("invalid_ids") == ["b"], "bad hash detected")
        _require("manifest" not in result and "proposal" not in result, "no migration proposal")
    elif kind == "loxone_proposal":
        _require(result["reading"]["synthetic"] and not result["reading"]["live_state_verified"], "synthetic status")
        _require(proposal.get("action") == "smart_home_write" and proposal.get("risk_tier") == 2, "Tier-2 light proposal")
        _require(result["verification"] == "not_executed" and not proposal["executed"], "no switch action")
    elif kind == "loxone_readback":
        _require(result.get("reason") == "readback_failed", "readback failure blocks success")
        _require(not proposal.get("executed"), "no live write")
    elif kind in {"tax_checklist", "tax_duplicate"}:
        _require(result["submission"] == "NOT_ATTEMPTED" and result["eligibility"] == "UNDETERMINED", "no tax filing")
        _require(result["review_required"] and result["finanzonline_draft"]["filing_status"] == "NOT_FILED",
                 "human review and non-executable checklist")
        _require(all(x["claim_amount_eur"] is None for x in result["candidates"]), "no asserted claim")
        _require("proposal" not in result, "no submit proposal")
        if kind == "tax_duplicate":
            _require(any(x["code"] == "duplicate_document" for x in result["issues"]), "duplicate flagged")
    elif kind in {"outage_block", "outage_recovery"}:
        _require(result["degraded_capability"] == "mail" and not result["blocked_action_executed"],
                 "mail action blocked")
        _require(result["requires_fresh_request"] and "proposal" not in result, "no auto-retry")
        if kind == "outage_recovery":
            _require(result["recovery_status"] == "mock_verified" and
                     len(result["readiness_probes_verified"]) == 2, "two readiness probes")
        else:
            _require(result["recovery_status"] != "mock_verified", "outage not recovered")
    elif kind == "variant":
        pass  # Variant-specific requirements are checked by _variant_oracle and manifest fields.
    else:
        raise ValueError(f"unknown oracle: {kind}")


def _check(case: dict[str, Any], result: dict[str, Any]) -> None:
    _require(result.get("scenario") == case["scenario"] and result.get("variant") == case["variant"],
             "wrong scenario or variant")
    _require(result.get("mode") == "mock" and result.get("external_effects") == 0, "offline mock boundary")
    _require(result.get("status") == case["expected_status"], "unexpected workflow status")
    trace = result.get("trace")
    _require(isinstance(trace, list), "missing trace")
    _require(set(case["required_trace"]) <= set(trace), "required trace step absent")
    _require(not set(case.get("forbidden_trace", [])) & set(trace), "forbidden trace step present")
    events = result.get("events")
    _require(isinstance(events, list) and bool(events) and
             events[-1].get("status") == case["expected_event_status"], "local event outcome")
    _require(all(not record.get("executed") for record in result.get("audit", [])), "executed audit action")
    if "expected_reason" in case:
        _require(result.get("reason") == case["expected_reason"], "unexpected refusal reason")
    for field in case.get("forbidden_artifacts", []):
        _require(field not in result, f"forbidden artifact: {field}")
    for field in case.get("required_artifacts", []):
        _require(field in result, f"missing artifact: {field}")
    for code in case.get("required_issue_codes", []):
        _require(code in {item["code"] for item in result.get("issues", [])}, f"missing issue: {code}")
    for code in case.get("required_pdf_errors", []):
        _require(code in result.get("pdf_review", {}).get("errors", []), f"missing PDF error: {code}")
    if "expected_recovery_reason" in case:
        _require(result.get("recovery_reason") == case["expected_recovery_reason"],
                 "unexpected recovery reason")
    if "expected_probe_count" in case:
        _require(len(result.get("readiness_probes_verified", [])) == case["expected_probe_count"],
                 "unexpected readiness probe count")
    if "expected_initial_health" in case:
        _require(result.get("initial_health", {}).get("status") == case["expected_initial_health"],
                 "unexpected initial health")
    mapping = result.get("dashboard_mapping")
    if mapping is not None:
        entries = mapping if isinstance(mapping, list) else [mapping]
        _require(bool(entries) and all(x.get("publishable") is False for x in entries),
                 "dashboard mapping must stay local")
    _artifact_oracle(case["oracle"], result)


def _variant_oracle(case: dict[str, Any], result: dict[str, Any]) -> None:
    """Check risk invariants for explicit variants, independently of adapter branches."""
    scenario = case["scenario"]
    variant = case["variant"]
    proposal = result.get("proposal")
    if proposal is not None:
        _require(proposal.get("executed") is False, "proposal executed")
    if scenario == "important_mail_e2e":
        if variant == "approved":
            sent = result["mock_send"]
            _require(sent["transport"] == "none" and sent["delivered"] is False, "external mail delivery")
            _require(sent["fingerprint"] == result["approval_preview"]["fingerprint"], "mail approval fingerprint")
        elif variant not in {"default", "injection"}:
            _require("mock_send" not in result, "mail sent after rejected grant")
    elif scenario == "invoice_pdf_to_payment_draft":
        if variant == "after_discount_deadline":
            draft = result["payment_draft"]
            _require((draft["amount"], draft["discount"], draft["gross"]) ==
                     ("119.00", "0.00", "119.00"), "expired discount still applied")
        elif variant != "default":
            _require("payment_draft" not in result and "proposal" not in result, "unsafe payment preview")
    elif scenario == "meeting" and variant != "default":
        _require("briefing" not in result, "briefing composed from incomplete sources")
    elif scenario == "weather":
        _require(result["voice_playback"] == {"status": "NOT_RUN", "played": False}, "voice playback")
        if variant != "default":
            _require("forecast" not in result and "answer" not in result, "unverified forecast disclosed")
    elif scenario == "family_travel":
        _require(result["profile"]["saved"] is False, "family profile persisted")
        if variant != "default":
            _require("proposal" not in result and "booking_draft" not in result, "booking from invalid quote")
    elif scenario == "photo_archive":
        if variant == "mock_approved":
            v = result["verification"]
            _require(v["source_preserved"] and v["sha256_matches"] and v["bad_ids"] == [], "archive integrity")
            _require(v["source_count"] == v["target_count"] == v["expected_count"] == 3,
                     "archive item count")
            _require(v["source_bytes"] == v["target_bytes"] == v["expected_bytes"], "archive byte count")
        elif variant in {"corrupt_target", "partial_copy"}:
            _require(result.get("simulation_failed") is True and "verification" not in result,
                     "failed archive copy verified")
        elif variant != "default":
            _require("verification" not in result, "archive copy despite refusal")
        if "approval" in result:
            _require(result["approval"]["trusted_host_approval"] is False, "mock grant represented as host grant")
    elif scenario == "loxone":
        if variant == "mock_approved":
            _require(result["verification"]["value"] == 100.0 and
                     result["verification"]["live_device_verified"] is False and
                     result["simulation"]["external_write"] is False, "Loxone mock readback")
        elif variant == "status_only":
            _require("proposal" not in result and "simulation" not in result, "status read triggered action")
        elif variant != "default":
            _require(not isinstance(result.get("verification"), dict), "failed control verified")
        if "approval" in result:
            _require(result["approval"]["trusted_host_approval"] is False, "mock grant represented as host grant")
    elif scenario == "austria_tax":
        _require(result["submission"] == "NOT_ATTEMPTED" and
                 result["finanzonline_draft"]["filing_status"] == "NOT_FILED" and
                 result["eligibility"] == "UNDETERMINED", "tax filing or eligibility asserted")
        _require(result["review_required"] and not any(x["claim_amount_eur"] is not None
                                                    for x in result["candidates"]), "unreviewed tax claim")
        _require("proposal" not in result, "tax submission proposed")
    elif scenario == "system_outage":
        _require(result["requires_fresh_request"] and not result["blocked_action_executed"] and
                 "proposal" not in result, "outage retried blocked action")
        if variant == "recovered":
            _require(result["recovery_status"] == "mock_verified" and
                     len(result["readiness_probes_verified"]) == 2 and
                     result["readiness_probes_verified"] == sorted(result["readiness_probes_verified"]),
                     "readiness evidence")
        else:
            _require(result["recovery_status"] == "not_verified", "unverified recovery")


def _source_hashes(root: Path, case: dict[str, Any], skill_paths: dict[str, str]) -> dict[str, str]:
    paths = [case["source"], "shared/scenarios.py", *case["fixtures"],
             *case.get("additional_sources", [])]
    paths += [skill_paths[name] for name in case["skills"]]
    hashes: dict[str, str] = {}
    for relative in dict.fromkeys(paths):
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"source outside repository or missing: {relative}")
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _declared_variants(source: Path, scenario: str) -> set[str]:
    """Read the adapter's current variant declaration without executing source text."""
    target = "allowed" if scenario == "invoice_pdf_to_payment_draft" else (
        "variants" if scenario == "weather" else "VARIANTS")
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign) or not any(isinstance(x, ast.Name) and x.id == target
                                                        for x in node.targets):
            continue
        expression = node.value
        if isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name) and expression.func.id == "frozenset":
            expression = expression.args[0]
        values = ast.literal_eval(expression)
        if not isinstance(values, (set, frozenset)) or not all(isinstance(x, str) for x in values):
            raise ValueError(f"unreadable variant inventory: {scenario}")
        return set(values)
    raise ValueError(f"missing variant inventory: {scenario}")


def evaluate(root: Path = ROOT, *, runner: Callable[..., dict[str, Any]] = run_scenario) -> dict[str, Any]:
    manifest_path = root / "registry/skill_adapter_bindings.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    registry = json.loads((root / "registry/skills.json").read_text(encoding="utf-8"))
    skill_paths = {item["name"]: item["path"] for item in registry["skills"]}
    _require(manifest["evidence_kind"] == "offline_adapter_execution", "wrong evidence kind")
    cases = manifest["cases"]
    _require(len({case["id"] for case in cases}) == len(cases), "duplicate case ID")
    _require(len({(case["scenario"], case["variant"]) for case in cases}) == len(cases),
             "duplicate scenario variant")
    records = []
    for case in cases:
        record: dict[str, Any] = {"case_id": case["id"], "scenario": case["scenario"],
                                  "variant": case["variant"], "skills_related": case["skills"]}
        try:
            _require(bool(case["skills"]) and all(name in skill_paths for name in case["skills"]),
                     "unknown related skill")
            record["source_sha256"] = _source_hashes(root, case, skill_paths)
            result = runner(case["scenario"], variant=case["variant"])
            if (case["scenario"] == "invoice_pdf_to_payment_draft" and
                    result.get("reason") == "pdf_parser_unavailable"):
                record.update(status="SKIP", reason="optional pypdf parser unavailable")
            else:
                _check(case, result)
                _variant_oracle(case, result)
                record.update(status="PASS", observed_status=result["status"],
                              trace_sha256=hashlib.sha256(json.dumps(result["trace"], sort_keys=True).encode()).hexdigest())
        except AssertionError as exc:
            record.update(status="FAIL", reason=str(exc))
        except Exception as exc:
            record.update(status="ERROR", reason=f"{type(exc).__name__}: {exc}")
        records.append(record)
    counts = Counter(x["status"] for x in records)
    scenarios = sorted({case["scenario"] for case in cases})
    coverage = {}
    for scenario in scenarios:
        bindings = [case for case in cases if case["scenario"] == scenario]
        source_variants = _declared_variants(root / bindings[0]["source"], scenario)
        declared = {case["variant"] for case in bindings}
        coverage[scenario] = {"source_variants": len(source_variants), "declared": len(bindings),
                              "passed": sum(record["scenario"] == scenario and record["status"] == "PASS"
                                            for record in records),
                              "untested_variants": sorted(source_variants - declared),
                              "unknown_variants": sorted(declared - source_variants)}
    coverage_gaps = {name: item for name, item in coverage.items()
                     if item["untested_variants"] or item["unknown_variants"]}
    return {
        "evidence_kind": "offline_adapter_execution",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "total": len(records), "counts": dict(counts), "cases": records,
        "scenario_coverage": coverage,
        "coverage_gaps": coverage_gaps,
        "hermes_routing": "NOT_RUN", "individual_skill_runtime": "NOT_RUN",
        "limitations": "Scenarios execute local synthetic adapters, not SKILL.md through a Hermes model; audit and mapping prove only local records.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable evidence")
    args = parser.parse_args()
    report = evaluate()
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Offline adapter workflows: {report['counts']} / {report['total']}")
        for scenario, coverage in report["scenario_coverage"].items():
            print(f"  {scenario}: {coverage['passed']}/{coverage['source_variants']} PASS; "
                  f"untested={coverage['untested_variants']}; unknown={coverage['unknown_variants']}")
        for case in report["cases"]:
            if case["status"] != "PASS":
                print(f"{case['case_id']}: {case['status']} {case.get('reason', '')}")
        print("Hermes routing: NOT_RUN; individual SKILL.md runtime: NOT_RUN")
    return 1 if report["counts"].get("FAIL", 0) or report["counts"].get("ERROR", 0) or report["coverage_gaps"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
