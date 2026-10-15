---
name: friday-energy-optimizer
description: Analyze home PV, battery, load and weather data for comfort-aware energy recommendations; no automatic control.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, home, energy]
---

# friday-energy-optimizer

## Routing

Use to recommend energy timing or automation candidates. Do not use for comparing retail tariffs or commanding a device.

## Inputs and capability

Inputs: Time-stamped PV, import/export, battery SoC, load, heating/hot water, weather, tariff windows and occupant comfort limits. Required read capabilities: loxone.read or another explicitly configured energy.telemetry.read feed for PV, battery and loads; weather.read and tariff.read are optional inputs and must be dated. mock uses synthetic telemetry; read_only and live produce advice only. No loxone.write is invoked by this skill.

## Procedure

1. Align measurements by time zone, interval and unit; identify missing telemetry and avoid comparing instantaneous power with energy.
2. Estimate self-consumption, peaks and flexible-load windows under explicit weather/tariff assumptions; account for battery reserve and comfort bounds.
3. Recommend action with expected benefit range, comfort effect, assumptions and optional automation proposal; separate estimate from observed saving.

## Approval and failures

No device action without separate policy and tier 2 approval through a real adapter. Tariff switching is outside scope.
Sparse or stale telemetry yields qualitative advice; do not invent precise savings or a successful automation.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recompute sample energy balance and check recommendation against comfort and battery reserve.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
