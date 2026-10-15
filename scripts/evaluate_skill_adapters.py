"""Run pinned offline adapter workflows; never count these as Hermes skill runs."""

from __future__ import annotations

import argparse
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
    mapping = result.get("dashboard_mapping")
    if mapping is not None:
        entries = mapping if isinstance(mapping, list) else [mapping]
        _require(bool(entries) and all(x.get("publishable") is False for x in entries),
                 "dashboard mapping must stay local")
    _artifact_oracle(case["oracle"], result)


def _source_hashes(root: Path, case: dict[str, Any], skill_paths: dict[str, str]) -> dict[str, str]:
    paths = [case["source"], "shared/scenarios.py", *case["fixtures"]]
    paths += [skill_paths[name] for name in case["skills"]]
    hashes: dict[str, str] = {}
    for relative in dict.fromkeys(paths):
        path = (root / relative).resolve()
        if not path.is_relative_to(root.resolve()) or not path.is_file():
            raise ValueError(f"source outside repository or missing: {relative}")
        hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def evaluate(root: Path = ROOT, *, runner: Callable[..., dict[str, Any]] = run_scenario) -> dict[str, Any]:
    manifest_path = root / "registry/skill_adapter_bindings.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    registry = json.loads((root / "registry/skills.json").read_text(encoding="utf-8"))
    skill_paths = {item["name"]: item["path"] for item in registry["skills"]}
    _require(manifest["evidence_kind"] == "offline_adapter_execution", "wrong evidence kind")
    cases = manifest["cases"]
    _require(len({case["id"] for case in cases}) == len(cases), "duplicate case ID")
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
                record.update(status="PASS", observed_status=result["status"],
                              trace_sha256=hashlib.sha256(json.dumps(result["trace"], sort_keys=True).encode()).hexdigest())
        except AssertionError as exc:
            record.update(status="FAIL", reason=str(exc))
        except Exception as exc:
            record.update(status="ERROR", reason=f"{type(exc).__name__}: {exc}")
        records.append(record)
    counts = Counter(x["status"] for x in records)
    return {
        "evidence_kind": "offline_adapter_execution",
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "total": len(records), "counts": dict(counts), "cases": records,
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
        for case in report["cases"]:
            if case["status"] != "PASS":
                print(f"{case['case_id']}: {case['status']} {case.get('reason', '')}")
        print("Hermes routing: NOT_RUN; individual SKILL.md runtime: NOT_RUN")
    return 1 if report["counts"].get("FAIL", 0) or report["counts"].get("ERROR", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
