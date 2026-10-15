---
name: friday-finance-briefing
description: Summarize verified payables, discounts, recurring costs and anomalies for a chosen period; not investment advice.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, finance, finance]
---

# friday-finance-briefing

## Routing

Use for cross-source finance overview. Do not use for one invoice's deadline alert or vendor alternative research.

## Inputs and capability

Inputs: Period/as-of date, invoice ledger, subscription list, receipt completeness and currency rules. Required logical read capabilities are finance.invoice-ledger.read, finance.subscription-ledger.read and finance.receipt-index.read for the corresponding sections. Missing feeds stay marked unavailable. mock aggregates synthetic records; read_only or live may read only configured feeds and create a local brief; neither mode authorizes a transfer.

## Procedure

1. Reconcile feed timestamps, statuses and currencies; state gaps before aggregating.
2. Group open/overdue invoices, near discounts, commitments, unusual movements and missing evidence; compare like periods only.
3. Write a ranked brief with totals, source counts, uncertainty and next review tasks; separate fact from projection.

## Approval and failures

Analysis is tier 0, local brief tier 1. No transfers or investment recommendations.
If one feed is offline, keep independent sections and mark overall result partial.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Trace sample totals to ledgers and check no invoice is counted twice.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.5 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
