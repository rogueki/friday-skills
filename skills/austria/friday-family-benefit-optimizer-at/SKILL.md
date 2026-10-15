---
name: friday-family-benefit-optimizer-at
description: Screen Austrian family tax benefits against current official rules and documented household facts; no eligibility guarantee.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, family]
---

# friday-family-benefit-optimizer-at

## Routing

Use for family-related Austrian benefits such as Familienbonus Plus or Mehrkindzuschlag. Do not use for commuter deductions.

## Inputs and capability

Inputs: Tax year, family relationship, child ages and residence, benefit periods, household and income facts, prior claims. Required capability: official-web.read for tax-year BMF and oesterreich.gv.at guidance, plus document.read only for privately supplied family evidence. If official access is absent, use dated user-supplied official material or mark rules unverified. mock uses synthetic facts; read_only and live perform analysis only, with no claim or submission.

## Procedure

1. Find tax-year-specific BMF and oesterreich.gv.at primary guidance; capture legal effective date, publication/update date and retrieval UTC time.
2. Test each candidate benefit against documented age, household, income, claim period and co-claim facts; show missing evidence and possible overlap.
3. Return candidate matrix with rule source, conditions met/unmet/unknown, estimated amount only when official formula and inputs are verified, and review steps.

## Approval and failures

No definitive entitlement or automatic claim. Sensitive family records stay private; submission remains tier 3 elsewhere.
If current rule or relevant household fact is missing, mark candidate uncertain and do not invent rate or eligibility.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recheck each material condition against official year-specific text and source records.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
