"""Bounded, resumable routing evaluation using isolated local Hermes sessions.

Each model attempt is reserved in an atomic report before invoking Hermes.
Unverified attempts require an explicit retry; a resumed run never silently
repeats a model call after a crash or missing trace.
"""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Iterator

if __package__:
    from scripts import local_hermes_smoke as smoke
    from scripts.evaluate_hermes_routing import ROOT, load_cases
else:
    import local_hermes_smoke as smoke
    from evaluate_hermes_routing import ROOT, load_cases


STATES = ("PASS", "FAIL", "PARTIAL", "NOT_RUN")
SCHEMA_VERSION = 1


def _digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True)
                          .encode("utf-8")).hexdigest()


def _revision(root: Path) -> str:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                            capture_output=True, text=True, timeout=10, check=False)
    revision = result.stdout.strip()
    if result.returncode or len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("a Git HEAD revision is required for local batch evaluation")
    return revision


def _skills_digest(root: Path) -> str:
    source = root / "skills"
    if not source.is_dir() or source.is_symlink():
        raise ValueError("skills source must be a real directory")
    entries = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("skills source contains a symlink")
        if path.is_file():
            entries.append((path.relative_to(source).as_posix(),
                            hashlib.sha256(path.read_bytes()).hexdigest()))
    return _digest(entries)


def _harness_digest() -> str:
    return _digest([hashlib.sha256(path.read_bytes()).hexdigest() for path in
                    (Path(__file__), Path(smoke.__file__), Path(load_cases.__code__.co_filename))])


def _artifact_path(root: Path, path: Path) -> Path:
    resolved = path.resolve()
    artifacts = (root / "artifacts").resolve()
    if not resolved.is_relative_to(artifacts):
        raise ValueError("batch reports and traces must be under ignored artifacts/")
    if resolved == artifacts or any(part.is_symlink() for part in
                                    (path, *path.parents)):
        raise ValueError("artifact path cannot be a directory or symlink")
    return resolved


def _trace_path(root: Path, output: Path, case: dict[str, Any]) -> Path:
    name = f"{case['skill']}--{case['case_id']}.jsonl"
    report_id = hashlib.sha256(str(output.resolve()).encode("utf-8")).hexdigest()[:16]
    return _artifact_path(root, root / "artifacts" / "hermes-routing-batch" / report_id / name)


def _record(case: dict[str, Any]) -> dict[str, Any]:
    return {"skill": case["skill"], "case_id": case["case_id"],
            "source": case["source"], "expected": case["expected"],
            "status": "NOT_RUN", "attempt_state": "PENDING", "trace_verified": False}


