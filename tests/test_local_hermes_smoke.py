"""Offline checks; these tests never contact Ollama or run Hermes."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import local_hermes_smoke as smoke


class LocalHermesSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "registry").mkdir()
        (self.root / "skills" / "friday-a" / "tests").mkdir(parents=True)
        (self.root / "registry" / "skills.json").write_text(json.dumps({"skills": [{
            "name": "friday-a", "trigger": "A", "path": "skills/friday-a/SKILL.md"}]}), encoding="utf-8")
        (self.root / "skills" / "friday-a" / "SKILL.md").write_text("---\nname: friday-a\n---\n", encoding="utf-8")
        (self.root / "skills" / "friday-a" / "tests" / "cases.json").write_text(json.dumps({
            "skill": "friday-a", "cases": [{"id": cid, "request": "Find A", "expected": expected}
                for cid, expected in [("positive", "select"), ("negative", "reject"),
                                      ("collision", "reject"), ("ambiguity", "defer")]]}), encoding="utf-8")

    @patch.object(smoke, "installed_exact_model")
    @patch.object(smoke.subprocess, "run")
    def test_dry_run_isolated_and_no_process_or_model_call(self, process, model):
        result = smoke.execute(self.root, "friday-a", "positive", run=False)
        self.assertEqual(result["status"], "NOT_RUN")
        self.assertEqual(result["skill_count"], 1)
        self.assertTrue(result["case_set_sha256"])
        self.assertNotIn("Find A", json.dumps(result))
        process.assert_not_called()
        model.assert_not_called()

    @patch.object(smoke, "installed_exact_model", return_value=False)
    @patch.object(smoke.subprocess, "run")
    def test_missing_exact_model_rejected_before_execution(self, process, _model):
        result = smoke.execute(self.root, "friday-a", "positive", run=True)
        self.assertEqual(result["status"], "NOT_RUN")
        self.assertIn("not installed", result["reason"])
        process.assert_not_called()

    def test_command_bounds_and_no_preload_or_yolo(self):
        command = smoke._command(Path("query.txt"))
        self.assertIn("--provider", command)
        self.assertIn("--max-turns", command)
        self.assertIn("--run-budget", command)
        self.assertIn("--ignore-rules", command)
        self.assertNotIn("--skills", command)
        self.assertNotIn("--yolo", command)
        self.assertNotIn("-z", command)

    def test_trace_requires_structured_assistant_tool_call(self):
        trace = self.root / "trace.jsonl"
        trace.write_text(json.dumps({"id": "20261015_183401_abcdef", "messages": [
            {"role": "assistant", "content": "I called skill_view(friday-a)"},
            {"role": "user", "tool_calls": [{"function": {"name": "skill_view", "arguments": "{\"name\":\"friday-a\"}"}}]},
            {"role": "assistant", "tool_calls": [{"function": {"name": "skill_view", "arguments": "{\"name\":\"friday-a\"}"}}]},
        ]}), encoding="utf-8")
        self.assertEqual(smoke._skill_view_calls(smoke._single_exported_session(trace)),
                         ["friday-a"])

    def test_export_must_have_exactly_one_native_session_id(self):
        trace = self.root / "trace.jsonl"
        trace.write_text("", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            smoke._single_exported_session(trace)
        valid = {"id": "20261015_183401_abcdef", "messages": []}
        trace.write_text(json.dumps(valid) + "\n" + json.dumps(valid) + "\n",
                         encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            smoke._single_exported_session(trace)
        for identifier in ("123e4567-e89b-12d3-a456-426614174000",
                           "20261015_183401_abcdef-extra", "20261015_183401_abcde"):
            trace.write_text(json.dumps({"id": identifier, "messages": []}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "valid Hermes session ID"):
                smoke._single_exported_session(trace)
        trace.write_text(json.dumps({**valid, "session_id": "20261015_183401_123abc"}),
                         encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "valid Hermes session ID"):
            smoke._single_exported_session(trace)

    def test_symlinks_rejected_before_copy(self):
        source = self.root / "skills"
        link = source / "external"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlink creation unavailable")
        with self.assertRaisesRegex(ValueError, "symlink"):
            smoke._copy_skills(source, self.root / "copy")

    @patch.object(smoke, "installed_exact_model", return_value=True)
    @patch.object(smoke.subprocess, "run")
    def test_no_trace_never_becomes_pass(self, process, _model):
        class Result:
            returncode = 0
            stdout = "Hermes Agent v0.20.5\n"
            stderr = ""
        process.return_value = Result()
        result = smoke.execute(self.root, "friday-a", "positive", run=True)
        self.assertEqual(result["status"], "NOT_RUN")
        self.assertFalse(result["trace_verified"])
        calls = process.call_args_list
        self.assertEqual(len(calls), 3)
        hermes = calls[1]
        self.assertNotEqual(hermes.kwargs["cwd"], self.root)
        self.assertNotIn(str(self.root), str(hermes.args[0]))
        self.assertEqual(hermes.kwargs["env"]["HERMES_HOME"],
                         str(hermes.kwargs["cwd"].parent / "hermes-home"))

    @patch.object(smoke, "installed_exact_model", return_value=True)
    @patch.object(smoke.subprocess, "run")
    def test_retained_structured_trace_scores_only_one_case(self, process, _model):
        session_id = "20261015_183401_abcdef"
        active_config = self.root / "active" / "config.yaml"
        active_config.parent.mkdir()
        active_config.write_text("active: untouched\n", encoding="utf-8")

        class Result:
            returncode = 0
            stderr = ""
            stdout = ""

        def invoke(command, **kwargs):
            self.assertNotEqual(kwargs["env"]["HERMES_HOME"], str(active_config.parent))
            self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
            self.assertNotIn("OPENROUTER_API_KEY", kwargs["env"])
            self.assertEqual((Path(kwargs["env"]["HERMES_HOME"]) / "config.yaml").is_file(), True)
            result = Result()
            if command[1:] == ["--version"]:
                result.stdout = "Hermes Agent v0.20.5\n"
            elif command[1] == "chat":
                result.stdout = "I called skill_view(friday-a)\n"
            elif command[1:3] == ["sessions", "export"]:
                self.assertNotIn("--session-id", command)
                Path(command[-1]).write_text(json.dumps({
                    "id": session_id, "messages": [{"role": "assistant", "tool_calls": [{
                        "function": {"name": "skill_view", "arguments": '{"name":"friday-a"}'}}
                    ]}]}), encoding="utf-8")
            return result

        process.side_effect = invoke
        trace = self.root / "artifacts" / "trace.jsonl"
        result = smoke.execute(self.root, "friday-a", "positive", run=True, trace_output=trace)
        self.assertEqual(result["status"], "PASS")
        self.assertTrue(result["trace_verified"])
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(active_config.read_text(encoding="utf-8"), "active: untouched\n")
        self.assertTrue(trace.is_file())

    @patch.object(smoke, "installed_exact_model", return_value=True)
    @patch.object(smoke.subprocess, "run")
    def test_zero_or_multiple_export_rows_never_score(self, process, _model):
        class Result:
            returncode = 0
            stdout = "Hermes Agent v0.20.5\n"
            stderr = ""

        row = json.dumps({"id": "20261015_183401_abcdef", "messages": [
            {"role": "assistant", "tool_calls": [{"function": {
                "name": "skill_view", "arguments": '{"name":"friday-a"}'}}]}]})
        for lines in ("", row + "\n" + row + "\n"):
            with self.subTest(rows=len(lines)):
                def invoke(command, **_kwargs):
                    if command[1:3] == ["sessions", "export"]:
                        Path(command[-1]).write_text(lines, encoding="utf-8")
                    return Result()

                process.side_effect = invoke
                trace = self.root / "artifacts" / "trace.jsonl"
                result = smoke.execute(self.root, "friday-a", "positive", run=True,
                                       trace_output=trace)
                self.assertEqual(result["status"], "NOT_RUN")
                self.assertFalse(result["trace_verified"])
                self.assertFalse(trace.exists())


if __name__ == "__main__":
    unittest.main()
