from __future__ import annotations

import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from adapters.caldav_calendar import Response
from plugins.friday_caldav import (
    MOCK_ACCOUNT, SCHEMA, TOOL_NAME,
    HostCalDAVReadConfig, register,
)


ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "https://cal.example.invalid/calendars/friday/"
ACCOUNT = "operator@example.invalid"
HOST = "cal.example.invalid"
START = "2026-10-15T10:00:00Z"
END = "2026-10-16T10:00:00Z"


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class FakeTransport:
    authenticated = True

    def __init__(self, body: bytes, status: int = 207, *, lose_auth_on_call: bool = False):
        self.body = body
        self.status = status
        self.lose_auth_on_call = lose_auth_on_call
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        if self.lose_auth_on_call:
            self.authenticated = False
        return Response(self.status, {}, self.body)


class BrokenAuthTransport:
    calls = 0

    @property
    def authenticated(self):
        raise RuntimeError("credential backend detail")

    def __call__(self, request):
        self.calls += 1
        return Response(207, {}, b"")


class HermesCalDAVTests(unittest.TestCase):
    def setUp(self):
        self.ctx = Context()
        env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT)})
        env.start()
        self.addCleanup(env.stop)
        register(self.ctx)

    def call(self, *, handler=None, **overrides):
        params = {"start": START, "end": END, **overrides}
        return json.loads((handler or self.ctx.tools[TOOL_NAME][2])(params))

    def make_host_context(self, transport, *, authorized=True):
        ctx = Context()
        config = HostCalDAVReadConfig(
            endpoint=ENDPOINT, account=ACCOUNT, allowed_host=HOST, transport=transport,
            authorized=authorized,
        )
        register(ctx, host_read=config)
        return ctx

    def test_registers_only_time_window_read_tool_and_mock_is_synthetic(self):
        manifest = (ROOT / "plugins/friday_caldav/plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("  - friday_caldav_events\n", manifest)
        self.assertEqual(set(self.ctx.tools), {TOOL_NAME})
        self.assertEqual(self.ctx.tools[TOOL_NAME][:2], ("friday_caldav", SCHEMA))
        self.assertEqual(SCHEMA["parameters"]["properties"].keys(), {"start", "end"})
        result = self.call()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mode"], "mock")
        self.assertEqual(result["account"], MOCK_ACCOUNT)
        self.assertEqual(result["source"], "synthetic:fixtures/calendar/adapter_multistatus.xml")
        self.assertTrue(result["synthetic"])
        self.assertFalse(result["write_effect"])

    def test_host_authorized_read_uses_fixed_binding_and_returns_fresh_read_capability(self):
        fixture = (ROOT / "fixtures/calendar/adapter_multistatus.xml").read_bytes()
        transport = FakeTransport(fixture)
        ctx = self.make_host_context(transport)
        result = self.call(handler=ctx.tools[TOOL_NAME][2])

        self.assertEqual(len(ctx.tools), 1)
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["mode"], "read_only")
        self.assertFalse(result["synthetic"])
        self.assertFalse(result["write_effect"])
        self.assertEqual(result["capability"]["name"], "caldav.read")
        self.assertEqual(result["capability"]["permissions"], ["read"])
        self.assertFalse(result["capability"]["synthetic"])
        self.assertEqual(len(transport.requests), 1)
        self.assertEqual(transport.requests[0].method, "REPORT")
        self.assertEqual(transport.requests[0].url, ENDPOINT)

    def test_model_cannot_supply_or_change_account_endpoint_host_or_mode(self):
        transport = FakeTransport(b"unused")
        ctx = self.make_host_context(transport)
        handler = ctx.tools[TOOL_NAME][2]
        for field, value in (("endpoint", "https://evil.invalid/"), ("account", "other@example.invalid"),
                             ("allowed_host", "evil.invalid"), ("mode", "live")):
            with self.subTest(field=field):
                result = self.call(handler=handler, **{field: value})
                self.assertEqual(result["status"], "blocked")
                self.assertEqual(result["error"]["code"], "invalid_request")
        self.assertEqual(transport.requests, [])

    def test_missing_host_authorization_or_transport_auth_fails_closed(self):
        fixture = (ROOT / "fixtures/calendar/adapter_multistatus.xml").read_bytes()
        unauthenticated = FakeTransport(fixture)
        unauthenticated.authenticated = False
        for authorized, transport, code in (
            (False, FakeTransport(fixture), "host_authorization_required"),
            (True, unauthenticated, "authenticated_transport_required"),
            (True, None, "authenticated_transport_required"),
        ):
            ctx = self.make_host_context(transport, authorized=authorized)
            result = self.call(handler=ctx.tools[TOOL_NAME][2])
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["error"]["code"], code)
            self.assertIsNone(result["capability"])
            self.assertFalse(result["write_effect"])
        self.assertEqual(len(ctx.tools), 1)

    def test_invalid_or_overlong_window_and_provider_failure_do_not_publish_capability(self):
        fixture = (ROOT / "fixtures/calendar/adapter_multistatus.xml").read_bytes()
        ctx = self.make_host_context(FakeTransport(fixture))
        handler = ctx.tools[TOOL_NAME][2]
        self.assertEqual(self.call(handler=handler, start="2026-10-15")["error"]["code"], "invalid_time")
        long_end = "2026-11-16T10:00:00Z"
        overlong = self.call(handler=handler, end=long_end)
        self.assertEqual(overlong["error"]["code"], "invalid_window")
        transport = FakeTransport(b"provider response with secret token", status=500)
        failed_ctx = self.make_host_context(transport)
        failure = self.call(handler=failed_ctx.tools[TOOL_NAME][2])
        self.assertEqual(failure["status"], "blocked")
        self.assertEqual(failure["error"]["code"], "bad_status")
        self.assertNotIn("secret token", json.dumps(failure))
        self.assertIsNone(failure["capability"])
        self.assertFalse(failure["write_effect"])

    def test_transport_losing_authentication_during_report_returns_no_events_or_capability(self):
        fixture = (ROOT / "fixtures/calendar/adapter_multistatus.xml").read_bytes()
        transport = FakeTransport(fixture, lose_auth_on_call=True)
        ctx = self.make_host_context(transport)

        result = self.call(handler=ctx.tools[TOOL_NAME][2])

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"]["code"], "authenticated_transport_required")
        self.assertIsNone(result["events"])
        self.assertIsNone(result["capability"])
        self.assertFalse(result["write_effect"])
        self.assertEqual(len(transport.requests), 1)

    def test_transport_authentication_property_error_fails_before_provider_call(self):
        transport = BrokenAuthTransport()
        ctx = self.make_host_context(transport)

        result = self.call(handler=ctx.tools[TOOL_NAME][2])

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"]["code"], "authenticated_transport_required")
        self.assertIsNone(result["events"])
        self.assertIsNone(result["capability"])
        self.assertEqual(transport.calls, 0)

    def test_registration_requires_real_support_root(self):
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": ""}):
            with self.assertRaises(RuntimeError):
                register(Context())
        with patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT / "fixtures")}):
            with self.assertRaises(RuntimeError):
                register(Context())


if __name__ == "__main__":
    unittest.main()
