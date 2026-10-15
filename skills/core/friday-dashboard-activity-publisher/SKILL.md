---
name: friday-dashboard-activity-publisher
description: Prepare local F.R.I.D.A.Y. skill lifecycle records and map them to real dashboard task/activity events only through a verified adapter.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, dashboard, core]
---

# Dashboard activity publication

Use when a task needs a local lifecycle record or a configured trusted Control API adapter. Do not claim that this skill streams events. Inputs: task/skill identity, mode, activity, status, progress, UTC clock, actual task ID and adapter capability.

1. Build a **local-only** `friday.skill.started/progress/waiting_approval/completed/failed` record under `shared/schemas/event.schema.json`; require stable ID, UTC timestamp, bounded progress and redacted activity. Never include tokens, private source text or unneeded personal data.
2. The current rogue-friday AsyncAPI has task lifecycle and `jarvis.activity.appended` events, but no `jarvis.skill.*` event. Read the [pinned contract and mapping boundary](../../../docs/CONTRACTS.md) before designing an adapter. Do not send the local record as a WebSocket event.
3. If a trusted Control API adapter has actually been implemented and is healthy, map the state to a supported task operation when a real task exists, or a redacted activity operation. Check the real endpoint and payload contract, idempotency and returned acknowledgement. In `mock`, save a fixture; in `read_only`, preview only.
4. Mark local completion only after result verification and progress 1. Report failure/approval state accurately when work stops.

Output a normalized result. If delivery fails or the endpoint is unconfigured, report `event_not_delivered` and retain the event as an artifact. Verify actual delivery with an adapter acknowledgement; a JSON payload alone is not dashboard proof.
