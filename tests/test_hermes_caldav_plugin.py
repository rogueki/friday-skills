from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from plugins.friday_caldav import SCHEMA, TOOL_NAME, register


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://cal.example.invalid/calendars/friday/"


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class HermesCalDAVTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Context()
        env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT)})
        env.start()
        self.addCleanup(env.stop)
        register(self.ctx)

    def call(self, **overrides):
        params = {"endpoint": ENDPOINT, "account": "friday@example.invalid",
                  "allowed_host": "cal.example.invalid", "start": "2026-10-15T10:00:00Z",
                  "end": "2026-10-16T10:00:00Z", **overrides}
        return json.loads(self.ctx.tools[TOOL_NAME][2](params))

    def test_registers_one_read_tool_and_mock_is_synthetic(self):
        manifest = (ROOT / "plugins/friday_caldav/plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("  - friday_caldav_events\n", manifest)
        self.assertEqual(set(self.ctx.tools), {TOOL_NAME})
        self.assertEqual(self.ctx.tools[TOOL_NAME][:2], ("friday_caldav", SCHEMA))
        result = self.call()
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["synthetic"])
        self.assertFalse(result["write_effect"])

    def test_external_mode_needs_explicit_transport_and_invalid_input_blocks(self):
        self.assertEqual(self.call(mode="read_only")["error"]["code"], "transport_required")
        self.assertEqual(self.call(mode="live")["error"]["code"], "transport_required")
        self.assertEqual(self.call(start="2026-10-15")["error"]["code"], "invalid_time")
        self.assertEqual(self.call(allowed_host="other.invalid")["error"]["code"], "invalid_endpoint")
        self.assertEqual(self.call(extra=True)["error"]["code"], "invalid_request")

    def test_registration_requires_real_support_root(self):
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": ""}):
            with self.assertRaises(RuntimeError):
                register(Context())
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT / "fixtures")}):
            with self.assertRaises(RuntimeError):
                register(Context())


if __name__ == "__main__":
    unittest.main()
