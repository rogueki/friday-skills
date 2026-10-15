---
name: friday-loxone-control
description: Plan and, only with a real approved adapter, change allowlisted Loxone light, shade or setpoint devices.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, home, loxone]
---

# friday-loxone-control

## Routing

Use for an explicit single smart-home control request. Do not use for read-only status or security-critical locks/alarms/access.

## Inputs and capability

Inputs: Exact configured controller/device identity, desired action/value, safe operating range, current state, affected occupants and action-specific approval. Required capabilities: loxone.read for identity, safe pre-state and readback, and loxone.write for the exact allowlisted command. Both require fresh trusted health records; naming them does not install a bridge. mock simulates only, read_only can preview only, and live may write solely after tier 2 action-bound approval and safety checks.

## Procedure

1. Resolve the request to one configured controller, one allowlisted device ID, device type and exact desired value. Accept only supported light, shade or setpoint commands with configured per-device safe bounds. Reject ambiguous names, unsupported units, contradictory commands and any door, lock, alarm, access or other security-critical target.
2. Obtain an authenticated fresh pre-state for that exact control via `loxone.read`; verify controller/device identity, unit, timestamp (at most five minutes old), allowed range and occupant/comfort constraints. The existing `adapters/loxone_status.py` only normalizes read snapshots; no native Miniserver client or live write adapter exists in this repository.
3. Show device, current value, desired value, safe bounds, occupants affected, likely effect and safe recovery plan. Bind a Tier 2 approval to the exact controller, control ID, command, value, pre-state, target fingerprint and expiry. Recheck capability, state and single-use approval just before issuing the command; state drift requires a new preview and approval.
4. A future host-owned live adapter must use a durable idempotency key and record dispatch/outcome. Dispatch only once. If the response is lost or uncertain, stop and reconcile with the provider instead of blindly retrying. Read back the same device with a newer timestamp and compare unit/value within the documented tolerance. Mark success only after matching authoritative readback; otherwise report partial or blocked with explicit uncertainty.

## Approval and failures

No door, alarm, access-control or safety-critical system manipulation in this skill. Mock and read_only never write. No configured identity or safe state means no write.
If write acknowledgement is missing or readback differs, report partial/failed and do not retry blindly. Offline adapter blocks the action.
The E2E8 `adapters/loxone_e2e_mock.py` scenario demonstrates one light with a simulated one-shot grant and in-memory readback. Its `mock_approved` result does not prove live approval, write capability or physical state change. Never route a live command through this mock.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Post-action readback must match requested safe state; mock simulation is not device success. Report pre-state evidence, approval fingerprint, idempotency key, dispatch outcome and per-device readback status without leaking credentials.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.2 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
