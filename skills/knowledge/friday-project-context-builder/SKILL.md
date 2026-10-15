---
name: friday-project-context-builder
description: Build a source-linked project context snapshot covering goals, stakeholders, decisions, tasks, timeline and risks.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, knowledge, project]
---

# Project context builder

Use to orient a new collaborator or resume a project from authorized material. Do not infer a live system state from an old memory file or silently replace the project's existing instructions.

**Inputs:** explicit project root and scope, authorized README/config/repository/task/decision records, known owners, observation time, excluded paths, operating mode and actual read/write capabilities.

1. Read `MEMORY.md` then `SCOPE.md` when present, and use the project's current source/configuration and task system for verification. Keep historical notes as dated claims. Do not broaden the scan to other projects, user profiles, secret files or whole drives. Record path/URI, revision or record ID, retrieval time and authority for each important fact.
2. Construct a compact map of goals, architecture, stakeholders by role, documents, decisions, open tasks with owners/status, timeline and risks. Distinguish *verified now*, *reported in a source*, *inference* and *unknown*. A repository commit proves its own contents, not a live deployment or a person's availability.
3. Reconcile contradictions by source authority and time: current scope and direct configuration, then signed/owned decisions and current task records, then old memory/notes. Show both sides when a decision, deadline or task owner still conflicts; route the issue to its owner rather than silently choosing one. Do not overwrite instructions or another agent's work.
4. Draft only targeted context updates with a cited before/after diff, preserving earlier decisions and task history. Recheck links, paths and key current-state claims before saving through an authorized local writer. Keep credential references without secret values; redact personal data outside the stated scope.

**Mode/capability:** `mock` uses synthetic project records; `read_only` returns a snapshot; `live` requires a verified local file writer and a conflict-safe update path. This package has no general project-context collection/synchronization adapter; `MEMORY.md` is context, not a verified live feed. Reads are Tier 0, reversible local draft/update Tier 1. Publishing to an external knowledge base or task system requires its own capability and approval.

**Output:** project brief with cited facts and freshness, decision/task timeline, conflicts, unresolved owner questions, proposed edits and normalized result. **Verification/failure:** Directly recheck critical paths/configs and source revisions; absent or stale evidence is marked `partial` or `unknown`, with no invented live state.
