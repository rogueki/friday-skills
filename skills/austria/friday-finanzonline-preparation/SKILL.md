---
name: friday-finanzonline-preparation
description: Map reviewed Austrian tax evidence to current FinanzOnline fields and produce a submission checklist; draft only.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, finanzonline]
---

# friday-finanzonline-preparation

## Routing

Use after tax intake to prepare field mappings. Do not use for researching family benefit eligibility or submitting a return.

## Inputs and capability

Inputs: Tax year, reviewed case file, current official form/instructions, evidence references and user-selected filing type. Required capabilities: document.read for reviewed case evidence and official-web.read for current BMF/FinanzOnline forms or user-supplied official copies with provenance. These are requested interfaces, not installed connectors. mock uses synthetic forms, read_only prepares local field mapping, and live remains draft-only; no finanzonline.submit call is made.

## Procedure

1. Verify current field labels and instructions from official BMF/FinanzOnline material; record publication date and retrieval UTC time.
2. Map each proposed value to field and evidence with calculation, tax year and uncertainty; distinguish blank, zero and not applicable.
3. Create a reviewable local export/checklist, reconcile totals and show unresolved entries before any possible filing.

## Approval and failures

Actual FinanzOnline submission is tier 3 with hard approval and second factor through a real adapter; this skill never submits.
Unavailable current forms or conflicting field definitions block a final mapping and require manual review.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Cross-check form version, field IDs and sums against official instructions and source evidence.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.2 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
