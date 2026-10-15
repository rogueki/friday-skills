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

Inputs: Signed contract and amendments, invoices, notice terms, jurisdiction/time zone, optional scheduler. Required logical capabilities: document.read for signed contracts and finance.subscription-ledger.read for billed charges; scheduler.run is needed for continuing checks. This repository has no contract-record store, subscription-ledger reader, scheduler or notice sender. Synthetic records can demonstrate a one-time timeline; real read_only output requires actually supplied signed documents and revisions. A `live` mode label does not activate monitoring.

## Procedure

1. Inventory the signed base contract, accepted amendments, notices and invoices. Record document ID/hash, signature or effective date, version order and page/clause for each party, tariff, price, renewal, cancellation window and notice channel. Mark an unsigned quote or marketing page as unverified terms.
2. Resolve amendment precedence and calculate candidate renewal and notice dates from cited clauses. State jurisdiction, calendar/time zone, receipt-vs-send rule and any business-day assumptions; if wording is unclear, show alternatives and ask for legal review instead of asserting a deadline. No current legal rule or mandatory notice form is inferred from the contract title.
3. Compare billed amounts only for the same tariff, billing period, tax basis and currency. Show old/new source amounts and effective date; flag missing invoices or unexplained differences without claiming an unauthorized price change.
4. Provide a one-time timeline and, if asked, a proposed cancellation draft bound to the exact contract revision and recipient. Continuing checks need a verified persistent register, scheduler, deduplication and delivery receipts; otherwise mark monitoring/alerts `NOT_CONFIGURED`.

## Approval and failures

Sending notice is tier 2; signing or switching a contract is tier 3 with real adapter and hard approval.
Missing signed copy, conflicting amendments, uncertain receipt date or absent ledger make dates provisional; legal ambiguity needs human review. Sending notice remains a separate tier-2 action with explicit recipient/content approval and an installed sender. Unknown delivery outcome must be reconciled before retrying; a drafted notice is not a cancellation.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Tie each date to a source clause and recompute calendar arithmetic.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.6 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
