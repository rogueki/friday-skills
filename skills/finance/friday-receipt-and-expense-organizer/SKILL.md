---
name: friday-receipt-and-expense-organizer
description: Classify receipts by merchant, project and category with duplicate evidence; not a tax entitlement decision.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, finance, receipt]
---

# friday-receipt-and-expense-organizer

## Routing

Use to organize receipt batches. Do not use for formal invoice validation or definitive deductibility decisions.

## Inputs and capability

Inputs: Original receipts, authorized workspace, project taxonomy, optional expense index and retention policy. Required logical capability: document.read or an available local OCR parser for receipts; finance.expense-ledger.read is optional for duplicate checks. mock handles synthetic receipts; read_only reads authorized originals and makes a local index; live may only perform explicitly authorized reversible filing in the workspace, never a tax or banking action.

## Procedure

1. Inventory originals without modification; extract merchant, date, gross/tax, currency and payment marker with location and confidence.
2. Classify by agreed project/category; flag duplicate hash or merchant/date/amount and missing proof. Tax relevance is a candidate label.
3. Produce an index and proposed filing map; copy or rename only within authorized local workspace while preserving originals.

## Approval and failures

Local reversible filing is tier 1. No tax submission. Keep payment details and personal addresses out of events.
Unreadable currency or image remains unresolved; do not silently merge near duplicates.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Sample index against originals, sum by currency and confirm source files remain.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
