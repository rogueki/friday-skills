"""Opt-in, one-case Hermes weather skill execution against local Ollama."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any
from urllib.request import HTTPRedirectHandler, ProxyHandler, build_opener

if __package__:
    from scripts import local_hermes_smoke as smoke
else:
    import local_hermes_smoke as smoke


ROOT = smoke.ROOT
MODELS = frozenset({"qwen3:4b", "qwen3.5:0.8b"})
PORTS = frozenset({11434, 11435})
SOURCE = "friday-local-weather-runtime"
QUERY = ("Wie wird das Wetter in Wien (48.2082 N, 16.3738 E) am 15. Oktober "
         "2026 um 14:00 UTC? Nutze ausschließlich den Wetter-Mock. "
         "Kennzeichne die Antwort ausdrücklich als synthetische Testdaten.")
TOOL = "friday_weather_forecast"
SKILL = "friday-weather"


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request: Any, fp: Any, code: int, msg: str,
                         headers: Any, newurl: str) -> None:
        raise ValueError("local model-list redirect rejected")


def _local_model(model: str, port: int) -> bool:
    if model not in MODELS or type(port) is not int or port not in PORTS:
        raise ValueError("only allowlisted local Ollama model and port are supported")
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    with opener.open(f"http://127.0.0.1:{port}/api/tags", timeout=3) as response:
        data = json.load(response)
    return any(isinstance(item, dict) and item.get("name") == model
               for item in data.get("models", []))


def _stage(root: Path, home: Path) -> tuple[Path, Path]:
    """Stage source-matched plugin and adapter with two independent mock guards."""
    skills = home / "skills-copy"
    smoke._copy_skills(root / "skills", skills)
    support = home / "friday-support"
    (support / "adapters").mkdir(parents=True)
    (support / "fixtures" / "weather").mkdir(parents=True)
    shutil.copy2(root / "adapters" / "__init__.py", support / "adapters" / "__init__.py")
    adapter = (root / "adapters" / "weather.py").read_text(encoding="utf-8")
    guard = 'if mode not in {"mock", "read_only", "live"}:'
    if adapter.count(guard) != 1:
        raise ValueError("weather adapter source changed; mock guard must be reviewed")
    adapter = adapter.replace(guard, 'if mode != "mock":')
    (support / "adapters" / "weather.py").write_text(adapter, encoding="utf-8")
    shutil.copy2(root / "fixtures" / "weather" / "adapter_forecast.json",
                 support / "fixtures" / "weather" / "adapter_forecast.json")
    plugin_src = root / "plugins" / "friday_weather"
    plugin_dst = home / "plugins" / "friday_weather"
    plugin_dst.mkdir(parents=True)
    plugin = (plugin_src / "__init__.py").read_text(encoding="utf-8")
    changes = {
        '"enum": ["mock", "read_only", "live"]': '"enum": ["mock"]',
        'if mode not in ("mock", "read_only", "live"):': 'if mode != "mock":',
    }
    for before, after in changes.items():
        if plugin.count(before) != 1:
            raise ValueError("weather plugin source changed; mock guard must be reviewed")
        plugin = plugin.replace(before, after)
    (plugin_dst / "__init__.py").write_text(plugin, encoding="utf-8")
    shutil.copy2(plugin_src / "plugin.yaml", plugin_dst / "plugin.yaml")
    return skills, support


def _config(skills: Path, port: int) -> str:
    config = smoke._config(skills)
    config = config.replace(smoke.OLLAMA_BASE, f"http://127.0.0.1:{port}/v1")
    config = config.replace("  enabled: []\n", "  enabled:\n    - friday-weather\n")
    if f"127.0.0.1:{port}/v1" not in config or "    - friday-weather\n" not in config:
        raise ValueError("isolated Hermes config could not be constructed")
    return config


def _arguments(call: dict[str, Any]) -> dict[str, Any] | None:
    function = call.get("function", call)
    if not isinstance(function, dict):
        return None
    args = function.get("arguments")
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except json.JSONDecodeError:
            return None
    return args if isinstance(args, dict) else None


def _calls(message: dict[str, Any]) -> list[tuple[str, dict[str, Any] | None, str | None]]:
    if message.get("role") != "assistant" or not isinstance(message.get("tool_calls"), list):
        return []
    calls = []
    for call in message["tool_calls"]:
        if not isinstance(call, dict):
            continue
        function = call.get("function", call)
        if isinstance(function, dict) and isinstance(function.get("name"), str):
            calls.append((function["name"], _arguments(call), call.get("id")))
    return calls


def score_session(session: dict[str, Any]) -> dict[str, Any]:
    """Score structured Hermes export only; never infer execution from prose."""
    messages = session.get("messages")
    if not isinstance(messages, list):
        return {"status": "NOT_RUN", "reason_code": "no_messages"}
    views: list[str] = []
    view_calls: list[tuple[int, str | None]] = []
    forecast_calls: list[tuple[int, dict[str, Any] | None, str | None]] = []
    unexpected_tools: list[str] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            continue
        for name, args, call_id in _calls(message):
            if name == "skill_view":
                view_calls.append((index, call_id))
                if args and isinstance(args.get("name"), str):
                    views.append(args["name"])
            elif name == TOOL:
                forecast_calls.append((index, args, call_id))
            else:
                unexpected_tools.append(name)
    observed = {"observed_skill_views": views,
                "weather_call_count": len(forecast_calls),
                "unexpected_tools": unexpected_tools}
    if views != [SKILL]:
        return {**observed, "status": "FAIL", "reason_code": "wrong_or_missing_skill_view"}
    if len(view_calls) != 1 or not isinstance(view_calls[0][1], str) or not view_calls[0][1]:
        return {**observed, "status": "FAIL", "reason_code": "invalid_skill_view_call"}
    if unexpected_tools:
        return {**observed, "status": "FAIL", "reason_code": "unexpected_tool_call"}
    if len(forecast_calls) != 1:
        return {**observed, "status": "FAIL", "reason_code": "wrong_weather_call_count"}
    call_index, args, call_id = forecast_calls[0]
    if not args or args.get("mode") != "mock" or not isinstance(call_id, str) or not call_id:
        return {**observed, "status": "FAIL", "reason_code": "non_mock_or_invalid_call"}
    view_index, view_id = view_calls[0]
    if view_index >= call_index:
        return {**observed, "status": "FAIL", "reason_code": "skill_not_viewed_first"}
    view_results = [(index, message) for index, message in enumerate(messages)
                    if view_index < index < call_index and isinstance(message, dict)
                    and message.get("role") == "tool" and message.get("tool_call_id") == view_id
                    and message.get("tool_name") == "skill_view"]
    if (len(view_results) != 1 or not isinstance(view_results[0][1].get("content"), str)
            or f"---\nname: {SKILL}\n" not in view_results[0][1]["content"]):
        return {**observed, "status": "FAIL", "reason_code": "missing_or_failed_skill_view_result"}
    results = [(index, message) for index, message in enumerate(messages)
               if index > call_index and isinstance(message, dict)
               and message.get("role") == "tool" and message.get("tool_call_id") == call_id
               and message.get("tool_name") == TOOL]
    if len(results) != 1:
        return {**observed, "status": "FAIL", "reason_code": "missing_tool_result"}
    result_index, result_msg = results[0]
    try:
        result = json.loads(result_msg.get("content"))
    except (TypeError, json.JSONDecodeError):
        return {**observed, "status": "FAIL", "reason_code": "invalid_tool_result"}
    capability = result.get("capability") if isinstance(result, dict) else None
    if (not isinstance(result, dict) or result.get("status") != "completed"
            or result.get("mode") != "mock" or result.get("write_effect") is not False
            or not isinstance(capability, dict) or capability.get("name") != "weather.read"
            or capability.get("synthetic") is not True or capability.get("mode") != "mock"
            or not isinstance(result.get("forecast"), dict)
            or result["forecast"].get("mode") != "mock"):
        return {**observed, "status": "FAIL", "reason_code": "invalid_mock_result"}
    finals = [message.get("content") for message in messages[result_index + 1:]
              if isinstance(message, dict) and message.get("role") == "assistant"
              and not message.get("tool_calls") and isinstance(message.get("content"), str)
              and message.get("content").strip()]
    if not finals or not any(word in finals[-1].casefold()
                             for word in ("synthet", "mock", "testdaten")):
        return {**observed, "status": "FAIL", "reason_code": "final_not_labelled_synthetic"}
    return {**observed, "status": "PASS", "reason_code": "verified_mock_skill_execution"}


def evaluate(root: Path = ROOT, *, run: bool = False, model: str = smoke.MODEL,
             port: int = 11434, trace_output: Path | None = None) -> dict[str, Any]:
    if model not in MODELS or type(port) is not int or port not in PORTS:
        raise ValueError("only allowlisted local Ollama model and port are supported")
    report: dict[str, Any] = {"skill": SKILL, "case_id": "weather-positive-mock",
                              "model": model, "ollama_url": f"http://127.0.0.1:{port}/v1",
                              "query_sha256": hashlib.sha256(QUERY.encode("utf-8")).hexdigest(),
                              "source_sha256": {name: hashlib.sha256((root / name).read_bytes()).hexdigest()
                                                for name in (
                                  "skills/weather/friday-weather/SKILL.md",
                                  "plugins/friday_weather/__init__.py",
                                  "plugins/friday_weather/plugin.yaml",
                                  "adapters/weather.py",
                                  "fixtures/weather/adapter_forecast.json")},
                              "requested_context_tokens": smoke.CONTEXT_TOKENS,
                              "effective_context_verified": False, "status": "NOT_RUN",
                              "trace_verified": False, "reason_code": "dry_run"}
    if not run:
        report["reason"] = "dry run; no Hermes or Ollama call"
        return report
    if trace_output is None:
        raise ValueError("--run requires --trace-output under ignored artifacts/")
    trace_output = trace_output.resolve()
    if (not trace_output.is_relative_to((root / "artifacts").resolve())
            or trace_output.exists() or any(part.is_symlink() for part in trace_output.parents)):
        raise ValueError("trace output must be a regular file under ignored artifacts/")
    try:
        if not _local_model(model, port):
            report.update(reason_code="model_not_installed", reason="exact local model absent")
            return report
    except (OSError, ValueError, TimeoutError):
        report.update(reason_code="ollama_unavailable", reason="local model list unavailable")
        return report
    with tempfile.TemporaryDirectory(prefix="friday-hermes-weather-") as temporary:
        base = Path(temporary)
        home, work = base / "hermes-home", base / "work"
        home.mkdir()
        work.mkdir()
        skills, support = _stage(root, home)
        config = _config(skills, port).replace(f"  default: {smoke.MODEL}\n",
                                                f"  default: {model}\n")
        (home / "config.yaml").write_text(config, encoding="utf-8")
        query_file = work / "query.txt"
        query_file.write_text(QUERY + "\n", encoding="utf-8")
        env = smoke._isolated_env(home)
        env.update({"FRIDAY_SKILLS_ROOT": str(support), "PYTHONPATH": str(support)})
        command = smoke._command(query_file)
        command[command.index("--model") + 1] = model
        command[command.index("--toolsets") + 1] = "skills,friday_weather"
        command[command.index("--max-turns") + 1] = "4"
        command[command.index("--source") + 1] = SOURCE
        started = time.monotonic()
        phase = "version_probe"
        try:
            version = subprocess.run(["hermes", "--version"], cwd=work, env=env,
                                     capture_output=True, text=True, encoding="utf-8",
                                     errors="replace", timeout=smoke.VERSION_TIMEOUT_SECONDS,
                                     check=False)
            if version.returncode != 0 or "Hermes Agent v0.20.5" not in version.stdout:
                report["reason_code"] = "wrong_hermes_version"
                return report
            report["hermes_version"] = "0.20.5"
            phase = "chat"
            chat = subprocess.run(command, cwd=work, env=env, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  timeout=smoke.TIMEOUT_SECONDS, check=False)
            report["exit_code"] = chat.returncode
            if chat.returncode != 0:
                report["reason_code"] = smoke._error_code(chat.stdout, chat.stderr)
                return report
            phase = "session_export"
            export = work / "session.jsonl"
            exported = subprocess.run(["hermes", "sessions", "export", "--format", "jsonl",
                                       "--redact", "--yes", "--source", SOURCE, str(export)],
                                      cwd=work, env=env, capture_output=True, text=True,
                                      encoding="utf-8", errors="replace",
                                      timeout=smoke.EXPORT_TIMEOUT_SECONDS, check=False)
            if exported.returncode != 0 or not export.is_file():
                report["reason_code"] = "missing_session_export"
                return report
            try:
                session = smoke._single_exported_session(export)
            except ValueError:
                report["reason_code"] = "invalid_session_export"
                return report
            trace_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(export, trace_output)
            report.update(trace_verified=True, trace_path=str(trace_output),
                          trace_sha256=hashlib.sha256(trace_output.read_bytes()).hexdigest(),
                          session_id=session.get("id", session.get("session_id")))
            report.update(score_session(session))
            return report
        except subprocess.TimeoutExpired:
            report["reason_code"] = f"{phase}_timeout"
            return report
        finally:
            report["elapsed_seconds"] = round(time.monotonic() - started, 2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", action="store_true", help="explicitly run one local model case")
    parser.add_argument("--model", choices=sorted(MODELS), default=smoke.MODEL)
    parser.add_argument("--ollama-port", type=int, choices=sorted(PORTS), default=11434)
    parser.add_argument("--trace-output", type=Path,
                        help="required for --run; retained Hermes-redacted JSONL in artifacts/")
    args = parser.parse_args()
    try:
        result = evaluate(run=args.run, model=args.model, port=args.ollama_port,
                          trace_output=args.trace_output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
