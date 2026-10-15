"""Offline batch tests: no Ollama or Hermes process is started."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import local_hermes_routing_batch as batch


class LocalHermesRoutingBatchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / "registry").mkdir()
        skill = self.root / "skills" / "friday-a"
        (skill / "tests").mkdir(parents=True)
        (skill / "SKILL.md").write_text("---\nname: friday-a\n---\n", encoding="utf-8")
        (self.root / "registry" / "skills.json").write_text(json.dumps({"skills": [{
            "name": "friday-a", "trigger": "A", "path": "skills/friday-a/SKILL.md"}]}),
            encoding="utf-8")
        (skill / "tests" / "cases.json").write_text(json.dumps({"skill": "friday-a", "cases": [
            {"id": cid, "request": "SECRET REQUEST", "expected": expected}
            for cid, expected in [("positive", "select"), ("negative", "reject"),
                                  ("collision", "reject"), ("ambiguity", "defer")]]}),
            encoding="utf-8")
        self.report = self.root / "artifacts" / "batch.json"
        revision = patch.object(batch, "_revision", return_value="a" * 40)
        revision.start()
        self.addCleanup(revision.stop)

    def _execute(self, root, skill, case_id, *, run, trace_output):
        self.assertTrue(run)
        self.assertEqual(root, self.root)
        session = {"id": "20261015_183401_abcdef", "messages": [{"role": "assistant",
                   "tool_calls": [{"function": {"name": "skill_view", "arguments":
                                                  json.dumps({"name": skill})}}]}]}
        trace_output.parent.mkdir(parents=True, exist_ok=True)
        trace_output.write_text(json.dumps(session) + "\n", encoding="utf-8")
        raw = trace_output.read_bytes()
        case, case_hash = batch.smoke.select_case(root, skill, case_id)
        actual = "select"
        status = "PARTIAL" if case["expected"] == "defer" else (
            "PASS" if actual == case["expected"] else "FAIL")
        return {"case_set_sha256": case_hash, "status": status, "trace_verified": True,
                "trace_sha256": hashlib.sha256(raw).hexdigest(), "session_id": session["id"],
                "observed_skill_views": [skill], "observed_decision": actual}

    @patch.object(batch.smoke, "installed_exact_model")
    @patch.object(batch.smoke, "execute")
    def test_dry_run_zero_model_calls_and_all_cases_not_run(self, execute, model):
        report = batch.evaluate(self.root, run=False, output=self.report)
        self.assertEqual(report["case_total"], 4)
        self.assertEqual(report["counts"]["NOT_RUN"], 4)
        self.assertEqual(report["attempted_total"], 0)
        self.assertEqual(report["attempt_reservations_total"], 0)
        self.assertNotIn("SECRET REQUEST", self.report.read_text(encoding="utf-8"))
        model.assert_not_called()
        execute.assert_not_called()

    @patch.object(batch.smoke, "installed_exact_model", return_value=True)
    @patch.object(batch.smoke, "execute")
    def test_cap_resume_skips_verified_and_failed_case_is_counted(self, execute, _model):
        execute.side_effect = self._execute
        first = batch.evaluate(self.root, run=True, max_cases=1, output=self.report)
        self.assertEqual((first["attempted_total"], first["counts"]["PASS"]), (1, 1))
        resumed = batch.evaluate(self.root, run=True, max_cases=1, output=self.report, resume=True)
        self.assertEqual(execute.call_count, 2)
        self.assertEqual(resumed["counts"], {"PASS": 1, "FAIL": 1, "PARTIAL": 0, "NOT_RUN": 2})
        self.assertEqual(resumed["attempted_total"], 2)
        self.assertEqual(resumed["attempt_reservations_total"], 2)
        self.assertEqual(resumed["cases"][1]["case_id"], "negative")
        self.assertNotIn("SECRET REQUEST", self.report.read_text(encoding="utf-8"))

    @patch.object(batch.smoke, "installed_exact_model", return_value=True)
    @patch.object(batch.smoke, "execute")
    def test_resume_rejects_revision_or_case_set_change(self, execute, _model):
        execute.side_effect = self._execute
        batch.evaluate(self.root, run=True, max_cases=1, output=self.report)
        with patch.object(batch, "_revision", return_value="b" * 40):
            with self.assertRaisesRegex(ValueError, "git_revision mismatch"):
                batch.evaluate(self.root, run=True, max_cases=1, output=self.report, resume=True)
        case_file = self.root / "skills" / "friday-a" / "tests" / "cases.json"
        data = json.loads(case_file.read_text(encoding="utf-8"))
        data["cases"][0]["request"] = "CHANGED"
        case_file.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "case_set_sha256 mismatch"):
            batch.evaluate(self.root, run=True, max_cases=1, output=self.report, resume=True)
        self.assertEqual(execute.call_count, 1)

    @patch.object(batch.smoke, "installed_exact_model", return_value=True)
    @patch.object(batch.smoke, "execute")
    def test_resume_rejects_corrupt_trace_or_report(self, execute, _model):
        execute.side_effect = self._execute
        batch.evaluate(self.root, run=True, max_cases=1, output=self.report)
        trace = batch._trace_path(self.root, self.report,
                                  {"skill": "friday-a", "case_id": "positive"})
        trace.write_text("tampered\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "trace hash mismatch"):
            batch.evaluate(self.root, run=True, max_cases=1, output=self.report, resume=True)
        self.assertEqual(execute.call_count, 1)

    @patch.object(batch.smoke, "installed_exact_model", return_value=True)
    @patch.object(batch.smoke, "execute")
    def test_unverified_attempt_is_not_repeated_implicitly(self, execute, _model):
        execute.return_value = {"case_set_sha256": batch._new_report(self.root)[0]["case_set_sha256"],
                                "status": "NOT_RUN", "trace_verified": False}
        report = batch.evaluate(self.root, run=True, max_cases=1, output=self.report)
        self.assertEqual(report["counts"]["NOT_RUN"], 4)
        with self.assertRaisesRegex(ValueError, "retry-unverified"):
            batch.evaluate(self.root, run=True, max_cases=1, output=self.report, resume=True)
        self.assertEqual(execute.call_count, 1)

    @patch.object(batch.smoke, "installed_exact_model", return_value=True)
    @patch.object(batch.smoke, "execute")
    def test_existing_report_and_concurrent_lock_prevent_duplicate_attempt(self, execute, _model):
        self.report.parent.mkdir(parents=True)
        self.report.write_text("old", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "report exists"):
            batch.evaluate(self.root, run=True, max_cases=1, output=self.report)
        self.report.unlink()
        lock = self.report.with_name(self.report.name + ".lock")
        lock.write_text("other run", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            batch.evaluate(self.root, run=True, max_cases=1, output=self.report)
        self.assertTrue(lock.is_file())
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
