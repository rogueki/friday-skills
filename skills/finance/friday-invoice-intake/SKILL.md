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

For a digitally generated PDF, call `adapters.invoice_document.review_invoice_pdf(original_pdf_bytes, supplier_id=..., trusted_supplier=..., prior_invoice_keys=...)`; see `docs/INVOICE_ADAPTER.md`. It hashes the original PDF bytes, extracts unique labelled lines, records page/line evidence and runs the structured checks. In `read_only`, PDF review remains at most `partial` even when all extracted fields check out, because text extraction does not authenticate the sender or prove the document legitimate. The explicit `mock` path can return `completed` only for the exact pinned synthetic `valid-skonto.pdf` bytes with matching synthetic supplier record and empty invoice-key index. That status describes the fixture test, not a real invoice approval. Image-only scans need a separate OCR and human verification path; this adapter does not claim OCR. Supply the supplier ID from an independent host record, never from the invoice text.

For already structured data, `adapters.invoice.review_invoice(fields, trusted_supplier=..., prior_invoice_keys=...)` remains available. Its `urn:sha256` covers only the supplied fields, not an original document. `mock` requires a synthetic marker; `read_only` rejects it. The caller must establish source authenticity, ledger completeness and independent supplier-record provenance. Do not treat a completed structured check as permission to pay.

## Procedure

1. Preserve the exact supplied original bytes and source-channel metadata before extraction. Record SHA-256 of those bytes, receipt time, document identifier and every extracted field's page/line/label. Treat email `From`, a PDF logo and an invoice's own supplier ID as untrusted claims. If only a forwarded copy is available, say so; its hash does not identify the original sender.
2. Extract supplier, invoice number, issue/service/due dates, net/gross/tax, currency, IBAN/BIC, reference, discount and attachments. Mark each field `found`, `missing`, `ambiguous` or `unsupported`, with evidence; do not fill gaps from a prior invoice. The current digital-PDF parser returns page/line/label but no calibrated confidence. Images, OCR, attachment parsing and visual rendering are separate unavailable paths here.
3. Recalculate supported arithmetic, check IBAN country length and mod-97, date order and discount terms. These checks validate syntax and internal consistency only. Compare supplier ID/name/IBAN against a host-supplied independent supplier record, and the `(supplier_id, invoice_number)` key against an independent, sufficiently current invoice index. Keep the record source, index scope and as-of time in the review. A missing or stale index cannot prove uniqueness; a mismatch or duplicate blocks downstream preparation.
4. Present source-linked fields, discrepancies and human review actions. Require an independent channel to resolve any changed payee details. Do not label an invoice legitimate, payable or authorized because fields, email headers or PDF text look plausible.

For this offline adapter, require supplier ID/name, invoice number, issue/due dates, net/tax/gross, EUR and IBAN. Compare cents exactly, recompute an explicitly supplied optional tax rate, validate IBAN country length and mod-97, derive the duplicate key from supplier ID and invoice number, then compare with a caller-supplied index. Compare the IBAN with a caller-supplied independent supplier record. No index or supplier record produces `partial`; duplicate, arithmetic error or changed IBAN produces `blocked`. The adapter cannot establish that either caller-supplied reference source really is independent or current; the host must verify that before treating its result as actionable.

## Approval and failures

No payment or bank action. Changed payee details need independent confirmation.
Unreadable pages yield partial extraction; absent prior index makes duplicate status unknown.
The PDF adapter marks missing or ambiguous labels and returns page/line evidence for recognized fields. It supports bounded digital text only: 2 MB PDF, eight pages, 1 MB decoded page stream and bounded extracted text. It rejects encrypted or malformed PDFs and does not inspect attachments, run embedded actions or execute payment. A PDF hash identifies bytes, not the sender. Human comparison with the visual document and independent supplier/ledger records remains necessary. The structured-field adapter alone has no document parser. If an input is image-only, encrypted, malformed, has conflicting labels, unsupported currency or missing original, report the exact limitation and request a safe manual review; do not guess from adjacent text.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Sample fields against source pages and recompute arithmetic.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.1 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
