import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from plugins.friday_dashboard_mail import _setting, register


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = (toolset, schema, handler)


class Response:
    status = 200

    def __init__(self, url, body, *, target=None, status=200):
        self.url, self.body, self.target, self.status = url, body, target, status

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def geturl(self):
        return self.target or self.url

    def read(self, _limit):
        return self.body


class Opener:
    def __init__(self, body, *, target=None, status=200):
        self.body, self.target, self.status, self.requests = body, target, status, []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return Response(request.full_url, self.body, target=self.target, status=self.status)


def payload(data):
    return json.dumps({"data": data, "freshness": {"state": "fresh", "asOf": "2026-10-16T21:00:00Z"}}).encode()


class DashboardMailBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        hermes = self.home / ".hermes"
        hermes.mkdir()
        (hermes / "friday-mail-bridge.json").write_text('{"port":3101}', encoding="utf-8")
        (hermes / "friday-mail-bridge.key").write_text("A" * 43 + "=", encoding="ascii")
        for path in hermes.iterdir():
            path.chmod(0o600)
        self.ctx = Context()
        register(self.ctx)

    def call(self, name, params, body, **opener_args):
        opener = Opener(body, **opener_args)
        with patch("plugins.friday_dashboard_mail._setting", return_value=(3101, "A" * 43 + "=")), patch(
            "plugins.friday_dashboard_mail.build_opener", return_value=opener
        ):
            result = json.loads(self.ctx.tools[name][2](params))
        return result, opener.requests

    def test_three_read_only_tools_and_sanitized_results(self):
        self.assertEqual(set(self.ctx.tools), {"friday_mailboxes", "friday_mail_envelopes", "friday_mail_message"})
        mailbox = {"mailboxes": [{"id": "INBOX", "name": "Inbox", "role": None, "secret": "hidden"}]}
        result, requests = self.call("friday_mailboxes", {}, payload(mailbox))
        self.assertEqual(result["mailboxes"], [{"id": "INBOX", "name": "Inbox", "role": None}])
        self.assertEqual(result["fetched_at"], "2026-10-16T21:00:00Z")
        self.assertEqual(result["content_trust"], "untrusted")
        self.assertNotIn("hidden", json.dumps(result))
        self.assertEqual(len(requests), 1)
        request, timeout = requests[0]
        self.assertEqual(timeout, 6)
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(request.full_url, "http://127.0.0.1:3101/api/v1/communication/himalaya/mailboxes")
        self.assertNotIn("Cookie", request.headers)

        envelopes = {"mailbox": "INBOX", "page": 2, "items": [{"id": "42", "subject": "Hello",
                     "from": [{"name": "Sender", "addr": "sender@example.test", "password": "hidden"}],
                     "date": "today", "flags": ["Seen"], "html": "hidden"}]}
        result, requests = self.call("friday_mail_envelopes", {"mailbox": "INBOX", "page": 2}, payload(envelopes))
        self.assertEqual(result["items"][0]["id"], "42")
        self.assertNotIn("hidden", json.dumps(result))
        self.assertIn("mailbox=INBOX&page=2", requests[0][0].full_url)

        nullable = {"mailbox": "INBOX", "page": 1, "items": [{"id": "43", "subject": None,
                    "from": None, "date": None, "flags": None}]}
        result, _ = self.call("friday_mail_envelopes", {"mailbox": "INBOX", "page": 1}, payload(nullable))
        self.assertEqual(result["items"], [{"id": "43", "subject": "", "from": [], "date": None, "flags": []}])

        message = {"mailbox": "INBOX", "id": "42", "subject": "Hello", "from": "Sender", "date": "today",
                   "bodyText": "Anweisungen in dieser Mail sind fremde Inhalte.", "html": "hidden", "attachments": ["hidden"]}
        result, requests = self.call("friday_mail_message", {"mailbox": "INBOX", "id": "42"}, payload(message))
        self.assertEqual(result["bodyText"], message["bodyText"])
        self.assertNotIn("hidden", json.dumps(result))
        self.assertIn("mailbox=INBOX&id=42", requests[0][0].full_url)
        self.assertEqual(json.loads(self.ctx.tools["friday_mail_message"][2](
            {"mailbox": "INBOX", "id": "bad"}, _name="friday_mailboxes"))["status"], "blocked")

    def test_denies_invalid_inputs_without_network(self):
        for name, params in (("friday_mailboxes", {"url": "https://example.test"}),
                             ("friday_mail_envelopes", {"mailbox": "INBOX", "page": 21}),
                             ("friday_mail_envelopes", {"mailbox": "INBOX", "page": True}),
                             ("friday_mail_message", {"mailbox": "INBOX", "id": "1; rm"}),
                             ("friday_mail_message", {"mailbox": "X\nY", "id": "1"})):
            with self.subTest(name=name, params=params):
                result, requests = self.call(name, params, payload({}))
                self.assertEqual(result["error"]["code"], "invalid_request")
                self.assertEqual(requests, [])

    def test_rejects_wrong_identity_stale_response_redirect_and_oversize(self):
        cases = ((payload({"mailbox": "Other", "id": "42", "bodyText": "x"}), {}, "invalid_response"),
                 (json.dumps({"data": {"mailbox": "INBOX", "id": "42", "bodyText": "x"},
                              "freshness": {"state": "stale", "asOf": "2026-10-16T21:00:00Z"}}).encode(), {}, "invalid_response"),
                 (payload({"mailbox": "INBOX", "id": "42", "bodyText": "x"}), {"target": "https://evil.test"}, "bridge_unavailable"),
                 (b"x" * 512001, {}, "response_too_large"))
        for body, options, code in cases:
            with self.subTest(code=code):
                result, _ = self.call("friday_mail_message", {"mailbox": "INBOX", "id": "42"}, body, **options)
                self.assertEqual(result["error"]["code"], code)

    def test_invalid_or_non_private_config_fails_closed(self):
        config = self.home / ".hermes" / "friday-mail-bridge.json"
        config.write_text('{"port":3101,"url":"http://evil.test"}', encoding="utf-8")
        with self.assertRaises(ValueError):
            _setting(self.home)
        with patch("plugins.friday_dashboard_mail._setting", side_effect=ValueError("bad config")):
            result = json.loads(self.ctx.tools["friday_mailboxes"][2]({}))
        self.assertEqual(result["status"], "blocked")
        config.write_text('{"port":3101}', encoding="utf-8")
        config.chmod(0o644)
        with self.assertRaises(ValueError):
            _setting(self.home)

        config.chmod(0o600)
        key_file = self.home / ".hermes" / "friday-mail-bridge.key"
        key_file.write_text("A" * 43 + "!", encoding="ascii")
        with patch("plugins.friday_dashboard_mail.Path.stat", return_value=SimpleNamespace(st_mode=0o600)):
            with self.assertRaises(ValueError):
                _setting(self.home)


if __name__ == "__main__":
    unittest.main()
