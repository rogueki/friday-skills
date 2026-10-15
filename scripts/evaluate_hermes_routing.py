"""Opt-in evaluation of authored skill routing cases against an external router.

The runner has no model dependency. A caller must explicitly supply both a
callback and a case cap. The callback never receives the expected answer.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Mapping
import hashlib
import importlib
import json
from pathlib import Path
import re
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DECISIONS = frozenset({"select", "reject", "defer"})
IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/~-]{0,127}$")
RouteCallback = Callable[[dict[str, Any]], Mapping[str, Any]]


def load_cases(root: Path = ROOT) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, str]]:
    """Load the canonical catalog and the four declared cases per skill."""
    registry = json.loads((root / "registry/skills.json").read_text(encoding="utf-8"))
    catalog = [{"name": item["name"], "trigger": item["trigger"]}
               for item in registry["skills"]]
    names = {item["name"] for item in catalog}
    aliases = {name: name for name in names}
    for item in registry["skills"]:
        legacy = item.get("legacy_plan_name")
        if legacy:
            if legacy in aliases and aliases[legacy] != item["name"]:
                raise ValueError(f"ambiguous skill alias: {legacy}")
            aliases[legacy] = item["name"]
    cases = []
    for item in registry["skills"]:
        path = root / item["path"]
        case_path = path.parent / "tests/cases.json"
        data = json.loads(case_path.read_text(encoding="utf-8"))
        if data.get("skill") != item["name"]:
            raise ValueError(f"skill/path mismatch: {case_path}")
        entries = data.get("cases")
        if not isinstance(entries, list) or {entry.get("id") for entry in entries} != {
                "positive", "negative", "collision", "ambiguity"} or len(entries) != 4:
            raise ValueError(f"invalid routing cases: {case_path}")
        for entry in entries:
            if (entry.get("expected") not in DECISIONS
                    or not isinstance(entry.get("request"), str)
                    or not entry["request"].strip()):
                raise ValueError(f"invalid routing expectation: {case_path}")
            cases.append({"skill": item["name"], "case_id": entry["id"],
                          "request": entry["request"], "expected": entry["expected"],
                          "source": case_path.relative_to(root).as_posix()})
    return cases, catalog, aliases


def _normalize_decision(value: Mapping[str, Any], aliases: Mapping[str, str],
                        candidate: str) -> tuple[str, list[str], str, dict[str, str]]:
    decision = value.get("decision")
    if decision not in DECISIONS:
        raise ValueError("decision must be select, reject, or defer")
    selected = value.get("selected_skills", [])
    if not isinstance(selected, list) or any(not isinstance(name, str) for name in selected):
        raise ValueError("selected_skills must be a list of skill names")
    if any(name not in aliases for name in selected):
        raise ValueError("selected_skills contains an unknown skill")
    canonical = [aliases[name] for name in selected]
    if len(canonical) != len(set(canonical)):
        raise ValueError("selected_skills contains duplicate aliases")
    if (decision == "select") != (candidate in canonical):
        raise ValueError("select requires the candidate, reject/defer exclude it")
    evidence = value.get("evidence", {})
    if not isinstance(evidence, Mapping):
        raise ValueError("evidence must be an object")
    kind = evidence.get("kind", "synthetic")
    if kind not in {"synthetic", "model_inference_claimed"}:
        raise ValueError("evidence.kind must be synthetic or model_inference_claimed")
    metadata = {}
    if kind == "model_inference_claimed":
        for field in ("provider", "model", "response_id"):
            identifier = evidence.get(field)
            if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
                raise ValueError(f"model evidence requires a bounded {field} identifier")
            metadata[field] = identifier
    return decision, canonical, kind, metadata


def evaluate(root: Path = ROOT, *, route_decision: RouteCallback | None = None,
             max_cases: int | None = None) -> dict[str, Any]:
    """Evaluate at most max_cases; synthetic observations never count as routing PASS."""
    cases, catalog, aliases = load_cases(root)
    if route_decision is not None and (not isinstance(max_cases, int) or
                                       isinstance(max_cases, bool) or
                                       max_cases < 1 or max_cases > len(cases)):
        raise ValueError("a callback requires an explicit max_cases from 1 to the case count")
    if route_decision is None and max_cases is not None:
        raise ValueError("max_cases requires a route_decision callback")
    observations = []
    for index, case in enumerate(cases):
        record: dict[str, Any] = {key: case[key] for key in ("skill", "case_id", "source", "expected")}
        record.update({"status": "NOT_RUN", "actual": None, "evidence_kind": "none"})
        if route_decision is not None and index < max_cases:
            # Deliberately omit case_id, expectation, and source from model input.
            prompt_input = {"request": case["request"], "candidate_skill": case["skill"],
                            "catalog": [item.copy() for item in catalog]}
            start = time.monotonic()
            try:
                response = route_decision(prompt_input)
                if not isinstance(response, Mapping):
                    raise ValueError("callback must return an object")
                actual, selected, kind, metadata = _normalize_decision(response, aliases, case["skill"])
                record.update({"actual": actual, "selected_skills": selected,
                               "evidence_kind": kind, **metadata})
                if kind == "model_inference_claimed":
                    record["status"] = "PASS" if actual == case["expected"] else "FAIL"
                else:
                    record["synthetic_match"] = actual == case["expected"]
            except Exception as exc:  # Provider errors can contain secrets: retain only the class.
                record["error_type"] = type(exc).__name__
            record["elapsed_ms"] = round((time.monotonic() - start) * 1000, 2)
        observations.append(record)
    counts = Counter(record["status"] for record in observations)
    case_set_hash = hashlib.sha256(json.dumps({"cases": cases, "catalog": catalog},
                                               ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return {"schema_version": 1, "case_total": len(cases), "case_set_sha256": case_set_hash,
            "attempted": min(max_cases or 0, len(cases)) if route_decision else 0,
            "counts": {state: counts[state] for state in ("PASS", "FAIL", "NOT_RUN")},
            "evidence_note": "Model provenance is callback-attested; verify provider traces externally. Synthetic decisions never count as routing PASS.",
            "cases": observations}


def _load_callback(spec: str) -> RouteCallback:
    module_name, separator, function_name = spec.partition(":")
    if not separator or not module_name or not function_name or "." in function_name:
        raise ValueError("provider must be a module:function reference")
    callback = getattr(importlib.import_module(module_name), function_name)
    if not callable(callback):
        raise ValueError("provider target must be callable")
    return callback


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", help="explicit Python module:function callback; may make paid calls")
    parser.add_argument("--max-cases", type=int, help="required positive execution cap with --provider")
    parser.add_argument("--output", type=Path, help="write JSON evidence to this file instead of stdout")
    args = parser.parse_args()
    if bool(args.provider) != (args.max_cases is not None):
        parser.error("--provider and --max-cases must be supplied together")
    try:
        callback = _load_callback(args.provider) if args.provider else None
        report = evaluate(route_decision=callback, max_cases=args.max_cases)
    except (OSError, ValueError, ImportError, AttributeError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 1 if report["counts"]["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
