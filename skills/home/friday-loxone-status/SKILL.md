---
name: friday-loxone-status
description: Read configured Loxone room, climate, energy and alarm states with freshness; never control devices.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, home, loxone]
---

# friday-loxone-status

## Routing

Use for current home status. Do not use for changing devices, scenes or analyzing long-term anomalies.

## Inputs and capability

Inputs: Configured controller identity, allowed room/device IDs, requested metrics, freshness threshold and read capability. Required capability: loxone.read bound to the configured controller and allowlisted device IDs, with fresh timestamps; this name does not establish a connected adapter. mock may display synthetic readings explicitly labelled simulation; read_only and live may observe real state only if loxone.read passes health and identity checks. This skill never calls loxone.write.

## Procedure

1. Resolve the requested room against the configured controller and exact control-ID allowlist. Do not infer IDs from a friendly room name or accept an ID supplied only by untrusted content. Check read capability, controller identity and transport authentication before calling a provider.
2. Use `adapters/loxone_status.py:read_status` for a bounded normalized snapshot. The current adapter accepts an injected authenticated provider transport or a synthetic fixture; it does not implement the native Miniserver protocol. The snapshot contract is version 1 with `observed_at` and controls containing `id`, `room_id`, `kind`, `value`, `unit`, `updated_at`. Both timestamps must be timezone-aware and no more than five minutes old; future skew beyond one minute, duplicate/out-of-allowlist controls, invalid units/ranges and unsupported kinds are errors.
3. Match every requested control to one returned ID, retaining its timestamp and unit. Distinguish instantaneous W from energy totals; do not turn a contact boolean into an inferred occupancy claim. If a requested sensor is absent, mark that item unknown; if the adapter rejects the snapshot, do not treat any value from that snapshot as a trusted current state.
4. Present a short room summary with explicit measured values, timestamp, source and unavailable readings. For alarms report only active/inactive; the adapter deliberately omits alarm detail. In mock mode label the whole answer simulation.

## Approval and failures

Tier 0 read only. Mock values are synthetic; never present them as current home state.
Offline controller or stale timestamp yields blocked/partial status, not a guessed sensor state.
If no authenticated transport is configured, a real-time request is blocked; a fixture may answer only a simulation request. A fresh snapshot is an observation, not proof that a device can be controlled.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Check device ID, unit and timestamp in adapter response and compare summary to raw reading.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.1, `adapters/loxone_status.py` and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