def _new_report(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cases, catalog, _ = load_cases(root)
    keys = [(case["skill"], case["case_id"]) for case in cases]
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate authored routing case")
    report = {"schema_version": SCHEMA_VERSION, "case_set_sha256": _digest({
                  "cases": cases, "catalog": catalog}),
              "model": smoke.MODEL, "provider": "local-ollama/hermes",
              "git_revision": _revision(root), "skills_sha256": _skills_digest(root),
              "harness_sha256": _harness_digest(),
              "case_total": len(cases), "attempted_total": 0,
              "attempt_reservations_total": 0,
              "cases": [_record(case) for case in cases]}
    _counts(report)
    return report, cases


def _counts(report: dict[str, Any]) -> None:
    counted = Counter(item["status"] for item in report["cases"])
    report["counts"] = {state: counted[state] for state in STATES}


def _trace_observation(root: Path, output: Path, case: dict[str, Any],
                       record: dict[str, Any]) -> None:
    expected_path = _trace_path(root, output, case)
    if record.get("trace_path") != str(expected_path) or not expected_path.is_file():
        raise ValueError("resume trace path is missing or unexpected")
    if expected_path.is_symlink():
        raise ValueError("resume trace is a symlink")
    trace_sha = hashlib.sha256(expected_path.read_bytes()).hexdigest()
    if trace_sha != record.get("trace_sha256"):
        raise ValueError("resume trace hash mismatch")
    session = smoke._single_exported_session(expected_path)
    views = smoke._skill_view_calls(session)
    if not views:
        raise ValueError("resume trace has no structured skill_view call")
    session_id = session.get("id", session.get("session_id"))
    if session_id != record.get("session_id") or len(views) != record.get("skill_view_count"):
        raise ValueError("resume trace observation mismatch")
    decision = ("select" if views[0] == case["skill"] else "reject") if len(views) == 1 else None
    status = ("PARTIAL" if len(views) != 1 or case["expected"] == "defer" else
              "PASS" if decision == case["expected"] else "FAIL")
    if status != record.get("status") or decision != record.get("observed_decision"):
        raise ValueError("resume status disagrees with structured trace")


def _resume_report(root: Path, path: Path, fresh: dict[str, Any],
                   cases: list[dict[str, Any]]) -> dict[str, Any]:
    saved = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(saved, dict):
        raise ValueError("resume report is not an object")
    if set(saved) != set(fresh):
        raise ValueError("resume report fields mismatch")
    for key in ("schema_version", "case_set_sha256", "model", "provider", "git_revision",
                "skills_sha256", "harness_sha256", "case_total"):
        if saved.get(key) != fresh[key]:
            raise ValueError(f"resume report {key} mismatch")
    records = saved.get("cases")
    if not isinstance(records, list) or len(records) != len(cases):
        raise ValueError("resume case list mismatch")
    for case, record in zip(cases, records, strict=True):
        if not isinstance(record, dict) or any(record.get(key) != case[key] for key in
                                                ("skill", "case_id", "source", "expected")):
            raise ValueError("resume case order or identity mismatch")
        allowed = set(_record(case)) | {"trace_path", "trace_sha256", "session_id",
                                       "skill_view_count", "observed_decision", "reason_code"}
        if not set(record).issubset(allowed) or record.get("reason_code") not in {
                None, "no_verified_trace", "attempt_error"}:
            raise ValueError("resume case fields invalid")
        state = record.get("attempt_state")
        if state not in {"PENDING", "STARTED", "FINISHED"} or record.get("status") not in STATES:
            raise ValueError("resume case state invalid")
        if state == "PENDING" and record != _record(case):
            raise ValueError("pending case contains attempt evidence")
        if record.get("trace_verified"):
            if state != "FINISHED":
                raise ValueError("verified trace has invalid attempt state")
            _trace_observation(root, path, case, record)
        elif record.get("status") != "NOT_RUN":
            raise ValueError("unverified case cannot have a scored status")
    if saved.get("attempted_total") != sum(record["attempt_state"] != "PENDING" for record in records):
        raise ValueError("resume attempt count mismatch")
    reservations = saved.get("attempt_reservations_total")
    if (not isinstance(reservations, int) or isinstance(reservations, bool)
            or reservations < saved["attempted_total"]):
        raise ValueError("resume reservation count invalid")
    _counts(saved)
    return saved


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=path.name + ".", suffix=".tmp",
                                         delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def _lock(path: Path) -> Iterator[None]:
    lock = path.with_name(path.name + ".lock")
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("x", encoding="utf-8") as stream:
        stream.write(str(os.getpid()))
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def evaluate(root: Path = ROOT, *, run: bool, max_cases: int | None = None,
             output: Path | None = None, resume: bool = False,
             retry_unverified: bool = False) -> dict[str, Any]:
    """Evaluate up to max_cases *new* attempts, recording each reservation first."""
    fresh, cases = _new_report(root)
    if run:
        if not isinstance(max_cases, int) or isinstance(max_cases, bool) or not 1 <= max_cases <= len(cases):
            raise ValueError("--run requires explicit --max-cases from 1 to case count")
        if output is None:
            raise ValueError("--run requires --output under artifacts/")
    elif max_cases is not None or resume or retry_unverified:
        raise ValueError("execution options require --run")
    if output is not None:
        output = _artifact_path(root, output)
    if not run:
        if output is not None:
            if output.exists():
                raise ValueError("dry-run report already exists")
            _write_report(output, fresh)
        return fresh

    assert output is not None
    with _lock(output):
        if resume:
            if not output.is_file():
                raise ValueError("--resume requires an existing report")
            report = _resume_report(root, output, fresh, cases)
        else:
            if output.exists():
                raise ValueError("report exists; use --resume or a new output path")
            report = fresh
        if not smoke.installed_exact_model():
            raise ValueError(f"exact local Ollama model {smoke.MODEL} is unavailable")
        if any(item["attempt_state"] != "PENDING" and not item["trace_verified"]
               for item in report["cases"]) and not retry_unverified:
            raise ValueError("unverified prior attempt; --retry-unverified is required to repeat it")
        if not resume:
            _write_report(output, report)
        attempts = 0
        for case, record in zip(cases, report["cases"], strict=True):
            if record["trace_verified"]:
                continue
            if record["attempt_state"] != "PENDING" and not retry_unverified:
                continue
            if attempts >= max_cases:
                break
            trace = _trace_path(root, output, case)
            if trace.exists():
                raise ValueError("case trace already exists; inspect it before retrying")
            for field in ("trace_path", "trace_sha256", "session_id", "skill_view_count",
                          "observed_decision", "reason_code"):
                record.pop(field, None)
            record.update({"status": "NOT_RUN", "attempt_state": "STARTED", "trace_verified": False})
            report["attempted_total"] = sum(item["attempt_state"] != "PENDING"
                                            for item in report["cases"])
            report["attempt_reservations_total"] += 1
            _counts(report)
            _write_report(output, report)
            attempts += 1
            try:
                result = smoke.execute(root, case["skill"], case["case_id"], run=True,
                                       trace_output=trace)
                if result.get("case_set_sha256") != report["case_set_sha256"]:
                    raise ValueError("single-case harness case-set hash changed")
                verified = result.get("trace_verified") is True
                record.update({"status": result["status"] if verified else "NOT_RUN",
                               "attempt_state": "FINISHED", "trace_verified": verified})
                if verified:
                    record.update({"trace_path": str(trace), "trace_sha256": result["trace_sha256"],
                                   "session_id": result["session_id"],
                                   "skill_view_count": len(result["observed_skill_views"]),
                                   "observed_decision": result.get("observed_decision")})
                    _trace_observation(root, output, case, record)
                else:
                    record["reason_code"] = "no_verified_trace"
            except Exception:
                for field in ("trace_path", "trace_sha256", "session_id", "skill_view_count",
                              "observed_decision"):
                    record.pop(field, None)
                record.update({"status": "NOT_RUN", "attempt_state": "FINISHED",
                               "trace_verified": False, "reason_code": "attempt_error"})
            _counts(report)
            _write_report(output, report)
        return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--max-cases", type=int, help="new attempt cap, required with --run")
    parser.add_argument("--output", type=Path, help="report under ignored artifacts/")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-unverified", action="store_true",
                        help="explicitly repeat attempts with no verified trace")
    args = parser.parse_args()
    try:
        report = evaluate(run=args.run, max_cases=args.max_cases, output=args.output,
                          resume=args.resume, retry_unverified=args.retry_unverified)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({"case_total": report["case_total"], "attempted_total":
                      report["attempted_total"], "attempt_reservations_total":
                      report["attempt_reservations_total"], "counts": report["counts"],
                      "case_set_sha256": report["case_set_sha256"]}, indent=2))
    return 1 if report["counts"]["FAIL"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
