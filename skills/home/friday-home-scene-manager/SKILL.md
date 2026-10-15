---
name: friday-home-scene-manager
description: Review or activate allowlisted Loxone scenes with explicit state preview and approval; no hidden access changes.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, home, home]
---

# friday-home-scene-manager

## Routing

Use for named home scenes such as home, away, night or focus. Do not use for a single light setpoint or read-only status.

## Inputs and capability

Inputs: Scene definition/version, exact device IDs and commands, current state, occupants, rollback plan and approval. Required capabilities: loxone.read for the exact scene version and pre/post device states, plus loxone.write for every allowlisted scene command. A separate scene-definition storage adapter is needed for edits; none is assumed installed. mock previews synthetic states, read_only previews real states, and live activation needs tier 2 approval bound to the full scene fingerprint.

## Procedure

1. Resolve named scene to reviewed version and enumerate every affected device; reject opaque commands, unknown IDs and hidden lock/alarm/access effects.
2. Read current states and evaluate safe ranges, occupant context and conflicts. Present a complete per-device change preview and rollback.
3. For definition edits, require review before saving. For activation, require tier 2 action-specific approval and live adapter; apply idempotently and read back each affected state.

## Approval and failures

Mock/read_only may preview only. A scene is not approval for unseen changes. Security-critical devices are outside scope.
Partial execution requires explicit per-device outcome and safe rollback proposal; never report whole scene success on one acknowledgement.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Compare post-state of each device to intended scene; retain scene version and action fingerprint.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.5 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
