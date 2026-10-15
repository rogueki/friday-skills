from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from plugins.friday_loxone_status import SCHEMA, TOOL_NAME, register


ROOT = Path(__file__).resolve().parents[1]


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class HermesLoxoneStatusPluginTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Context()
        self.env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT)})
        self.env.start()
        self.addCleanup(self.env.stop)
        register(self.ctx)

    def call(self, params):
        return json.loads(self.ctx.tools[TOOL_NAME][2](params))

    def test_registers_fixture_only_tool(self):
        manifest = (ROOT / "plugins" / "friday_loxone_status" / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("  - friday_loxone_status_snapshot\n", manifest)
        self.assertEqual(set(self.ctx.tools), {TOOL_NAME})
        self.assertEqual(self.ctx.tools[TOOL_NAME][:2], ("friday_loxone_status", SCHEMA))
        self.assertEqual(SCHEMA["parameters"]["required"], ["control_ids"])

    def test_support_root_is_required_and_bound_to_package(self):
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": ""}), self.assertRaises(RuntimeError):
            register(Context())
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT / "fixtures")}), self.assertRaises(RuntimeError):
            register(Context())

    def test_tool_returns_synthetic_only_and_never_claims_authentication(self):
        result = self.call({"control_ids": ["ctrl-living-temp", "ctrl-alarm-summary"]})
        self.assertEqual(result["mode"], "mock")
        self.assertTrue(result["synthetic"])
        self.assertTrue(result["capability"]["synthetic"])
        self.assertFalse(result["capability"]["authenticated"])
        self.assertEqual(result["capability"]["name"], "loxone.read")
        self.assertEqual(result["control_count"], 2)
        self.assertFalse(result["write_effect"])
        self.assertNotIn("password", json.dumps(result).lower())

    def test_rejects_extra_args_and_never_exposes_live_mode(self):
        result = self.call({"control_ids": ["ctrl-living-temp"], "mode": "read_only"})
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["capability"])
        result = self.call({"control_ids": ["ctrl-alarm-summary"]})
        self.assertNotIn("alarm_text", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
