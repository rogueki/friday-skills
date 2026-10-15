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

1. Identify each meter's measurement boundary (house load, grid import/export, PV inverter, battery charge/discharge), sign convention, interval, unit, timezone and provenance. Reject totals that mix different boundaries or double-count battery flows. The current Loxone status normalizer exposes fresh instantaneous W and percent readings; it does not provide historical kWh, tariff, battery-capacity or native Miniserver data.
2. For interval measurements, compute energy only from valid matched intervals (`kWh = average kW × hours`), recording gaps and meter resets. Never label a single W sample as consumption over a day. Check whether PV production, self-consumption and grid import are independently measured before calculating a balance; otherwise use a qualitative comparison.
3. Determine flexible load windows, heating/hot-water and shade effects using dated weather forecast and tariff periods when available. Record source and retrieval time; never treat forecast, tariff estimate or proposed automation as a measured saving. Keep occupant comfort limits, device safe ranges and battery reserve as hard constraints.
4. Present a ranked recommendation with proposed time, supporting measurement window, expected benefit range or `not quantifiable`, comfort impact, assumptions, data gaps and verification method. Any control recommendation is an `actions_proposed` draft for `friday-loxone-control` or `friday-home-scene-manager`, with its own policy and approval; this skill issues no command.

## Approval and failures

No device action without separate policy and tier 2 approval through a real adapter. Tariff switching is outside scope.
Sparse or stale telemetry yields qualitative advice; do not invent precise savings or a successful automation.
If import/export direction, meter boundary or tariff validity is unknown, omit numerical cost or self-consumption claims. Do not promise a scheduled change: no home scheduler or gateway is connected.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recompute sample energy balance and check recommendation against comfort and battery reserve.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
