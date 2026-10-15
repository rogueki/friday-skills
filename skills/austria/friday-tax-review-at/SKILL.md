---
name: friday-tax-review-at
description: Review an Austrian tax draft for evidence coverage, double counts and tax-year rule currency before human sign-off.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, tax]
---

# friday-tax-review-at

## Routing

Use for final quality review of an assembled tax draft. Do not use for first document intake or FinanzOnline submission.

## Inputs and capability

Inputs: Tax year, complete draft, source index, calculations, current official rule citations, unresolved questions and user review status. Required capabilities: document.read for the completed draft/source index and official-web.read for tax-year BMF rules, or dated official copies with provenance. mock reviews synthetic cases; read_only and live produce a local gate report only. No FinanzOnline submit capability is inferred.

## Procedure

1. Check every material entry against source, tax year, period and current official BMF rule; record rule effective and retrieval dates.
2. Reconcile income and deduction totals, identify duplicate expenses, missing receipts, unsupported assumptions and contradictions.
3. Produce a gate list: verified, needs correction, needs professional review and user sign-off. Final status is not tax authority acceptance.

## Approval and failures

No submission. Filing is tier 3 and requires a real adapter, hard approval and second factor.
Absent source, outdated rule or unresolved double count blocks ready-for-review status; preserve draft with findings.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Independent arithmetic spot checks and source-to-field trace for high-value entries.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.6 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
