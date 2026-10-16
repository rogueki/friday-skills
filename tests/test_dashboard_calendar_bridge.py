import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


from plugins.friday_dashboard_calendar import TOOL_NAME, register


class Context:
    def register_tool(self, *, name, toolset, schema, handler):
        self.name, self.toolset, self.schema, self.handler = name, toolset, schema, handler


class Response:
    status = 200

    def __init__(self, url, body):
        self.url, self.body = url, body

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self.url

    def read(self, _limit):
        return json.dumps(self.body).encode()


class Opener:
    def __init__(self, bodies):
        self.bodies, self.requests = iter(bodies), []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return Response(request.full_url, next(self.bodies))


class DashboardCalendarBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        hermes = self.home / ".hermes"
        hermes.mkdir()
        (hermes / "friday-calendar-bridge.json").write_text('{"port": 3101}')
        (hermes / "friday-calendar-bridge.key").write_text("A" * 43 + "=")
        for path in hermes.iterdir():
            path.chmod(0o600)
        self.ctx = Context()
        register(self.ctx)
        self.params = {"start": "2026-10-15T00:00:00Z", "end": "2026-10-16T00:00:00Z"}

    def call(self, bodies):
        opener = Opener(bodies)
        with patch("plugins.friday_dashboard_calendar._setting", return_value=(3101, "A" * 43 + "=")), patch("plugins.friday_dashboard_calendar.build_opener", return_value=opener):
            result = json.loads(self.ctx.handler(self.params))
        return result, opener.requests

    def test_register_and_bound_paged_read_without_cookie_or_provider_secret(self):
        self.assertEqual(self.ctx.name, TOOL_NAME)
        self.assertEqual(set(self.ctx.schema["parameters"]["properties"]), {"start", "end"})
        event = {"title": "Meeting", "source": {"adapterId": "caldav-calendar"}}
        first = {"items": [event], "pageInfo": {"nextCursor": "50"}, "freshness": {"state": "fresh", "asOf": "2026-10-16T10:00:00Z"}}
        second = {"items": [], "pageInfo": {"nextCursor": None}, "freshness": {"state": "fresh", "asOf": "2026-10-16T10:01:00Z"}}
        result, requests = self.call([first, second])
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["source_status"], "unknown")
        self.assertEqual(result["events"], [{"title": "Meeting"}])
        self.assertEqual(result["fetched_at"], "2026-10-16T10:00:00Z")
        self.assertEqual(len(requests), 2)
        for request, timeout in requests:
            self.assertEqual(timeout, 6)
            self.assertTrue(request.full_url.startswith("http://127.0.0.1:3101/api/v1/calendar/events?"))
            self.assertNotIn("Cookie", request.headers)
            self.assertEqual(request.get_method(), "GET")
        self.assertIn("cursor=50", requests[1][0].full_url)

    def test_denies_extra_fields_bad_windows_missing_key_and_stale_data(self):
        self.assertEqual(json.loads(self.ctx.handler({**self.params, "url": "http://other"}))["status"], "blocked")
        self.assertEqual(json.loads(self.ctx.handler({**self.params, "end": "2026-11-20T00:00:00Z"}))["status"], "blocked")
        result, _ = self.call([{"items": [], "pageInfo": {"nextCursor": None}, "freshness": {"state": "stale", "asOf": "2026-10-16T10:00:00Z"}}])
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["fetched_at"])
        invalid, _ = self.call([{"items": [], "pageInfo": {"nextCursor": None}, "freshness": {"state": "fresh", "asOf": "not-a-time"}}])
        self.assertEqual(invalid["status"], "blocked")

    def test_live_source_is_proven_by_adapter_and_urls_are_not_returned(self):
        event = {"id": "cal_123", "title": "Meeting", "start": self.params["start"],
                 "end": self.params["end"], "description": "https://private.example.invalid/token",
                 "source": {"adapterId": "caldav-calendar", "externalId": "private-url"}}
        page = {"items": [event], "pageInfo": {"nextCursor": None}, "freshness": {"state": "fresh", "asOf": "2026-10-16T10:00:00Z"}}
        result, _ = self.call([page])
        self.assertEqual(result["source_status"], "live")
        self.assertNotIn("private.example.invalid", json.dumps(result))
        self.assertNotIn("private-url", json.dumps(result))

    def test_page_limit_fails_closed(self):
        page = {"items": [], "pageInfo": {"nextCursor": "50"}, "freshness": {"state": "fresh", "asOf": "2026-10-16T10:00:00Z"}}
        result, requests = self.call([page, page])
        self.assertEqual(result["error"]["code"], "page_limit")
        self.assertEqual(len(requests), 2)


if __name__ == "__main__":
    unittest.main()
