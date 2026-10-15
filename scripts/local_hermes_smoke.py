"""Opt-in, one-case Hermes routing smoke test against local Ollama only.

This does not preload a skill or use an active Hermes profile. A structured
``skill_view`` call in an isolated session export is the only scoring evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
from typing import Any
if __package__:
    from scripts.evaluate_hermes_routing import ROOT, load_cases
else:
    from evaluate_hermes_routing import ROOT, load_cases


MODEL = "qwen3:4b"
CONTEXT_TOKENS = 65536
RUN_BUDGET_SECONDS = 420
TIMEOUT_SECONDS = 480
VERSION_TIMEOUT_SECONDS = 30
EXPORT_TIMEOUT_SECONDS = 30
OLLAMA_TAGS = "http://127.0.0.1:11434/api/tags"
OLLAMA_BASE = "http://127.0.0.1:11434/v1"
CASE_IDS = frozenset({"positive", "negative", "collision", "ambiguity"})
SESSION_ID = re.compile(r"[0-9]{8}_[0-9]{6}_[0-9a-f]{6}", re.I)
ERROR_CODES = frozenset({"local_model_memory", "local_context_limit",
                         "hermes_context_minimum",
                         "local_ollama_unavailable", "local_model_unavailable",
                         "local_model_error", "hermes_cli_arguments",
                         "hermes_config_invalid", "hermes_runtime_dependency",
                         "hermes_nonzero_exit", "version_probe_timeout",
                         "chat_timeout", "session_export_timeout"})


def _error_code(stdout: str | None, stderr: str | None) -> str:
    """Return only a fixed diagnostic label; never persist process output."""
    output = ((stderr or "")[:8192] + "\n" + (stdout or "")[:8192]).lower()
    if "context window" in output and ("minimum 64,000" in output or
                                       "minimum 64000" in output):
        return "hermes_context_minimum"
    if any(term in output for term in ("not enough memory", "out of memory",
                                       "insufficient memory", "cannot allocate memory",
                                       "model requires more system memory")):
        return "local_model_memory"
    if "context" in output and any(term in output for term in ("exceed", "too long", "overflow")):
        return "local_context_limit"
    if any(term in output for term in ("connection refused", "cannot connect to ollama",
                                       "failed to connect to 127.0.0.1:11434")):
        return "local_ollama_unavailable"
    if "model" in output and "not found" in output:
        return "local_model_unavailable"
    if "ollama" in output and any(term in output for term in ("api error", "error 500", "http 500")):
        return "local_model_error"
    if any(term in output for term in ("unrecognized arguments", "invalid choice:", "usage: hermes")):
        return "hermes_cli_arguments"
    if any(term in output for term in ("invalid model.context_length", "invalid yaml",
                                       "yaml.scanner.scannererror")):
        return "hermes_config_invalid"
    if "no module named" in output:
        return "hermes_runtime_dependency"
    return "hermes_nonzero_exit"


def select_case(root: Path, skill: str, case_id: str) -> tuple[dict[str, Any], str]:
    if case_id not in CASE_IDS:
        raise ValueError("unknown authored case ID")
    cases, catalog, _ = load_cases(root)
    selected = [case for case in cases if case["skill"] == skill and case["case_id"] == case_id]
    if len(selected) != 1:
        raise ValueError("skill/case ID not found in authored case set")
    digest = hashlib.sha256(json.dumps({"cases": cases, "catalog": catalog},
                                       ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    return selected[0], digest


def installed_exact_model() -> bool:
    # urlopen has no proxy fallback here: local requests use a proxy-free opener.
    from urllib.request import ProxyHandler, build_opener

    with build_opener(ProxyHandler({})).open(OLLAMA_TAGS, timeout=3) as response:
        data = json.load(response)
    return any(item.get("name") == MODEL for item in data.get("models", [])
               if isinstance(item, dict))


def _copy_skills(source: Path, destination: Path) -> None:
    if not source.is_dir() or source.is_symlink():
        raise ValueError("skills source must be a real directory")
    for folder, dirs, files in os.walk(source, followlinks=False):
        for name in [*dirs, *files]:
            if (Path(folder) / name).is_symlink():
                raise ValueError("skills source contains a symlink")
    shutil.copytree(source, destination)


def _validate_context_tokens(context_tokens: int) -> None:
    if type(context_tokens) is not int or context_tokens != CONTEXT_TOKENS:
        raise ValueError("Hermes local routing requires exactly 65536 context tokens")


def _config(skills_copy: Path, context_tokens: int = CONTEXT_TOKENS) -> str:
    _validate_context_tokens(context_tokens)
    # JSON string literals are valid YAML scalars; a Windows path stays quoted.
    return ("model:\n"
            f"  default: {MODEL}\n"
            "  provider: custom\n"
            f"  base_url: {OLLAMA_BASE}\n"
            "  api_key: none\n"
            f"  context_length: {context_tokens}\n"
            f"  ollama_num_ctx: {context_tokens}\n"
            "fallback_providers: []\n"
            "skills:\n"
            "  external_dirs:\n"
            f"    - {json.dumps(str(skills_copy))}\n"
            "  write_approval: true\n"
            "  guard_agent_created: true\n"
            "plugins:\n"
            "  enabled: []\n"
            "mcp_servers: {}\n")


def _isolated_env(home: Path) -> dict[str, str]:
    # Hermes and its children receive no ambient API keys, auth tokens, proxy,
    # Python path, or profile overrides. Windows needs these for process start.
    keep = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
            "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA",
            "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE"}
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}
    env.update({"HERMES_HOME": str(home), "HOME": str(home),
                "USERPROFILE": str(home), "LOCALAPPDATA": str(home),
                "APPDATA": str(home), "XDG_CONFIG_HOME": str(home),
                "XDG_DATA_HOME": str(home), "HERMES_INFERENCE_PROVIDER": "custom",
                "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1",
                "NO_PROXY": "127.0.0.1,localhost", "no_proxy": "127.0.0.1,localhost"})
    return env


def _command(query_file: Path, run_budget_seconds: int = RUN_BUDGET_SECONDS) -> list[str]:
    return ["hermes", "chat", "--query-file", str(query_file),
            "--provider", "custom", "--model", MODEL, "--toolsets", "skills",
            "--max-turns", "2", "--run-budget", str(run_budget_seconds), "--ignore-rules", "-Q",
            "--source", "friday-local-routing-smoke"]


def _single_exported_session(export_path: Path) -> dict[str, Any]:
    """Require the one full-session JSONL row produced in the isolated home."""
    rows: list[dict[str, Any]] = []
    for line in export_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("session export contains invalid JSONL") from exc
        if not isinstance(row, dict):
            raise ValueError("session export contains a non-session row")
        rows.append(row)
    if len(rows) != 1:
        raise ValueError("session export must contain exactly one session")
    session = rows[0]
    session_id = session.get("id", session.get("session_id"))
    if (not isinstance(session_id, str) or not SESSION_ID.fullmatch(session_id)
            or ("id" in session and "session_id" in session
                and session["id"] != session["session_id"])):
        raise ValueError("session export has no valid Hermes session ID")
    return session


def _skill_view_calls(session: dict[str, Any]) -> list[str]:
    """Accept assistant tool-call objects only, never prose mentioning a tool."""
    found: list[str] = []
    messages = session.get("messages")
    if not isinstance(messages, list):
        return found
    for message in messages:
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        calls = message.get("tool_calls")
        if not isinstance(calls, list):
            continue
        for call in calls:
            if not isinstance(call, dict):
                continue
            function = call.get("function", call)
            if not isinstance(function, dict) or function.get("name") != "skill_view":
                continue
            args = function.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    continue
            if isinstance(args, dict) and isinstance(args.get("name"), str):
                found.append(args["name"])
    return found


def execute(root: Path, skill: str, case_id: str, *, run: bool,
            timeout: int = TIMEOUT_SECONDS, trace_output: Path | None = None,
            context_tokens: int = CONTEXT_TOKENS,
            run_budget_seconds: int = RUN_BUDGET_SECONDS) -> dict[str, Any]:
    _validate_context_tokens(context_tokens)
    if (not isinstance(run_budget_seconds, int) or isinstance(run_budget_seconds, bool)
            or not 180 <= run_budget_seconds <= 600):
        raise ValueError("run budget must be 180-600 seconds")
    if (not isinstance(timeout, int) or isinstance(timeout, bool)
            or not run_budget_seconds + 30 <= timeout <= run_budget_seconds + 180
            or timeout > 780):
        raise ValueError("subprocess timeout must exceed run budget by 30-180 seconds")
    case, case_hash = select_case(root, skill, case_id)
    report: dict[str, Any] = {"case_set_sha256": case_hash, "skill": skill,
                              "case_id": case_id, "model": MODEL, "provider": "custom",
                              "base_url": OLLAMA_BASE, "status": "NOT_RUN",
                              "trace_verified": False, "observed_skill_views": [],
                              "requested_context_tokens": context_tokens,
                              "effective_context_verified": False,
                              "run_budget_seconds": run_budget_seconds,
                              "subprocess_timeout_seconds": timeout}
    if run:
        try:
            if not installed_exact_model():
                report["reason"] = "exact local model is not installed"
                return report
        except (OSError, ValueError, TimeoutError):
            report["reason"] = "local Ollama model list unavailable"
            return report

    with tempfile.TemporaryDirectory(prefix="friday-hermes-smoke-") as temporary:
        base = Path(temporary)
        home = base / "hermes-home"
        work = base / "work"
        home.mkdir()
        work.mkdir()
        copied = home / "skills-copy"
        _copy_skills(root / "skills", copied)
        (home / "config.yaml").write_text(_config(copied, context_tokens), encoding="utf-8")
        query_file = work / "query.txt"
        query_file.write_text(case["request"] + "\n", encoding="utf-8")
        report["skill_count"] = len(list(copied.rglob("SKILL.md")))
        report["isolation"] = "temporary Hermes home, skill copy and working directory"
        report["command_flags"] = _command(Path("<isolated-query-file>"), run_budget_seconds)[1:]
        if not run:
            report["reason"] = "dry run; no Ollama or Hermes call"
            return report

        env = _isolated_env(home)
        start = time.monotonic()
        phase = "version_probe"
        try:
            version = subprocess.run(["hermes", "--version"], cwd=work, env=env,
                                     capture_output=True, text=True,
                                     encoding="utf-8", errors="replace",
                                     timeout=VERSION_TIMEOUT_SECONDS, check=False)
            version_lines = version.stdout.splitlines()
            report["hermes_version"] = version_lines[0][:160] if version.returncode == 0 and version_lines else None
            phase = "chat"
            invocation = subprocess.run(_command(query_file, run_budget_seconds), cwd=work, env=env,
                                        capture_output=True, text=True, encoding="utf-8",
                                        errors="replace", timeout=timeout, check=False)
            report["exit_code"] = invocation.returncode
            report["elapsed_seconds"] = round(time.monotonic() - start, 2)
            if invocation.returncode != 0:
                report["reason"] = "Hermes process exited unsuccessfully; output suppressed"
                report["reason_code"] = _error_code(invocation.stdout, invocation.stderr)
                return report
            export = work / "session.jsonl"
            phase = "session_export"
            export_command = ["hermes", "sessions", "export", "--format", "jsonl",
                              "--redact", "--yes", "--source", "friday-local-routing-smoke"]
            export_command.append(str(export))
            exported = subprocess.run(export_command, cwd=work, env=env,
                                      capture_output=True, text=True,
                                      encoding="utf-8", errors="replace",
                                      timeout=EXPORT_TIMEOUT_SECONDS, check=False)
            if exported.returncode != 0 or not export.is_file():
                report["reason"] = "session export unavailable; routing unverified"
                return report
            try:
                session = _single_exported_session(export)
            except ValueError as exc:
                report["reason"] = str(exc)
                return report
            report["session_id"] = session.get("id", session.get("session_id"))
            views = _skill_view_calls(session)
            report["observed_skill_views"] = views
            if trace_output is None:
                report["status"] = "PARTIAL" if views else "NOT_RUN"
                report["reason"] = ("trace found but not retained for independent review"
                                    if views else "no structured assistant skill_view trace found")
                return report
            trace_output = trace_output.resolve()
            if trace_output.is_relative_to(root.resolve()) and not trace_output.is_relative_to((root / "artifacts").resolve()):
                raise ValueError("trace output inside repository must be under ignored artifacts/")
            trace_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(export, trace_output)
            report["trace_sha256"] = hashlib.sha256(trace_output.read_bytes()).hexdigest()
            report["trace_path"] = str(trace_output)
            report["trace_verified"] = True
            if not views:
                report["reason"] = "no structured assistant skill_view trace found"
                return report
            # A single selected candidate can be scored; absence or multiple
            # views needs manual inspection of the isolated session trace.
            if len(views) != 1:
                report["status"] = "PARTIAL"
                report["reason"] = "multiple skill_view calls need manual routing review"
            else:
                actual = "select" if views[0] == skill else "reject"
                report["observed_decision"] = actual
                if case["expected"] == "defer":
                    report["status"] = "PARTIAL"
                    report["reason"] = "skill_view alone cannot prove defer semantics"
                else:
                    report["status"] = "PASS" if actual == case["expected"] else "FAIL"
            return report
        except subprocess.TimeoutExpired:
            report["elapsed_seconds"] = round(time.monotonic() - start, 2)
            report["reason_code"] = f"{phase}_timeout"
            report["reason"] = "Hermes subprocess timed out; routing unverified"
            return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--case-id", choices=sorted(CASE_IDS), required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--trace-output", type=Path,
                        help="retain Hermes-redacted JSONL for independent review; may include case text")
    parser.add_argument("--context-tokens", type=int, choices=(CONTEXT_TOKENS,),
                        default=CONTEXT_TOKENS)
    parser.add_argument("--run-budget-seconds", type=int, default=RUN_BUDGET_SECONDS)
    parser.add_argument("--timeout-seconds", type=int, default=TIMEOUT_SECONDS)
    args = parser.parse_args()
    try:
        result = execute(ROOT, args.skill, args.case_id, run=args.run,
                         trace_output=args.trace_output, context_tokens=args.context_tokens,
                         run_budget_seconds=args.run_budget_seconds,
                         timeout=args.timeout_seconds)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
