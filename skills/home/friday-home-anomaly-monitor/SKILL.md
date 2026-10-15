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

1. Resolve controller/control IDs against configuration; validate unit, timezone, freshness, sampling gaps and sensor health. The current `loxone_status` adapter supplies only a current bounded snapshot, not history. Require a separately configured time-series source for a trend; do not fabricate one from a single reading.
2. Build a comparable baseline by hour and, when supported by data, weekday, season, weather and occupancy. Record baseline length, sample count, variance and exclusions. If occupancy is unknown, keep it unknown; do not infer it from a contact or one power spike.
3. Compare candidate abnormal load, temperature fall, heating with an open window, PV drop, prolonged appliance load or battery fault against explicit threshold and duration. Corroborate with an independent signal or contextual event (for example, irradiance before asserting PV failure). Distinguish physical anomaly from stale sensor, meter reset, network outage or ordinary schedule change.
4. Report affected control and interval, observation versus baseline, confidence, alternative explanations and one safe manual check. Deduplicate by controller/control, anomaly kind and time window; rate-limit repeats. Recurring observation and delivery require verified `scheduler.run` and `notification.deliver`, which this repository does not provide. Without them return a one-time analysis or a proposed watch, never claim an active alarm.

## Approval and failures

No panic alert from one outlier; no automatic device writes or emergency calls.
Sensor outage or missing baseline is a data-quality alert, not proof of physical fault.
Escalate according to the configured channel and quiet-hour policy only after corroboration; do not call emergency services or issue control writes from this skill.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Replay sample window and confirm threshold/duration plus corroborating signal; check alert deduplication.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
