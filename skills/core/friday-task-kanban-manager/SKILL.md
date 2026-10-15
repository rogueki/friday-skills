---
name: friday-task-kanban-manager
description: Structure longer F.R.I.D.A.Y. tasks with dependencies, progress and evidence-based completion when a Kanban workflow is needed.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, kanban, core]
---

# Task and Kanban management

Use for work spanning several steps, sessions or independent deliverables. Do not create a board item for a one-step answer or imply the dashboard has a task adapter. Inputs: requested outcome, owner/board if known, priority, dependencies, artifacts, acceptance tests, mode and `task.write` capability.

1. Define a measurable completion condition before starting. Split independent work into separate tasks; dependencies must point to actual prerequisites.
2. Check whether a task adapter is healthy and whether the mode permits writes. In `mock`, use fixture IDs only. In `read_only`, produce a proposed task record. In `live`, a task creation may be tier 1 if within the authorized board; user-directed external notifications still use tier 2.
3. Record status transitions, progress evidence, blockers and artifact references. With an implemented task adapter, use the actual Control API task operations; the server may then emit its existing `jarvis.task.*` events. Do not publish raw WebSocket events from a skill.
4. Close only after verifying each acceptance criterion against an observed artifact or response. If an external dependency is pending, mark blocked or partial instead.

Output a normalized result plus task ID only when an adapter returned one. On timeout, query by idempotency key before retrying to avoid duplicate tasks. Report uncertain writes as uncertain, not completed.
