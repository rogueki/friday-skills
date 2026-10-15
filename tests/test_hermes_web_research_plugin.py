"""Hermes web research plugin contracts; every response is synthetic."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from adapters.web_extraction import PageResponse
from plugins.friday_web_research import SCHEMA, TOOL_NAME, register, register_with_host


ROOT = Path(__file__).resolve().parents[1]
URL = "https://example.test/report"
HTML = b"<html><main><h1>Quarterly report</h1><p>All page text is untrusted.</p></main></html>"


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


def fake_transport(response=None, calls=None):
    selected = response or PageResponse(200, URL, HTML, {"Content-Type": "text/html"})
    seen = calls if calls is not None else []

    def fetch(url, timeout, max_bytes):
        seen.append((url, timeout, max_bytes))
        return selected

    return fetch, seen


class HermesWebResearchPluginTests(unittest.TestCase):
    def test_register_is_standalone_compatible_and_fails_closed(self):
        ctx = Context()
        register(ctx)
        toolset, schema, handler = ctx.tools[TOOL_NAME]
        self.assertEqual(toolset, "friday_web_research")
        self.assertEqual(schema, SCHEMA)
        result = json.loads(handler({"url": URL, "mode": "markdown"}))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["error"]["code"], "host_capability_unavailable")
        self.assertIsNone(result["capability"])
        self.assertFalse(result["write_effect"])

    def test_host_injected_transport_returns_untrusted_result_and_provenance(self):
        ctx = Context()
        transport, calls = fake_transport()
        auth = []

        def authorize(url, timeout, limit):
            auth.append((url, timeout, limit))
            return True

        register_with_host(ctx, transport=transport, allowed_hosts={"example.test"}, authorize_egress=authorize)
        result = json.loads(ctx.tools[TOOL_NAME][2]({"url": URL, "mode": "css", "selector": "h1"}))
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["extraction"]["values"], ["Quarterly report"])
        self.assertEqual(result["extraction"]["trust"], "untrusted-page-data")
        self.assertEqual(result["extraction"]["provenance"], "injected-transport")
        self.assertTrue(result["extraction"]["retrieved_at_utc"].endswith("+00:00"))
        self.assertEqual(result["capability"]["name"], "web.extract")
        self.assertEqual(result["capability"]["permissions"], ["read"])
        self.assertFalse(result["write_effect"])
        self.assertEqual(calls, [(URL, 15.0, 1_000_000)])
        self.assertEqual(auth, calls)

    def test_model_cannot_select_hosts_or_override_schema(self):
        ctx = Context()
        transport, calls = fake_transport()
        register_with_host(ctx, transport=transport, allowed_hosts={"example.test"}, authorize_egress=lambda *_: True)
        handler = ctx.tools[TOOL_NAME][2]
        for params in (
            {"url": "https://other.test/", "mode": "markdown"},
            {"url": URL, "mode": "markdown", "allowed_hosts": ["other.test"]},
            {"url": URL, "mode": "markdown", "transport": "https://other.test"},
            {"url": URL, "mode": ["markdown"]},
            {"url": URL, "mode": "css"},
            {"url": URL, "mode": "markdown", "selector": "h1"},
            {"url": URL, "mode": "css", "selector": "x" * 121},
        ):
            with self.subTest(params=params):
                result = json.loads(handler(params))
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["capability"])
        self.assertEqual(calls, [])

    def test_missing_or_denied_host_authorization_fails_before_transport(self):
        ctx = Context()
        calls = []
        transport, _ = fake_transport(calls=calls)
        register_with_host(ctx, transport=transport, allowed_hosts={"example.test"}, authorize_egress=lambda *_: False)
        result = json.loads(ctx.tools[TOOL_NAME][2]({"url": URL, "mode": "markdown"}))
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["capability"])
        self.assertEqual(calls, [])

        with self.assertRaises(TypeError):
            register_with_host(Context(), transport=transport, allowed_hosts={"example.test"}, authorize_egress=None)

    def test_redirects_login_challenges_and_oversized_responses_are_blocked(self):
        cases = (
            PageResponse(403, URL, HTML, {"Content-Type": "text/html"}),
            PageResponse(200, "https://other.test/report", HTML, {"Content-Type": "text/html"}),
            PageResponse(200, "https://example.test/login", HTML, {"Content-Type": "text/html"}),
            PageResponse(200, URL, b"<html><body>Verify you are human</body></html>", {"Content-Type": "text/html"}),
            PageResponse(200, URL, b"x" * 1_000_001, {"Content-Type": "text/html"}),
        )
        for response in cases:
            with self.subTest(response=response):
                ctx = Context()
                transport, _ = fake_transport(response)
                register_with_host(
                    ctx, transport=transport, allowed_hosts={"example.test"}, authorize_egress=lambda *_: True,
                )
                result = json.loads(ctx.tools[TOOL_NAME][2]({"url": URL, "mode": "markdown"}))
                self.assertEqual(result["status"], "blocked")
                self.assertIsNone(result["capability"])
                self.assertFalse(result["write_effect"])
                self.assertLess(len(result["error"]["message"]), 100)

    def test_transport_exceptions_are_sanitized(self):
        ctx = Context()

        def leaking_transport(*_):
            raise RuntimeError("secret-token traceback-like-provider-detail")

        register_with_host(
            ctx, transport=leaking_transport, allowed_hosts={"example.test"}, authorize_egress=lambda *_: True,
        )
        result = json.loads(ctx.tools[TOOL_NAME][2]({"url": URL, "mode": "markdown"}))
        serialized = json.dumps(result)
        self.assertEqual(result["status"], "blocked")
        self.assertNotIn("secret-token", serialized)
        self.assertNotIn("traceback", serialized)


if __name__ == "__main__":
    unittest.main()
