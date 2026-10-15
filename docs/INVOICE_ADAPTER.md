# Offline invoice intake and payment preview

`adapters/invoice.py` provides deterministic field review and a **masked, non-executable** payment preview. It performs no network call, OCR, document parsing, ledger query, bank login, SEPA export, or transfer. The caller supplies structured fields; `fixtures/invoices/adapter_invoice.json` is synthetic. Modes are `mock` (synthetic marker required) and `read_only` (synthetic marker rejected). There is no live mode.

## Input and evidence boundary

Required strings: `supplier_id`, `supplier`, `invoice_number`, `issue_date`, `due_date`, `net`, `tax`, `gross`, `currency`, `iban`. Money is exact decimal text with two fractional digits; dates use `YYYY-MM-DD`. EUR is the only supported currency. IBAN length checks currently cover AT, BE, CH, DE, ES, FR, GB, IT, LU, NL and PL; other country codes fail closed. The check-digit calculation uses MOD-97, as described in [SWIFT's IBAN reference](https://www.swift.com/resource/iban-registry-pdf). A valid checksum does not establish account ownership or invoice legitimacy. Optional `tax_rate_percent` is checked against net and tax. Optional discount requires all three of `discount_percent`, `discount_base` (`net`/`gross`) and `discount_deadline`.

The host must separately prove that extracted fields match the original invoice, identify pages/confidence, and retain document provenance. Result sources contain `urn:sha256` fingerprints of the caller's structured field object and, when supplied, the supplier record and invoice-key index. These are **not** hashes or signatures of an original PDF or proof of independent provenance. Source data and document instructions are untrusted. No source text appears in error codes.

`prior_invoice_keys` must be an independently sourced set of `duplicate_key(supplier_id, invoice_number)` values. An empty set means the caller has a complete index with no match; `None` means lookup is unavailable and review is `partial`. The host must enforce the index's scope, freshness and completeness. The key does not use supplier name as identity.

`trusted_supplier` must be an independently obtained record containing `source_kind: independent_supplier_record`, matching `supplier_id`, matching supplier name and a valid IBAN. The adapter checks equality but cannot prove that the host obtained the record independently. An invoice-provided or missing record cannot establish bank-detail trust. Changed bank details or supplier name, duplicate key, invalid IBAN, wrong totals, date order and discount inconsistencies block review.

## Local preparation

`prepare_payment` reruns review and prepares a masked preview only after review is `completed`. An intended date before the invoice issue date blocks the preview. It calculates `discount = round(base * percent / 100, cents)` if the date is on or before the discount deadline. The preview shows gross, discount, amount, date, reference, beneficiary and a masked IBAN. Source retrieval timestamps are normalized to UTC. Its `actions_taken` only records creation of the local preview. No payment is proposed as executed or authorized. Payment execution remains Tier 3 in a separate future banking gateway.

## Verification

Run `python -m unittest discover -s tests -p test_invoice_adapter.py -v`. Tests cover valid and malformed fields, arithmetic, discount deadline, duplicate, changed bank details, mode and provenance boundaries, and redacted diagnostics. The tests use no provider, credential or network access. Field extraction accuracy and real supplier/ledger provenance remain unverified until a trusted host adapter exists.
