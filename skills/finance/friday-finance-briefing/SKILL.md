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

Inputs: Period/as-of date, invoice ledger, subscription list, receipt completeness and currency rules. Required logical read capabilities are finance.invoice-ledger.read, finance.subscription-ledger.read and finance.receipt-index.read for the corresponding sections. These live feeds are not implemented in this repository. Missing feeds stay marked unavailable; fixtures must be labelled synthetic. read_only or live may describe only data actually supplied by a trusted host; neither mode authorizes a transfer, dashboard delivery or investment decision.

## Procedure

1. Define the reporting period, as-of instant, time zone, currency and source coverage. For each supplied feed record its identity, fetch time, status freshness and completeness. Label absent or stale ledger, subscription and receipt feeds per section before calculating anything.
2. Deduplicate invoices by supplier ID and invoice number across feeds; exclude paid, void, disputed and ambiguous rows from open totals. Keep original currency totals separate; conversion needs an explicitly sourced rate and date. Recompute sampled totals from source rows and show item counts.
3. Group open/overdue invoices, documented discount windows, recurring obligations, unusual movements and missing receipts. Calculate a period comparison only when definitions and coverage match; cite the baseline, denominator and threshold for each anomaly. Distinguish a contractual recurring amount from a charged payment and a projected obligation from a booked expense.
4. Produce a ranked brief with at most a few urgent decisions, source-linked totals, gaps and proposed follow-ups. State whether each section is verified, partial or unavailable. Do not turn a missing feed into zero, claim a dashboard card/notification was delivered, or give investment advice.

## Approval and failures

Analysis is tier 0, local brief tier 1. No transfers or investment recommendations.
If one feed is offline, keep independent sections and mark overall result partial. If all required sources are absent, return blocked with a missing-capability list rather than a fabricated briefing. Legal/tax/financial claims require a current dated source; do not present inferred deductions or payment deadlines as official rules.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Trace sample totals to ledgers and check no invoice is counted twice.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.5 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
