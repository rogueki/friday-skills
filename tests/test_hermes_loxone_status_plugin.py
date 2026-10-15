from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
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

    def test_host_injected_read_uses_only_requested_subset(self):
        calls = []

        class Provider:
            authenticated = True

            def read_snapshot(self, ids, timeout):
                calls.append((ids, timeout))
                stamp = datetime.now(timezone.utc).isoformat()
                return {"version": 1, "observed_at": stamp, "controls": [{
                    "id": ids[0], "room_id": "room-living", "kind": "temperature",
                    "value": 21.0, "unit": "°C", "updated_at": stamp,
                }]}

        ctx = Context()
        register(ctx, transport=Provider(), allowed_control_ids=["ctrl-living-temp", "ctrl-alarm-summary"])
        self.assertEqual(set(ctx.tools), {TOOL_NAME})
        result = json.loads(ctx.tools[TOOL_NAME][2]({"control_ids": ["ctrl-living-temp"]}))
        self.assertEqual(calls, [(('ctrl-living-temp',), 5.0)])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mode"], "read_only")
        self.assertFalse(result["synthetic"])
        self.assertFalse(result["write_effect"])
        self.assertEqual(result["capability"]["name"], "loxone.read")
        self.assertTrue(result["capability"]["authenticated"])
        self.assertFalse(result["capability"]["synthetic"])
        self.assertEqual(result["capability"]["source"], "injected-provider-snapshot")
        self.assertTrue(result["capability"]["checked_at"])
        rejected = json.loads(ctx.tools[TOOL_NAME][2]({"control_ids": ["ctrl-secret"]}))
        self.assertEqual(rejected["error"]["code"], "not_allowlisted")
        self.assertEqual(len(calls), 1)

    def test_host_injection_fails_closed_without_auth_or_valid_snapshot(self):
        class Provider:
            authenticated = False

            def __init__(self, payload=None, error=None, authenticated=True):
                self.payload = payload
                self.error = error
                self.calls = 0
                self.authenticated = authenticated

            def read_snapshot(self, *_args):
                self.calls += 1
                if self.error:
                    raise RuntimeError(self.error)
                return self.payload

        stamp = datetime.now(timezone.utc)
        good = {"version": 1, "observed_at": stamp.isoformat(), "controls": [{
            "id": "ctrl-living-temp", "room_id": "room-living", "kind": "temperature",
            "value": 21.0, "unit": "°C", "updated_at": stamp.isoformat(),
        }]}
        stale = {**good, "observed_at": (stamp - timedelta(minutes=6)).isoformat()}
        for provider, expected in [
            (Provider(good, authenticated=False), "transport_required"),
            (Provider(stale), "stale_status"),
            (Provider({"bad": "shape"}), "invalid_snapshot"),
            (Provider(error="password=secret host=private"), "provider_unavailable"),
        ]:
            ctx = Context()
            register(ctx, transport=provider, allowed_control_ids=["ctrl-living-temp"])
            result = json.loads(ctx.tools[TOOL_NAME][2]({"control_ids": ["ctrl-living-temp"]}))
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["error"], {"code": expected})
            self.assertIsNone(result["capability"])
            self.assertFalse(result["write_effect"])
            self.assertNotIn("secret", json.dumps(result))
            self.assertEqual(provider.calls, 0 if expected == "transport_required" else 1)

    def test_host_configuration_rejects_missing_or_invalid_allowlist(self):
        class Provider:
            authenticated = True

        for kwargs in [
            {"transport": Provider()},
            {"allowed_control_ids": ["ctrl-living-temp"]},
            {"transport": Provider(), "allowed_control_ids": []},
            {"transport": Provider(), "allowed_control_ids": ["ctrl-living-temp", "ctrl-living-temp"]},
            {"transport": Provider(), "allowed_control_ids": ["../secret"]},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(RuntimeError):
                register(Context(), **kwargs)


if __name__ == "__main__":
    unittest.main()
