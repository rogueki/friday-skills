---
name: friday-invoice-intake
description: Extract and validate supplied invoices, flag duplicates and changed bank details; use before payment preparation.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, finance, invoice]
---

# friday-invoice-intake

## Routing

Use for invoice extraction and review. Do not use for receipts without an invoice obligation or for executing payment.

## Inputs and capability

Inputs: Original invoice, source channel, hash, prior invoice index and independent supplier details where available. Required logical capabilities: document.read for the original PDF/image and, for duplicate checks, finance.invoice-ledger.read; supplier-record lookup is optional but required before calling changed bank details verified. These IDs describe needed adapters, not installed connectivity. mock uses synthetic invoices; read_only reads authorized originals; live adds no payment permission.

The executable offline contract is `adapters.invoice.review_invoice(fields, trusted_supplier=..., prior_invoice_keys=...)`; see `docs/INVOICE_ADAPTER.md`. It accepts **caller-supplied structured fields only**, not PDF, image, OCR or mail text. `mock` requires an explicit synthetic marker; `read_only` rejects that marker. The caller must establish source authenticity, document-to-field provenance, ledger completeness and independent supplier-record provenance. The returned `urn:sha256` covers the structured input, not the original invoice.

## Procedure

1. Extract supplier, invoice number, issue/service/due dates, net/gross/tax, currency, IBAN/BIC, reference, discount and attachments with page and confidence.
2. Recalculate totals and tax; check IBAN syntax, date order, duplicate keys and bank-detail changes against an independently trusted supplier record.
3. Present discrepancies, unresolved fields and review priority. Valid formatting never establishes legitimacy.

For this offline adapter, require supplier ID/name, invoice number, issue/due dates, net/tax/gross, EUR and IBAN. Compare cents exactly, recompute optional tax rate, validate IBAN country length and mod-97, derive the duplicate key from supplier ID and invoice number, then compare with an independently supplied index. Compare the IBAN with an independently supplied supplier record. No index or supplier record produces `partial`; duplicate, arithmetic error or changed IBAN produces `blocked`.

## Approval and failures

No payment or bank action. Changed payee details need independent confirmation.
Unreadable pages yield partial extraction; absent prior index makes duplicate status unknown.
The offline adapter cannot detect unreadable pages because it has no document parser; the host must mark extraction confidence and source-page evidence separately. Do not represent its structured-field checks as original-document verification.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Sample fields against source pages and recompute arithmetic.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.1 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
