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

Use when a workflow needs a local lifecycle record or a verified Dashboard task update. This skill cannot install a publisher. Inputs: skill invocation, real task ID if any, mode, result status, progress, redacted activity, UTC timestamp and verified adapter capability.

1. Create a local `friday.skill.started`, `.progress`, `.waiting_approval`, `.completed` or `.failed` record under `shared/schemas/event.schema.json`. Use a stable event ID, UTC timestamp, progress in `[0,1]`, and brief activity free of secrets and source content. Preserve other internal states in `status`; do not invent an event type.
2. Apply the [delivery matrix](references/delivery-matrix.md). A local record or `dashboard_mapping(...).publishable=false` is only a proposal. The checked parent contract has `jarvis.task.*` and `jarvis.activity.appended`; it does not accept `friday.skill.*` or `jarvis.skill.*`.
3. With a real task and a trusted authenticated Control API adapter, update only fields supported by its current POST/PATCH contract. The server owns `jarvis.task.*` events. The checked contract has no activity-append endpoint, so a taskless standalone activity remains local. `mock` and `read_only` never publish.
4. Record `delivered` only after an authoritative server response and correlation to the same task/version; distinguish accepted mutation from observed Dashboard display. On timeout, 5xx, malformed success or conflict, preserve an `unknown`/`failed` delivery state and reconcile before another write.
5. Emit local completion only after underlying result verification and no pending approval. A dashboard event never proves the task itself succeeded.

Output the normalized result with local event ID, proposed mapping, task ID if verified, delivery state, acknowledgement reference if any, and remaining verification gaps. Do not include raw mail, financial, family or credential content in activity text.
