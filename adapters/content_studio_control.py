"""Bounded Control API client for Content Studio. Credentials and approval stay with the host."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

from shared.control_task_client import Response, _base_url


class StudioError(Exception):
    def __init__(self, code: str, status: int | None = None):
        self.code, self.status = code, status
        super().__init__(f"Content Studio: {code}")


Transport = Callable[[str, str, Mapping[str, str], bytes | None, float], Response]
TASK_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
VOICE_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
IDEMPOTENCY = re.compile(r"^[A-Za-z0-9_-]{8,128}$")
MAX_RESPONSE = 10 * 1024 * 1024


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise StudioError("redirect_denied", code)


def local_http_transport(method: str, url: str, headers: Mapping[str, str], body: bytes | None, timeout: float) -> Response:
    """Real loopback HTTP transport, opt-in through a trusted host configuration."""
    origin, _, _path = url.partition("/api/v1/")
    _base_url(origin)
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    request = Request(url, data=body, headers=dict(headers), method=method)
    try:
        with opener.open(request, timeout=timeout) as reply:
            payload = reply.read(MAX_RESPONSE + 1)
            if len(payload) > MAX_RESPONSE:
                raise StudioError("response_too_large")
            return Response(reply.status, dict(reply.headers.items()), payload)
    except HTTPError as exc:
        return Response(exc.code, {}, b"")
    except URLError as exc:
        raise StudioError("transport_unavailable") from exc


@dataclass(frozen=True)
class StudioHostBinding:
    origin: str
    session: str
    csrf: str
    approve_paid: Callable[[str, Mapping[str, Any]], bool]
    transport: Transport = local_http_transport
    authorized: bool = False


class ContentStudioClient:
    def __init__(self, host: StudioHostBinding):
        if not isinstance(host, StudioHostBinding) or host.authorized is not True:
            raise StudioError("host_authorization_required")
        self.origin = _base_url(host.origin)
        if not host.session or any(c in host.session for c in "\r\n; "):
            raise StudioError("invalid_session")
        if not host.csrf or any(c in host.csrf for c in "\r\n"):
            raise StudioError("invalid_csrf")
        if not callable(host.approve_paid) or not callable(host.transport):
            raise StudioError("invalid_host_binding")
        self.host = host

    def _send(self, method: str, path: str, body: dict[str, Any] | None = None, key: str | None = None) -> Response:
        headers = {"Cookie": f"friday_session={self.host.session}", "Accept": "application/json"}
        if method == "POST":
            headers.update({"X-CSRF-Token": self.host.csrf, "Content-Type": "application/json"})
            if not key or not IDEMPOTENCY.fullmatch(key):
                raise StudioError("invalid_idempotency_key")
            headers["Idempotency-Key"] = key
        encoded = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
        if encoded is not None and len(encoded) > 4096:
            raise StudioError("request_too_large")
        try:
            response = self.host.transport(method, self.origin + path, headers, encoded, 30.0)
        except StudioError:
            raise
        except Exception as exc:
            raise StudioError("unknown_provider_outcome" if method == "POST" else "transport_unavailable") from exc
        if not isinstance(response, Response) or not isinstance(response.body, bytes) or len(response.body) > MAX_RESPONSE:
            raise StudioError("invalid_response")
        if response.status not in {200, 202}:
            raise StudioError("control_api_rejected", response.status)
        return response

    @staticmethod
    def _envelope(response: Response, status: int) -> dict[str, Any]:
        if response.status != status:
            raise StudioError("unexpected_status", response.status)
        try:
            value = json.loads(response.body)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise StudioError("invalid_json") from exc
        if not isinstance(value, dict) or not isinstance(value.get("data"), dict):
            raise StudioError("invalid_envelope")
        return value["data"]

    def create_kie(self, *, kind: str, prompt: str, aspect_ratio: str, idempotency_key: str) -> dict[str, Any]:
        if kind not in {"image", "video"} or aspect_ratio not in {"1:1", "16:9"} or not isinstance(prompt, str) or not 1 <= len(prompt.strip()) <= 2000:
            raise StudioError("invalid_request")
        request = {"kind": kind, "prompt": prompt.strip(), "aspectRatio": aspect_ratio, "confirmed": True}
        if self.host.approve_paid("kie.create", request) is not True:
            raise StudioError("paid_action_not_approved")
        data = self._envelope(self._send("POST", "/api/v1/content-studio/kie/tasks", request, idempotency_key), 202)
        if not isinstance(data.get("taskId"), str) or not TASK_ID.fullmatch(data["taskId"]):
            raise StudioError("invalid_task_id")
        return data

    def get_kie(self, task_id: str) -> dict[str, Any]:
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise StudioError("invalid_task_id")
        data = self._envelope(self._send("GET", f"/api/v1/content-studio/kie/tasks/{task_id}"), 200)
        if data.get("taskId") != task_id or data.get("state") not in {"waiting", "queuing", "generating", "success", "fail"}:
            raise StudioError("invalid_task_status")
        return data

    def create_speech(self, *, text: str, voice_id: str, idempotency_key: str) -> bytes:
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 2500 or not isinstance(voice_id, str) or not VOICE_ID.fullmatch(voice_id):
            raise StudioError("invalid_request")
        request = {"text": text.strip(), "voiceId": voice_id, "confirmed": True}
        if self.host.approve_paid("elevenlabs.speech", request) is not True:
            raise StudioError("paid_action_not_approved")
        response = self._send("POST", "/api/v1/content-studio/elevenlabs/speech", request, idempotency_key)
        content_type = next((value for name, value in response.headers.items() if name.lower() == "content-type"), "")
        if response.status != 200 or not content_type.lower().startswith("audio/mpeg") or not response.body:
            raise StudioError("invalid_audio_response")
        return response.body
