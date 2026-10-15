"""Standalone GMX Hermes plugin registration and fail-closed tool checks."""

from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from adapters import gmx_mail
from plugins.friday_gmx_mail import SCHEMA, TOOL_NAME, register


ROOT = Path(__file__).resolve().parents[1]


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class HermesGMXMailPluginTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Context()
        env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT), "FRIDAY_GMX_ALLOW_READ": ""}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        register(self.ctx)

    def call(self, **params):
        return json.loads(self.ctx.tools[TOOL_NAME][2](params))

    def test_manifest_and_default_mock(self):
        manifest = (ROOT / "plugins" / "friday_gmx_mail" / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("  - friday_gmx_read_uid\n", manifest)
        self.assertEqual(set(self.ctx.tools), {TOOL_NAME})
        self.assertEqual(self.ctx.tools[TOOL_NAME][:2], ("friday_gmx_mail", SCHEMA))
        result = self.call(mailbox="INBOX", uid="42")
        self.assertEqual(result["mode"], "mock")
        self.assertIn("synthetic", result["source"])
        self.assertFalse(result["write_effect"])

    def test_read_only_needs_explicit_operator_opt_in(self):
        with patch.object(gmx_mail, "read_message") as reader:
            result = self.call(mailbox="INBOX", uid="42", mode="read_only")
        self.assertEqual(result["error"], "read_not_enabled")
        reader.assert_not_called()

    def test_invalid_input_and_send_are_blocked(self):
        self.assertEqual(self.call(mailbox="INBOX", uid="42", mode="live")["status"], "blocked")
        self.assertEqual(self.call(mailbox="INBOX", uid="42", send=True)["status"], "blocked")
        self.assertEqual(self.call(mailbox="INBOX", uid="1:2")["error"], "invalid_uid")

    def test_registration_rejects_other_support_root(self):
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT / "fixtures")}):
            with self.assertRaises(RuntimeError):
                register(Context())


if __name__ == "__main__":
    unittest.main()
