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

Inputs: Original receipts, authorized workspace, project taxonomy, optional expense index and retention policy. Required logical capability: document.read or an actually installed local OCR parser for receipts; finance.expense-ledger.read is optional for duplicate checks. No receipt OCR, expense-ledger connector or filing adapter is implemented in this repository. mock may describe synthetic receipts; read_only may produce a one-time index only from actually readable authorized originals. Filing requires a separate verified workspace operation; a mode label alone does not provide it.

## Procedure

1. Inventory originals without modification. Record per-file source path/ID, byte hash, capture time and page/region evidence for merchant, date, gross, tax, currency and payment marker. Distinguish an OCR guess from a visually verified field; for unreadable images return `unreadable` rather than inferred values.
2. Classify only against the provided project/category taxonomy. Record a candidate category and reason with evidence; tax relevance and deductibility remain unverified until current jurisdiction-specific rules and competent review establish them. Keep mixed currencies separate and distinguish receipt, invoice, card slip and refund.
3. Check exact-byte duplicates by hash and near duplicates by merchant/date/amount/reference, but keep separate originals and flag uncertain matches for review. A card slip may document payment but not establish the underlying invoice or tax treatment.
4. Produce a proposed filing map and index with original IDs, hashes, field provenance, duplicate state and missing evidence. If a verified local filing capability is later connected, copy only to an authorized destination, verify the copy hash and retain the source; do not report a move/copy as done from a proposal.

## Approval and failures

Local reversible filing is tier 1. No tax submission. Keep payment details and personal addresses out of events.
Unreadable currency or image remains unresolved; do not silently merge near duplicates. Missing originals, unresolved refunds, conflicting project tags or absent retention rules leave filing `partial` or `blocked` as appropriate. Do not claim a persistent receipt register or scheduled missing-beleg alert without its backing adapter.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Sample index against originals, sum by currency and confirm source files remain.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
