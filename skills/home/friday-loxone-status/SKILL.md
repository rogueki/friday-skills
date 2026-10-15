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

1. Obtain fresh trusted loxone.read capability and map requested rooms to allowlisted device IDs; use adapter state, not inferred names.
2. Read temperatures, humidity, contacts, lighting, shading, heating, PV, battery, consumption and alarms only where available; preserve timestamps and units.
3. Summarize normal, stale and unknown readings separately; disclose controller reachability and sensor gaps.

## Approval and failures

Tier 0 read only. Mock values are synthetic; never present them as current home state.
Offline controller or stale timestamp yields blocked/partial status, not a guessed sensor state.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Check device ID, unit and timestamp in adapter response and compare summary to raw reading.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.1 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
