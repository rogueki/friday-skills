from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from adapters.content_studio_control import Response, StudioHostBinding
from plugins.friday_content_studio import SCHEMAS, register


ROOT = Path(__file__).resolve().parents[1]


class Context:
    def __init__(self):
        self.tools = {}

    def register_tool(self, *, name, toolset, schema, handler):
        self.tools[name] = handler


class FakeControlApi:
    def __init__(self):
        self.requests = []
        self.tasks = {}
        self.plan_state = {"revision": 0, "plan": None, "updatedAt": None}

    def __call__(self, method, url, headers, body, timeout):
        self.requests.append((method, url, headers, body, timeout))
        if headers.get("Cookie") != "friday_session=session-test" or (method in {"POST", "PUT"} and headers.get("X-CSRF-Token") != "csrf-test"):
            return Response(403, {}, b"")
        if url.endswith("/content-studio/plan") and method == "GET":
            return Response(200, {"content-type": "application/json"}, json.dumps({"contractVersion": "2.0.0", "data": self.plan_state}).encode())
        if url.endswith("/content-studio/plan") and method == "PUT":
            if headers.get("If-Match") != str(self.plan_state["revision"]):
                return Response(409, {}, b"")
            plan = json.loads(body)
            self.plan_state = {"revision": self.plan_state["revision"] + 1, "plan": plan, "updatedAt": "2026-10-16T12:00:00.000Z"}
            return Response(200, {"content-type": "application/json"}, json.dumps({"contractVersion": "2.0.0", "data": self.plan_state}).encode())
        if method == "POST" and url.endswith("/kie/tasks"):
            payload = json.loads(body)
            if payload.get("confirmed") is not True:
                return Response(422, {}, b"")
            task_id = "task-test-1"
            self.tasks[task_id] = payload["kind"]
            return Response(202, {"content-type": "application/json"}, json.dumps({"contractVersion": "1.0.0", "data": {"taskId": task_id, "kind": payload["kind"], "state": "waiting", "resultUrls": [], "creditsConsumed": None}}).encode())
        if method == "GET" and "/kie/tasks/" in url:
            task_id = url.rsplit("/", 1)[-1]
            if task_id not in self.tasks:
                return Response(404, {}, b"")
            return Response(200, {"content-type": "application/json"}, json.dumps({"contractVersion": "1.0.0", "data": {"taskId": task_id, "kind": self.tasks[task_id], "state": "success", "resultUrls": ["https://example.invalid/result.png"], "creditsConsumed": 2}}).encode())
        if method == "POST" and url.endswith("/elevenlabs/speech"):
            return Response(200, {"Content-Type": "audio/mpeg"}, b"ID3test")
        return Response(404, {}, b"")


class ContentStudioBridgeTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"FRIDAY_SKILLS_ROOT": str(ROOT)})
        self.env.start()
        self.addCleanup(self.env.stop)
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.transport = FakeControlApi()
        self.approvals = []

    def plugin(self, *, approved=True, authorized=True, output=True):
        ctx = Context()
        def approve(action, payload):
            self.approvals.append((action, payload))
            return approved
        host = StudioHostBinding("http://127.0.0.1:8384", "session-test", "csrf-test", approve, self.transport, authorized)
        register(ctx, host=host, output_dir=Path(self.temp.name) if output else None)
        return ctx

    @staticmethod
    def call(ctx, name, params):
        return json.loads(ctx.tools[name](params))

    def test_plugin_to_mock_control_api_media_status_and_speech(self):
        ctx = self.plugin()
        self.assertEqual(set(ctx.tools), set(SCHEMAS))
        media = self.call(ctx, "friday_studio_create_media", {"kind": "image", "prompt": "A studio portrait", "aspect_ratio": "1:1", "idempotency_key": "intent-media-123"})
        self.assertEqual(media["status"], "accepted")
        self.assertEqual(media["task"]["taskId"], "task-test-1")
        status = self.call(ctx, "friday_studio_media_status", {"task_id": "task-test-1"})
        self.assertEqual(status["task"]["state"], "success")
        speech = self.call(ctx, "friday_studio_create_speech", {"text": "Hallo F.R.I.D.A.Y.", "voice_id": "voice123", "idempotency_key": "intent-speech-123"})
        self.assertEqual(speech["status"], "completed")
        self.assertEqual(Path(speech["path"]).read_bytes(), b"ID3test")
        self.assertEqual([item[0] for item in self.approvals], ["kie.create", "elevenlabs.speech"])
        self.assertEqual(len(self.transport.requests), 3)
        for _, url, headers, _, _ in self.transport.requests:
            self.assertTrue(url.startswith("http://127.0.0.1:8384/api/v1/content-studio/"))
            self.assertNotIn("session-test", str(media) + str(status) + str(speech))
            self.assertNotIn("csrf-test", str(media) + str(status) + str(speech))
            self.assertEqual(headers["Cookie"], "friday_session=session-test")

    def test_plan_read_write_uses_csrf_and_exact_revision(self):
        ctx = self.plugin()
        initial = self.call(ctx, "friday_studio_read_plan", {})
        self.assertEqual(initial, {"status": "completed", "state": {"revision": 0, "plan": None, "updatedAt": None}, "write_effect": False})
        plan = {"version": 1, "content": [], "postings": []}
        saved = self.call(ctx, "friday_studio_write_plan", {"plan": plan, "expected_revision": initial["state"]["revision"]})
        self.assertEqual(saved["state"]["revision"], 1)
        self.assertEqual(saved["state"]["plan"], plan)
        self.assertTrue(saved["write_effect"])
        self.assertEqual(self.transport.requests[0][0], "GET")
        method, _, headers, body, _ = self.transport.requests[1]
        self.assertEqual(method, "PUT")
        self.assertEqual(headers["Cookie"], "friday_session=session-test")
        self.assertEqual(headers["X-CSRF-Token"], "csrf-test")
        self.assertEqual(headers["If-Match"], "0")
        self.assertEqual(json.loads(body), plan)
        self.assertNotIn("session-test", str(saved))
        self.assertNotIn("csrf-test", str(saved))
        self.assertEqual(self.approvals, [])

    def test_plan_conflict_has_no_automatic_retry_or_overwrite(self):
        ctx = self.plugin()
        plan = {"version": 1, "content": [], "postings": []}
        self.call(ctx, "friday_studio_write_plan", {"plan": plan, "expected_revision": 0})
        stale = self.call(ctx, "friday_studio_write_plan", {"plan": plan, "expected_revision": 0})
        self.assertEqual(stale["error"]["code"], "revision_conflict")
        self.assertFalse(stale["write_effect"])
        self.assertEqual(len(self.transport.requests), 2)
        self.assertEqual(self.transport.plan_state["revision"], 1)

    def test_plan_failures_reject_invalid_inputs_and_api_auth(self):
        ctx = self.plugin()
        plan = {"version": 1, "content": [], "postings": []}
        for params, code in (({"plan": plan}, "invalid_request"), ({"plan": plan, "expected_revision": True}, "invalid_revision"), ({"plan": {"version": 2, "content": [], "postings": []}, "expected_revision": 0}, "invalid_plan"), ({"plan": plan, "expected_revision": 0, "origin": "https://evil.invalid"}, "invalid_request")):
            with self.subTest(code=code):
                self.assertEqual(self.call(ctx, "friday_studio_write_plan", params)["error"]["code"], code)
        self.assertEqual(self.transport.requests, [])
        self.assertEqual(self.call(ctx, "friday_studio_read_plan", {"session": "steal"})["error"]["code"], "invalid_request")
        denied = self.plugin(authorized=False)
        self.assertEqual(self.call(denied, "friday_studio_read_plan", {})["error"]["code"], "host_authorization_required")
        self.assertEqual(self.call(denied, "friday_studio_write_plan", {"plan": plan, "expected_revision": 0})["error"]["code"], "host_authorization_required")
        self.assertEqual(self.transport.requests, [])

    def test_plan_csrf_rejection_and_unknown_outcome_do_not_retry(self):
        plan = {"version": 1, "content": [], "postings": []}
        original_transport = self.transport
        def reject_csrf(method, url, headers, body, timeout):
            return original_transport(method, url, {**headers, "X-CSRF-Token": "wrong"}, body, timeout)
        host = StudioHostBinding("http://127.0.0.1:8384", "session-test", "csrf-test", lambda *_: True, reject_csrf, True)
        denied = Context()
        register(denied, host=host)
        self.assertEqual(self.call(denied, "friday_studio_write_plan", {"plan": plan, "expected_revision": 0})["error"]["code"], "control_api_rejected")
        self.assertEqual(self.transport.plan_state["revision"], 0)
        self.assertEqual(len(self.transport.requests), 1)
        def lost_response(*_args):
            raise TimeoutError()
        uncertain = Context()
        register(uncertain, host=StudioHostBinding("http://127.0.0.1:8384", "session-test", "csrf-test", lambda *_: True, lost_response, True))
        self.assertEqual(self.call(uncertain, "friday_studio_write_plan", {"plan": plan, "expected_revision": 0})["error"]["code"], "unknown_plan_outcome")

    def test_paid_requests_fail_closed_without_trusted_host_approval(self):
        for approved, authorized, expected in ((False, True, "paid_action_not_approved"), (True, False, "host_authorization_required")):
            with self.subTest(expected=expected):
                ctx = self.plugin(approved=approved, authorized=authorized)
                result = self.call(ctx, "friday_studio_create_media", {"kind": "image", "prompt": "Test", "aspect_ratio": "1:1", "idempotency_key": "intent-denied-123"})
                self.assertEqual(result["error"]["code"], expected)
        self.assertEqual(self.transport.requests, [])

    def test_no_default_host_or_model_supplied_origin_and_no_retry(self):
        ctx = Context()
        register(ctx)
        args = {"kind": "video", "prompt": "Test", "aspect_ratio": "16:9", "idempotency_key": "intent-video-123"}
        self.assertEqual(self.call(ctx, "friday_studio_create_media", args)["error"]["code"], "host_binding_required")
        ctx = self.plugin()
        self.assertEqual(self.call(ctx, "friday_studio_create_media", {**args, "origin": "https://evil.invalid"})["error"]["code"], "invalid_request")
        self.assertEqual(self.call(ctx, "friday_studio_create_media", {**args, "idempotency_key": "bad"})["error"]["code"], "invalid_idempotency_key")
        self.assertEqual(self.transport.requests, [])

    def test_interactive_binding_fails_closed_without_tty(self):
        with patch.dict(os.environ, {"FRIDAY_CONTENT_STUDIO_INTERACTIVE_APPROVAL": "1", "FRIDAY_CONTROL_API_ORIGIN": "http://127.0.0.1:8384", "FRIDAY_CONTROL_API_SESSION": "session-test", "FRIDAY_CONTROL_API_CSRF": "csrf-test", "FRIDAY_CONTENT_STUDIO_OUTPUT_DIR": self.temp.name}), patch("sys.stdin.isatty", return_value=False):
            ctx = Context()
            register(ctx)
            result = self.call(ctx, "friday_studio_create_media", {"kind": "image", "prompt": "A blue room", "aspect_ratio": "1:1", "idempotency_key": "intent-no-tty-123"})
            self.assertEqual(result["error"]["code"], "paid_action_not_approved")
            self.assertEqual(self.transport.requests, [])

    def test_invalid_origin_and_missing_audio_output_path(self):
        ctx = Context()
        host = StudioHostBinding("https://evil.invalid", "session-test", "csrf-test", lambda *_: True, self.transport, True)
        register(ctx, host=host)
        result = self.call(ctx, "friday_studio_media_status", {"task_id": "task-test-1"})
        self.assertEqual(result["error"]["code"], "bridge_failure")
        ctx = self.plugin(output=False)
        result = self.call(ctx, "friday_studio_create_speech", {"text": "Hallo", "voice_id": "voice123", "idempotency_key": "intent-speech-123"})
        self.assertEqual(result["error"]["code"], "output_dir_required")
        self.assertEqual(self.transport.requests, [])


if __name__ == "__main__":
    unittest.main()
