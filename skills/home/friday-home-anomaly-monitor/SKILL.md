---
name: friday-home-anomaly-monitor
description: Detect plausible home energy and climate anomalies from time-series evidence; recurring alerts need a scheduler.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, home, home]
---

# friday-home-anomaly-monitor

## Routing

Use for unusual consumption, temperature, PV or battery patterns. Do not use for one-time current status or device control.

## Inputs and capability

Inputs: Timestamped sensor history, baseline period, sensor health, operating context, alert thresholds and optional scheduler. Required capability: loxone.read or configured home.telemetry.read with timestamped history; scheduler.run and notification.deliver are separately required for an ongoing watch. mock replays synthetic traces, read_only performs one-time analysis, and live may monitor only through verified hooks. No control write is allowed.

## Procedure

1. Validate device identity, timestamp, unit and sensor health; build comparable baselines by hour, season and occupancy where available.
2. Test candidate anomalies (unusual load, temperature fall, open window with heating, PV outage, active appliance, battery issue) against multiple signals and duration.
3. Report severity with evidence, alternative explanations and recommended check. Recurring watch requires configured scheduler/hook, deduplication and quiet-hours policy.

## Approval and failures

No panic alert from one outlier; no automatic device writes or emergency calls.
Sensor outage or missing baseline is a data-quality alert, not proof of physical fault.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Replay sample window and confirm threshold/duration plus corroborating signal; check alert deduplication.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
