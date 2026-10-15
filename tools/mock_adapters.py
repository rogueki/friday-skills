"""Fixture-only adapters with no network, process, or real filesystem mutation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from shared.runtime import load_fixture


@dataclass
class MockAdapter:
    domain: str
    calls: list[dict[str, Any]] = field(default_factory=list)

    def read(self, fixture: str) -> dict[str, Any]:
        record = load_fixture(self.domain, fixture)
        self.calls.append({"method": "read", "fixture": fixture, "external_effect": False})
        return record

    def propose(self, action: str, payload: Any) -> dict[str, Any]:
        record = {"method": "propose", "action": action, "payload": payload, "external_effect": False}
        self.calls.append(record)
        return record

    def execute(self, *_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError("mock adapters never execute external writes")
