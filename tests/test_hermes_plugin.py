"""Opt-in Hermes plugin contract tests, with no active-profile changes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from plugins.friday_local import FIXTURES, SCHEMAS, register


ROOT = Path(__file__).resolve().parents[1]


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class HermesPluginTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.ctx = Context()
        register(self.ctx)

    def call(self, tool_name, **params):
        return json.loads(self.ctx.tools[tool_name][2](params))

    def test_registration_matches_manifest_and_schemas(self):
        manifest = json.loads((ROOT / "plugins" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(set(self.ctx.tools), set(manifest["provides_tools"]))
        self.assertEqual(set(self.ctx.tools), set(SCHEMAS))
        self.assertTrue(all(toolset == "friday_local" for toolset, _, _ in self.ctx.tools.values()))

    def test_dangerous_action_cannot_be_approved_or_executed(self):
        result = self.call("friday_policy_preflight", action="payment", target="bank", payload={"amount": 100})
        self.assertEqual(result["decision"], "deny")
        self.assertFalse(result["executed"])
        self.assertFalse(result["publishable"])
        live = self.call("friday_policy_preflight", action="payment", target="bank", payload={}, mode="live")
        self.assertEqual(live["decision"], "deny")
        observed = self.call("friday_policy_preflight", action="observe", target="synthetic-weather", payload={})
        self.assertEqual(observed["decision"], "allow_local")
        self.assertFalse(observed["executed"])

    def test_fixture_is_strictly_allowlisted(self):
        good = self.call("friday_fixture_read", kind="weather", name="current")
        self.assertTrue(good["synthetic"])
        self.assertFalse(good["external_effect"])
        for kind, name in (("..", "secrets"), ("weather", "../../.env"), ("unknown", "current")):
            denied = self.call("friday_fixture_read", kind=kind, name=name)
            self.assertEqual(denied["error"], "fixture not allowlisted")
        self.assertEqual(self.call("friday_fixture_read", kind=["weather"], name="current")["error"],
                         "fixture not allowlisted")
        self.assertEqual(len(FIXTURES), 10)

    def test_proposal_and_activity_remain_local(self):
        proposal = self.call("friday_mock_propose", action="send_message", target="someone", payload="hello")
        self.assertFalse(proposal["proposal"]["executed"])
        self.assertTrue(proposal["requires_approval"])
        self.assertFalse(proposal["publishable"])
        activity = self.call("friday_activity_record", skill="friday-weather", status="working",
                             message="Synthetic forecast", progress=0.2)
        self.assertFalse(activity["delivered"])
        self.assertFalse(activity["intended_mapping"]["publishable"])

    def test_wrong_package_root_refused(self):
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT / "plugins")}, clear=False):
            with self.assertRaises(RuntimeError):
                register(Context())


if __name__ == "__main__":
    unittest.main()
