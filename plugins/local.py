"""Synchronous mock plugin composition for policy, audit, and local lifecycle records."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from shared.hooks import inspect_untrusted, preflight_action
from shared.runtime import MockRuntime, dashboard_mapping


@dataclass
class LocalPluginSuite:
    runtime: MockRuntime = field(default_factory=MockRuntime)

    def inspect_input(self, content: str) -> dict[str, str]:
        decision = inspect_untrusted(content)
        self.runtime.audit.append({"kind": "input_inspection", "decision": decision["decision"], "executed": False})
        return decision

    def guard(self, action: str, target: str, payload: Any, *, mode: str,
              capability: Mapping[str, Any], approval: Mapping[str, Any] | None = None,
              idempotency_key: str | None = None) -> dict[str, Any]:
        decision = preflight_action(action, target, payload, mode=mode,
                                    capability=capability, approval=approval,
                                    idempotency_key=idempotency_key)
        self.runtime.audit.append({"kind": "policy_preflight", "action": action,
                                   "target": target, "decision": decision["decision"], "executed": False})
        return decision

    def activity(self, skill: str, status: str, message: str, progress: float,
                 *, task_id: str | None = None) -> dict[str, Any]:
        record = self.runtime.event(skill, status, message, progress, task_id=task_id)
        return {"local_record": record, "intended_mapping": dashboard_mapping(record), "delivered": False}

    def notify(self, channel: str, message: str) -> dict[str, Any]:
        record = {"channel": channel, "message": message, "delivered": False, "mode": "mock"}
        self.runtime.audit.append({"kind": "notification_proposal", "channel": channel, "executed": False})
        return record
