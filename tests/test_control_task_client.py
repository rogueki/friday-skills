"""Control API task client contract tests. All transports are in-memory fakes."""

import json
import unittest

from shared.control_task_client import ControlTaskClient, Response, TaskClientError, UnknownMutationOutcome


TASK_ID = "task_" + "A" * 26


def task_response(*, version=1, status="todo", task_id=TASK_ID):
    task = {
        "id": task_id, "version": version, "createdAt": "2026-10-15T12:00:00Z",
        "updatedAt": "2026-10-15T12:00:00Z",
        "source": {"adapterId": "mock-tasks", "system": "mock", "lastSyncedAt": "2026-10-15T12:00:00Z"},
        "title": "Test task",
        "status": status, "priority": "P3", "agentId": None, "model": None,
        "progress": {"mode": "none", "value": None}, "startedAt": None, "runtimeMs": None, "dueAt": None,
        "estimatedCompletionAt": None, "blockers": [], "lastActivityAt": None,
        "artifactCount": 0, "artifacts": [], "steps": [], "toolCalls": [],
        "sourceRefs": [], "approvalIds": [], "errors": [], "createdBy": {"type": "system", "id": "mock"},
    }
    return json.dumps({"contractVersion": "1.0.0", "data": task,
                       "freshness": {"state": "fresh", "asOf": "2026-10-15T12:00:00Z"}}).encode()


class RecordingTransport:
    def __init__(self, response=None):
        self.calls = []
        self.response = response or Response(201, {}, task_response())

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append((method, url, headers, body, timeout))
        return self.response


class ControlTaskClientTests(unittest.TestCase):
    def test_create_contract_and_idempotent_same_payload(self):
        transport = RecordingTransport()
        client = ControlTaskClient("http://127.0.0.1:8384", transport=transport)
        task = client.create({"title": "Test task", "priority": "P3"}, session="opaque_session",
                             csrf="csrf-token", idempotency_key="request-123")
        self.assertEqual((task.id, task.version, task.if_match), (TASK_ID, 1, "1"))
        self.assertEqual(transport.calls[0][0:2], ("POST", "http://127.0.0.1:8384/api/v1/tasks"))
        self.assertEqual(transport.calls[0][2]["Cookie"], "jarvis_session=opaque_session")
        self.assertEqual(transport.calls[0][2]["X-CSRF-Token"], "csrf-token")
        self.assertEqual(transport.calls[0][2]["Idempotency-Key"], "request-123")
        client.create({"priority": "P3", "title": "Test task"}, session="opaque_session",
                      csrf="csrf-token", idempotency_key="request-123")
        self.assertEqual(len(transport.calls), 2)

    def test_reject_changed_payload_with_same_key_before_dispatch(self):
        transport = RecordingTransport()
        client = ControlTaskClient("http://localhost:8384", transport=transport)
        client.create({"title": "First"}, session="s", csrf="c", idempotency_key="same-key")
        with self.assertRaises(ValueError):
            client.create({"title": "Other"}, session="s", csrf="c", idempotency_key="same-key")
        self.assertEqual(len(transport.calls), 1)

    def test_update_uses_version_and_maps_conflict(self):
        transport = RecordingTransport(Response(200, {}, task_response(version=2, status="review")))
        client = ControlTaskClient("http://localhost:8384", transport=transport)
        task = client.update(TASK_ID, {"status": "review"}, session="s", csrf="c", if_match="1")
        self.assertEqual((task.status, task.if_match), ("review", "2"))
        self.assertEqual(transport.calls[0][2]["If-Match"], "1")
        transport.response = Response(409, {}, b'{"secret":"server body"}')
        with self.assertRaises(TaskClientError) as raised:
            client.update(TASK_ID, {"status": "done"}, session="s", csrf="c", if_match="1")
        self.assertEqual((raised.exception.code, raised.exception.status), ("conflict", 409))
        self.assertNotIn("secret", str(raised.exception))

    def test_auth_and_csrf_are_required_without_dispatch(self):
        transport = RecordingTransport()
        client = ControlTaskClient("http://localhost:8384", transport=transport)
        for session, csrf in (("", "c"), ("s", "")):
            with self.assertRaises(ValueError):
                client.create({"title": "Task"}, session=session, csrf=csrf, idempotency_key="request-123")
        self.assertEqual(transport.calls, [])

    def test_unauthorized_and_forbidden(self):
        transport = RecordingTransport(Response(401, {}, b"token is a secret"))
        client = ControlTaskClient("http://localhost:8384", transport=transport)
        with self.assertRaises(TaskClientError) as unauthorized:
            client.get(TASK_ID, session="s")
        self.assertEqual(unauthorized.exception.code, "unauthorized")
        transport.response = Response(403, {}, b"forbidden secret")
        with self.assertRaises(TaskClientError) as forbidden:
            client.create({"title": "Task"}, session="s", csrf="c", idempotency_key="request-123")
        self.assertEqual(forbidden.exception.code, "forbidden")
        self.assertNotIn("secret", str(forbidden.exception))

    def test_mutation_timeout_and_server_failure_have_unknown_outcome(self):
        def timeout(*_args):
            raise TimeoutError("cookie: private")

        client = ControlTaskClient("http://localhost:8384", transport=timeout)
        with self.assertRaises(UnknownMutationOutcome) as timeout_error:
            client.create({"title": "Task"}, session="s", csrf="c", idempotency_key="request-123")
        self.assertNotIn("private", str(timeout_error.exception))
        transport = RecordingTransport(Response(503, {}, b"failure"))
        client = ControlTaskClient("http://localhost:8384", transport=transport)
        with self.assertRaises(UnknownMutationOutcome):
            client.update(TASK_ID, {"status": "waiting"}, session="s", csrf="c", if_match="1")
        self.assertEqual(len(transport.calls), 1)

    def test_get_and_invalid_response(self):
        transport = RecordingTransport(Response(200, {}, task_response()))
        client = ControlTaskClient("http://[::1]:8384", transport=transport)
        self.assertEqual(client.get(TASK_ID, session="s").id, TASK_ID)
        transport.response = Response(200, {}, b'{}')
        with self.assertRaises(TaskClientError) as invalid:
            client.get(TASK_ID, session="s")
        self.assertEqual(invalid.exception.code, "invalid_response")

    def test_mutation_success_with_invalid_or_wrong_task_response_is_uncertain(self):
        transport = RecordingTransport(Response(201, {}, b'{}'))
        client = ControlTaskClient("http://localhost:8384", transport=transport)
        with self.assertRaises(UnknownMutationOutcome):
            client.create({"title": "Task"}, session="s", csrf="c", idempotency_key="request-123")
        transport.response = Response(200, {}, task_response(task_id="task_" + "B" * 26))
        with self.assertRaises(UnknownMutationOutcome):
            client.update(TASK_ID, {"status": "review"}, session="s", csrf="c", if_match="1")

    def test_non_loopback_and_malformed_origins_rejected(self):
        transport = RecordingTransport()
        for origin in ("https://example.com", "http://192.168.1.3:8384", "ftp://localhost",
                       "http://localhost:8384/path", "http://user:pass@localhost:8384"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                ControlTaskClient(origin, transport=transport)
        self.assertEqual(transport.calls, [])

    def test_no_default_network_or_implicit_credentials(self):
        client = ControlTaskClient("http://localhost:8384")
        with self.assertRaises(TaskClientError) as missing:
            client.get(TASK_ID, session="s")
        self.assertEqual(missing.exception.code, "transport_unavailable")


if __name__ == "__main__":
    unittest.main()
