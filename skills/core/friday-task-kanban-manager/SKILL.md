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

Use for work crossing the configured duration threshold, sessions or independent deliverables. A short one-step answer needs no board item. Inputs: operator objective, acceptance criteria, priority, owner/profile, dependencies, artifacts, mode and actual task capability. If the threshold is unavailable, decide from duration and coordination needs; do not invent a configured value.

1. Write the completion evidence before work starts. Split independent outcomes into tasks with explicit prerequisite IDs. Confirm which board is meant: Hermes Kanban and the parent Dashboard task store are separate; neither ID implies the other exists.
2. Check capability, health, auth and mode for the chosen store. `mock` uses synthetic records; `read_only` produces a proposal. `live` may create/update a parent task only through the authenticated Control API. Never infer `task.write` from this SKILL.md or an observer hook.
3. For a parent task, follow [task operations](references/task-operations.md): create with the approved field set and a stable `Idempotency-Key`; update only with a fresh version in `If-Match`. Track local acceptance criteria, dependency links and artifact evidence separately when the API has no corresponding write field. Do not smuggle them into another field.
4. After each significant transition, read the authoritative task snapshot and compare ID, version, status and evidence. On conflict or unknown mutation outcome, stop further writes and reconcile before retry. A proposed progress comment or local hook is not a parent update.
5. Set `done` only after all acceptance criteria have observed evidence and no pending approval. Otherwise use a supported nonterminal status and report blockers or partial outcome in the normalized result. Never mark an uncertain or merely drafted action complete.

Output a normalized result with the authoritative task ID only if the adapter returned it. Link source and artifact IDs, actual actions, proposed actions, verification, and unresolved gaps. The optional Hermes observer writes a local sanitized journal; it does not create or update Dashboard tasks.
