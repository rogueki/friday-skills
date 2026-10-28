"""Opt-in, transport-injected client for rogue-friday's Control API task contract.

No transport or credentials are installed by default. This module does not publish
activity events or turn a local Friday record into a Control API task implicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from ipaddress import ip_address
from typing import Any, Callable, Mapping
from urllib.parse import quote, urlsplit
import json
import re


TASK_ID = re.compile(r"^task_[0-9A-Za-z]{26}$")
AGENT_ID = re.compile(r"^agent_[0-9A-Za-z]{26}$")
STATUSES = frozenset({"triage", "todo", "ready", "running", "waiting", "review", "done", "failed", "cancelled"})
PRIORITIES = frozenset({"P0", "P1", "P2", "P3", "P4"})
CREATE_FIELDS = frozenset({"title", "description", "priority", "agentId", "model", "dueAt", "labels"})
UPDATE_FIELDS = frozenset({"title", "description", "status", "priority", "agentId", "dueAt", "labels"})
TASK_REQUIRED = frozenset({
    "id", "version", "createdAt", "updatedAt", "source", "title", "status",
    "priority", "agentId", "model", "progress", "startedAt", "runtimeMs",
    "dueAt", "estimatedCompletionAt", "blockers", "lastActivityAt", "artifactCount",
    "artifacts", "steps", "toolCalls", "sourceRefs", "approvalIds", "errors", "createdBy",
})
TASK_OPTIONAL = frozenset({"labels", "description", "agentName", "parentTaskId"})


class TaskClientError(Exception):
    """Safe, credential-free public error; server bodies are never interpolated."""

    def __init__(self, code: str, *, status: int | None = None) -> None:
        self.code = code
        self.status = status
        super().__init__(f"Control API task request: {code}")


class UnknownMutationOutcome(TaskClientError):
    """Transport failed after dispatch may have reached the server; reconcile first."""


@dataclass(frozen=True)
class Response:
    status: int
    headers: Mapping[str, str]
    body: bytes


Transport = Callable[[str, str, Mapping[str, str], bytes | None, float], Response]


@dataclass(frozen=True)
class TaskSnapshot:
    id: str
    version: int
    title: str
    status: str
    priority: str
    raw: Mapping[str, Any]

    @property
    def if_match(self) -> str:
        return str(self.version)


def _base_url(value: str) -> str:
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except (ValueError, AttributeError) as exc:
        raise ValueError("invalid Control API URL") from exc
    if parsed.scheme not in {"http", "https"} or not hostname or parsed.username or parsed.password:
        raise ValueError("Control API URL must use HTTP(S) without userinfo")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment or port == 0:
        raise ValueError("Control API URL must be an origin")
    if hostname != "localhost":
        try:
            if not ip_address(hostname).is_loopback:
                raise ValueError("Control API URL must be loopback")
        except ValueError as exc:
            raise ValueError("Control API URL must be loopback") from exc
    return value.rstrip("/")


def _text(value: Any, name: str, *, maximum: int | None = None) -> None:
    if not isinstance(value, str) or not value.strip() or any(ch in value for ch in "\r\n\x00"):
        raise ValueError(f"invalid {name}")
    if maximum is not None and len(value) > maximum:
        raise ValueError(f"invalid {name}")


def _date_time(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _payload(data: Mapping[str, Any], *, update: bool) -> bytes:
    if not isinstance(data, Mapping) or not data or set(data) - (UPDATE_FIELDS if update else CREATE_FIELDS):
        raise ValueError("invalid task fields")
    if not update and "title" not in data:
        raise ValueError("task title required")
    for name, value in data.items():
        if name == "title":
            _text(value, name, maximum=300)
        elif name == "description":
            if not isinstance(value, str):
                raise ValueError("invalid description")
        elif name == "status":
            if not isinstance(value, str) or value not in STATUSES:
                raise ValueError("invalid status")
        elif name == "priority":
            if not isinstance(value, str) or value not in PRIORITIES:
                raise ValueError("invalid priority")
        elif name == "agentId":
            if value is not None and (not isinstance(value, str) or not AGENT_ID.fullmatch(value)):
                raise ValueError("invalid agentId")
        elif name in {"model", "dueAt"}:
            if value is not None and not isinstance(value, str):
                raise ValueError(f"invalid {name}")
            if name == "dueAt" and value is not None and not _date_time(value):
                raise ValueError("invalid dueAt")
        elif name == "labels":
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                raise ValueError("invalid labels")
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _snapshot(body: bytes) -> TaskSnapshot:
    try:
        envelope = json.loads(body)
    except (ValueError, TypeError) as exc:
        raise TaskClientError("invalid_response") from exc
    if not isinstance(envelope, dict) or set(envelope) != {"contractVersion", "data", "freshness"}:
        raise TaskClientError("invalid_response")
    if not isinstance(envelope["contractVersion"], str) or not re.fullmatch(r"\d+\.\d+\.\d+", envelope["contractVersion"]):
        raise TaskClientError("invalid_response")
    freshness = envelope["freshness"]
    if not isinstance(freshness, dict) or set(freshness) != {"state", "asOf"}:
        raise TaskClientError("invalid_response")
    if freshness["state"] not in {"fresh", "stale", "unknown", "offline-cache"}:
        raise TaskClientError("invalid_response")
    if freshness["asOf"] is not None and (not isinstance(freshness["asOf"], str) or not _date_time(freshness["asOf"])):
        raise TaskClientError("invalid_response")
    task = envelope["data"]
    if not isinstance(task, dict) or not TASK_REQUIRED <= task.keys() or set(task) - TASK_REQUIRED - TASK_OPTIONAL:
        raise TaskClientError("invalid_response")
    if not isinstance(task["id"], str) or not TASK_ID.fullmatch(task["id"]):
        raise TaskClientError("invalid_response")
    if type(task["version"]) is not int or task["version"] < 1:
        raise TaskClientError("invalid_response")
    if not isinstance(task["title"], str) or not 1 <= len(task["title"]) <= 300:
        raise TaskClientError("invalid_response")
    if not isinstance(task["status"], str) or task["status"] not in STATUSES:
        raise TaskClientError("invalid_response")
    if not isinstance(task["priority"], str) or task["priority"] not in PRIORITIES:
        raise TaskClientError("invalid_response")
    if not isinstance(task["createdAt"], str) or not _date_time(task["createdAt"]):
        raise TaskClientError("invalid_response")
    if not isinstance(task["updatedAt"], str) or not _date_time(task["updatedAt"]):
        raise TaskClientError("invalid_response")
    source = task["source"]
    actor = task["createdBy"]
    if not isinstance(source, dict) or not {"adapterId", "system", "lastSyncedAt"} <= source.keys():
        raise TaskClientError("invalid_response")
    if not isinstance(source["adapterId"], str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", source["adapterId"]):
        raise TaskClientError("invalid_response")
    if not isinstance(source["system"], str) or not isinstance(source["lastSyncedAt"], str) or not _date_time(source["lastSyncedAt"]):
        raise TaskClientError("invalid_response")
    if not isinstance(actor, dict) or actor.get("type") not in {"user", "agent", "system", "adapter"} or not isinstance(actor.get("id"), str):
        raise TaskClientError("invalid_response")
    progress = task["progress"]
    if not isinstance(progress, dict) or set(progress) != {"mode", "value"} or progress["mode"] not in {"determinate", "indeterminate", "none"}:
        raise TaskClientError("invalid_response")
    value = progress["value"]
    if value is not None and (type(value) not in {int, float} or not 0 <= value <= 1):
        raise TaskClientError("invalid_response")
    for name in ("blockers", "artifacts", "steps", "toolCalls", "sourceRefs", "approvalIds", "errors"):
        if not isinstance(task[name], list):
            raise TaskClientError("invalid_response")
    if type(task["artifactCount"]) is not int or task["artifactCount"] < 0:
        raise TaskClientError("invalid_response")
    return TaskSnapshot(task["id"], task["version"], task["title"], task["status"], task["priority"], envelope)


class ControlTaskClient:
    def __init__(self, origin: str, *, transport: Transport | None = None, timeout: float = 5.0) -> None:
        self.origin = _base_url(origin)
        if not 0 < timeout <= 30:
            raise ValueError("timeout must be between 0 and 30 seconds")
        self.timeout = timeout
        self.transport = transport
        self._keys: dict[str, str] = {}

    def _send(self, method: str, path: str, *, session: str, csrf: str | None = None,
              idempotency_key: str | None = None, if_match: str | None = None,
              body: bytes | None = None, expected: int = 200) -> TaskSnapshot:
        _text(session, "session")
        if any(ch in session for ch in ";,= "):
            raise ValueError("invalid session")
        if method != "GET":
            _text(csrf, "CSRF token")
        if self.transport is None:
            raise TaskClientError("transport_unavailable")
        headers = {"Accept": "application/json", "Cookie": f"friday_session={session}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        if csrf is not None:
            headers["X-CSRF-Token"] = csrf
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key
        if if_match is not None:
            headers["If-Match"] = if_match
        try:
            response = self.transport(method, self.origin + path, headers, body, self.timeout)
        except Exception:
            if method == "GET":
                raise TaskClientError("transport_failure") from None
            raise UnknownMutationOutcome("unknown_outcome") from None
        if not isinstance(response, Response) or type(response.status) is not int:
            if method != "GET":
                raise UnknownMutationOutcome("unknown_outcome")
            raise TaskClientError("invalid_response")
        if response.status == expected:
            try:
                snapshot = _snapshot(response.body)
            except TaskClientError as exc:
                if method != "GET":
                    raise UnknownMutationOutcome("unknown_outcome") from exc
                raise
            if method != "GET" and snapshot.raw["freshness"]["state"] != "fresh":
                raise UnknownMutationOutcome("unknown_outcome")
            return snapshot
        codes = {400: "bad_request", 401: "unauthorized", 403: "forbidden", 404: "not_found",
                 409: "conflict", 422: "unprocessable", 429: "rate_limited", 503: "service_unavailable"}
        if response.status >= 500 and method != "GET":
            raise UnknownMutationOutcome("unknown_outcome", status=response.status)
        raise TaskClientError(codes.get(response.status, "unexpected_status"), status=response.status)

    def create(self, data: Mapping[str, Any], *, session: str, csrf: str, idempotency_key: str) -> TaskSnapshot:
        _text(idempotency_key, "idempotency key", maximum=128)
        if len(idempotency_key) < 8:
            raise ValueError("invalid idempotency key")
        body = _payload(data, update=False)
        fingerprint = sha256(body).hexdigest()
        previous = self._keys.setdefault(idempotency_key, fingerprint)
        if previous != fingerprint:
            raise ValueError("idempotency key reused for different payload")
        return self._send("POST", "/api/v1/tasks", session=session, csrf=csrf,
                          idempotency_key=idempotency_key, body=body, expected=201)

    def update(self, task_id: str, data: Mapping[str, Any], *, session: str, csrf: str,
               if_match: str) -> TaskSnapshot:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task id")
        _text(if_match, "If-Match")
        if not re.fullmatch(r"[1-9]\d*", if_match):
            raise ValueError("If-Match must be task version")
        body = _payload(data, update=True)
        result = self._send("PATCH", f"/api/v1/tasks/{quote(task_id)}", session=session,
                            csrf=csrf, if_match=if_match, body=body)
        if result.id != task_id:
            raise UnknownMutationOutcome("unknown_outcome")
        return result

    def get(self, task_id: str, *, session: str) -> TaskSnapshot:
        if not TASK_ID.fullmatch(task_id):
            raise ValueError("invalid task id")
        result = self._send("GET", f"/api/v1/tasks/{quote(task_id)}", session=session)
        if result.id != task_id:
            raise TaskClientError("invalid_response")
        return result
