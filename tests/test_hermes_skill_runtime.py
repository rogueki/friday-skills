"""Offline parser and staging tests; no Hermes model is invoked here."""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import evaluate_hermes_skill_runtime as runtime


def _session(*, view: str = runtime.SKILL, mode: str = "mock",
             status: str = "completed", result: bool = True,
             final: str = "Dies sind synthetische Testdaten.") -> dict:
    messages = [
        {"role": "user", "content": runtime.QUERY},
        {"role": "assistant", "tool_calls": [{"id": "view-1", "function": {
            "name": "skill_view", "arguments": json.dumps({"name": view})}}]},
        {"role": "tool", "tool_call_id": "view-1", "tool_name": "skill_view",
         "content": "Loaded skill:\n---\nname: friday-weather\n---\n# weather\n"},
        {"role": "assistant", "tool_calls": [{"id": "weather-1", "function": {
            "name": runtime.TOOL, "arguments": json.dumps({
                "latitude": 48.2082, "longitude": 16.3738, "mode": mode})}}]},
    ]
    if result:
        messages.append({"role": "tool", "tool_call_id": "weather-1",
                         "tool_name": runtime.TOOL, "content": json.dumps({
                             "status": status, "mode": mode, "write_effect": False,
                             "capability": {"name": "weather.read", "mode": mode,
                                            "synthetic": True},
                             "forecast": {"mode": mode, "temperature_c": 16.6}})})
    messages.append({"role": "assistant", "content": final, "tool_calls": None})
    return {"id": "20261015_183401_abcdef", "messages": messages}


class HermesWeatherRuntimeParserTests(unittest.TestCase):
    def test_offline_fixture_satisfies_parser_contract_only(self):
        self.assertEqual(runtime.score_session(_session())["status"], "PASS")

    def test_wrong_skill_live_call_missing_result_and_unlabelled_answer_fail(self):
        for session, reason in (
            (_session(view="friday-weather-alerts"), "wrong_or_missing_skill_view"),
            (_session(mode="live"), "non_mock_or_invalid_call"),
            (_session(result=False), "missing_tool_result"),
            (_session(status="blocked"), "invalid_mock_result"),
            (_session(final="16 Grad in Wien"), "final_not_labelled_synthetic"),
        ):
            with self.subTest(reason=reason):
                self.assertEqual(runtime.score_session(session)["reason_code"], reason)

    def test_prose_and_unmatched_tool_result_do_not_count(self):
        session = _session()
        session["messages"][1] = {"role": "assistant", "content": "skill_view(friday-weather)"}
        self.assertEqual(runtime.score_session(session)["reason_code"],
                         "wrong_or_missing_skill_view")
        session = _session()
        session["messages"][4]["tool_call_id"] = "other-call"
        self.assertEqual(runtime.score_session(session)["reason_code"],
                         "missing_tool_result")

    def test_skill_view_requires_correlated_loaded_content_before_weather(self):
        for change in ("missing", "wrong_id", "error", "after"):
            with self.subTest(change=change):
                session = _session()
                if change == "missing":
                    del session["messages"][2]
                elif change == "wrong_id":
                    session["messages"][2]["tool_call_id"] = "other-call"
                elif change == "error":
                    session["messages"][2]["content"] = "Error: skill unavailable"
                else:
                    view_result = session["messages"].pop(2)
                    session["messages"].insert(3, view_result)
                self.assertEqual(runtime.score_session(session)["reason_code"],
                                 "missing_or_failed_skill_view_result")

    @patch.object(runtime.subprocess, "run")
    @patch.object(runtime, "_local_model")
    def test_dry_run_does_not_call_model_or_hermes(self, model, process):
        report = runtime.evaluate()
        self.assertEqual(report["status"], "NOT_RUN")
        self.assertFalse(report["trace_verified"])
        model.assert_not_called()
        process.assert_not_called()

    def test_stage_is_mock_only_and_keeps_originals_untouched(self):
        plugin_source = (runtime.ROOT / "plugins/friday_weather/__init__.py").read_bytes()
        adapter_source = (runtime.ROOT / "adapters/weather.py").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            skills, support = runtime._stage(runtime.ROOT, home)
            self.assertEqual(len(list(skills.rglob("SKILL.md"))), 105)
            staged_plugin = (home / "plugins/friday_weather/__init__.py").read_text()
            staged_adapter = (support / "adapters/weather.py").read_text()
            self.assertIn('"enum": ["mock"]', staged_plugin)
            self.assertIn('if mode != "mock":', staged_plugin)
            self.assertIn('if mode != "mock":', staged_adapter)
            self.assertIn("    - friday-weather\n", runtime._config(skills, 11435))
            self.assertIn("127.0.0.1:11435/v1", runtime._config(skills, 11435))
        self.assertEqual(plugin_source,
                         (runtime.ROOT / "plugins/friday_weather/__init__.py").read_bytes())
        self.assertEqual(adapter_source,
                         (runtime.ROOT / "adapters/weather.py").read_bytes())

    def test_run_requires_artifact_and_allowlisted_local_model(self):
        with self.assertRaisesRegex(ValueError, "trace-output"):
            runtime.evaluate(run=True)
        for model, port in (("cloud-model", 11434), ("qwen3:4b", 443),
                            ("qwen3:4b", True)):
            with self.subTest(model=model, port=port), self.assertRaises(ValueError):
                runtime.evaluate(model=model, port=port)


if __name__ == "__main__":
    unittest.main()
