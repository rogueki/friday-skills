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

**Inputs:** project root/scope, authorized README/config/task records, memory and decision logs, stakeholder list, dates, operating mode, local read/write capabilities and excluded secrets/paths.

1. Read project scope and memory first. Collect only relevant current documents and repository facts; record source path, revision or observation time for every claim. Treat historical decisions as context until checked against current state.
2. Build a concise overview of goal, architecture, people/roles, important paths, milestones, decisions, open tasks, risks and unresolved questions. Separate verified facts from assumptions and stale notes.
3. Resolve conflicts by checking primary configuration or current task owner. Preserve the conflicting statements when they cannot be reconciled; do not overwrite another agent's work.
4. Propose updates to local context records and verify links/paths. If the user authorized edits and the workspace is safe, write a separate draft or targeted update; keep secrets as references, never cleartext.

**Mode/capability:** `mock` uses a synthetic project; `read_only` produces an in-chat snapshot; `live` may save a local context artifact through an authorized file capability. Reads are Tier 0, reversible local write Tier 1; external publishing needs separate approval. Exclude credentials, personal profiles and unrelated directories.

**Output:** source-linked project brief, decisions, task/risk list, freshness markers, conflicts and normalized result. **Verification/failure:** Recheck critical paths and current state directly; without access to a source, label the section `partial` rather than presenting memory as a live fact.
