"""Host-side source binding for F.R.I.D.A.Y. mock action proposals.

The host must authenticate the initiating request and capture source metadata
outside model-facing tool parameters. This module cannot authenticate either.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any

from shared.policy import action_fingerprint, risk_tier
from shared.runtime import MockRuntime


SOURCE_TYPES = frozenset({"email", "web", "pdf", "office", "chat", "attachment", "tool", "imported_skill"})
SHA256_HEX = re.compile(r"[0-9a-f]{64}\Z")


class InputTrustError(ValueError):
    """A bound proposal cannot be made from this source and request."""


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip() or len(value) > 1024:
        raise InputTrustError(f"invalid {label}")
    return value


def _digest(content: str) -> str:
    if not isinstance(content, str):
        raise InputTrustError("source content must be text")
    return sha256(content.encode("utf-8")).hexdigest()


def _snapshot_payload(payload: Any) -> Any:
    try:
        return json.loads(json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True))
    except (TypeError, ValueError) as exc:
        raise InputTrustError("JSON-compatible action payload required") from exc


@dataclass(frozen=True)
class SourceEnvelope:
    source_id: str
    source_type: str
    canonical_identifier: str
    retrieved_at: datetime
    extraction_method: str
    content_sha256: str
    trust_class: str = "untrusted"
    complete: bool = True

    def validate(self) -> None:
        _required_text(self.source_id, "source ID")
        _required_text(self.canonical_identifier, "canonical identifier")
        _required_text(self.extraction_method, "extraction method")
        if (not isinstance(self.source_type, str) or self.source_type not in SOURCE_TYPES
                or self.trust_class != "untrusted"):
            raise InputTrustError("unsupported source classification")
        if not isinstance(self.retrieved_at, datetime) or self.retrieved_at.tzinfo is None:
            raise InputTrustError("aware retrieval time required")
        if self.retrieved_at.astimezone(timezone.utc) > datetime.now(timezone.utc):
            raise InputTrustError("retrieval time is in the future")
        if not isinstance(self.content_sha256, str) or not SHA256_HEX.fullmatch(self.content_sha256):
            raise InputTrustError("invalid source digest")
        if self.complete is not True:
            raise InputTrustError("incomplete source extraction")


def capture_source(*, source_id: str, source_type: str, canonical_identifier: str,
                   retrieved_at: datetime, extraction_method: str, content: str,
                   complete: bool = True) -> SourceEnvelope:
    """Capture provenance from a trusted reader, before content reaches the model."""
    envelope = SourceEnvelope(source_id, source_type, canonical_identifier, retrieved_at,
                              extraction_method, _digest(content), complete=complete)
    envelope.validate()
    return envelope


@dataclass(frozen=True)
class HostRequest:
    """Exact intent recorded by an authenticating host, never from tool JSON."""

    request_id: str
    operator_id: str
    action: str
    target: str
    action_sha256: str
    source_id: str
    source_sha256: str

    def validate(self) -> None:
        for label, value in (("request ID", self.request_id), ("operator ID", self.operator_id),
                             ("action", self.action), ("target", self.target), ("source ID", self.source_id)):
            _required_text(value, label)
        for label, value in (("action digest", self.action_sha256), ("source digest", self.source_sha256)):
            if not isinstance(value, str) or not SHA256_HEX.fullmatch(value):
                raise InputTrustError(f"invalid {label}")


def bind_host_request(*, request_id: str, operator_id: str, action: str, target: str,
                      payload: Any, source: SourceEnvelope) -> HostRequest:
    """Host-only factory; the caller must already have authenticated the operator."""
    if not isinstance(source, SourceEnvelope):
        raise InputTrustError("host-captured source required")
    source.validate()
    try:
        action_hash = action_fingerprint(action, target, _snapshot_payload(payload))
    except (TypeError, ValueError) as exc:
        raise InputTrustError("invalid action payload") from exc
    request = HostRequest(request_id, operator_id, action, target, action_hash,
                          source.source_id, source.content_sha256)
    request.validate()
    return request


def create_bound_mock_proposal(*, runtime: MockRuntime, request: HostRequest,
                               source: SourceEnvelope, content: str, action: str,
                               target: str, payload: Any) -> dict[str, Any]:
    """Fail closed before the only effect: an in-memory mock proposal."""
    if not isinstance(runtime, MockRuntime) or not isinstance(request, HostRequest) or not isinstance(source, SourceEnvelope):
        raise InputTrustError("trusted host objects required")
    request.validate()
    source.validate()
    if _digest(content) != source.content_sha256:
        raise InputTrustError("source content changed")
    if (request.source_id, request.source_sha256) != (source.source_id, source.content_sha256):
        raise InputTrustError("source binding mismatch")
    if action != request.action or target != request.target:
        raise InputTrustError("action or target mismatch")
    try:
        payload_snapshot = _snapshot_payload(payload)
        action_hash = action_fingerprint(action, target, payload_snapshot)
    except (TypeError, ValueError) as exc:
        raise InputTrustError("invalid action payload") from exc
    if action_hash != request.action_sha256:
        raise InputTrustError("action payload mismatch")
    return runtime.propose(action, target, payload_snapshot, tier=risk_tier(action))
