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

1. Resolve the named scene to a reviewed, versioned definition from a trusted scene store. Enumerate exact controller, control ID, kind, unit, command and target value for every step. Reject opaque macros, unknown controls, conflicting commands and hidden door, lock, alarm or access effects. No scene-definition store or native Loxone write adapter is currently implemented here.
2. Read fresh pre-state for every target, then check safe ranges, occupants, comfort limits and cross-device conflicts. Preview a per-device before/after table, expected order, partial-failure impact and recovery steps. A room name or generic scene label cannot stand in for the full action list.
3. Treat definition edit and activation as separate actions. Definition edits need reviewed version change and a real storage adapter. Activation needs an action-bound Tier 2 approval covering the exact scene version and fingerprint of *all* commands; revalidate the version, pre-states, health and grant immediately before dispatch. An approval for an earlier scene version is invalid.
4. A future host-owned live adapter must dispatch idempotently and retain a per-device journal. After each command, read back that exact device with a newer timestamp. On unknown outcome, stop rather than replay. If any target is unconfirmed, return partial with the list of applied, failed and unknown steps and a safe recovery proposal; never call the whole scene successful from one acknowledgement. Confirm success only when every target matches.

## Approval and failures

Mock/read_only may preview only. A scene is not approval for unseen changes. Security-critical devices are outside scope.
Partial execution requires explicit per-device outcome and safe rollback proposal; never report whole scene success on one acknowledgement.
The E2E8 mock covers one light only; it is not a multi-device scene test or a live-control proof.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Compare post-state of each device to intended scene; retain scene version and action fingerprint.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 17.5 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
