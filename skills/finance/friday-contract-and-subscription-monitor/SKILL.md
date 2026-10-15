---
name: friday-contract-and-subscription-monitor
description: Extract renewal, cancellation and price-change terms from supplied contracts; monitor only with a scheduler.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, finance, contract]
---

# friday-contract-and-subscription-monitor

## Routing

Use for contract timelines and notice dates. Do not use for comparing energy offers or purchasing a new plan.

## Inputs and capability

Inputs: Signed contract and amendments, invoices, notice terms, jurisdiction/time zone, optional scheduler. Required logical capabilities: document.read for signed contracts and finance.subscription-ledger.read for billed charges; scheduler.run is needed for continuing checks. mock uses synthetic contracts, read_only produces a one-time timeline and draft, and live may monitor only through a configured scheduler. No notice sender or contract-signing adapter is presumed.

## Procedure

1. Extract parties, term, renewal, notice, price clauses and version with clause/page evidence.
2. Calculate relevant notice dates with assumptions; compare invoiced prices and flag unclear changes.
3. Provide timeline or cancellation draft. A recurring monitor requires configured scheduler and deduplication.

## Approval and failures

Sending notice is tier 2; signing or switching a contract is tier 3 with real adapter and hard approval.
Missing signed copy or conflicting amendments make dates provisional; legal ambiguity needs human review.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Tie each date to a source clause and recompute calendar arithmetic.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.6 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
