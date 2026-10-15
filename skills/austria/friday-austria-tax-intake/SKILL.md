---
name: friday-austria-tax-intake
description: Build an evidence-linked Austrian tax case inventory and missing-document list; no filing or eligibility ruling.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, austria]
---

# friday-austria-tax-intake

## Routing

Use to collect Austrian tax inputs. Do not use for final return review or FinanzOnline field entry.

## Inputs and capability

Inputs: Tax year, residency/jurisdiction, income records, employer forms, family, commuting, work expenses, special expenses and receipts. Required logical capability: document.read or an available local parser for supplied evidence; no tax-account connector is assumed. mock uses synthetic tax files, read_only builds a private local index, and live still only prepares the case file. FinanzOnline access and submission are outside this workflow.

## Procedure

1. Inventory supplied documents by tax year and owner; separate original evidence from user statements and check coverage.
2. Map evidence to possible income, family, commuting, work expense and exceptional-burden categories without asserting deductibility.
3. Produce a case file index, missing items and questions for tax review; mark uncertain jurisdiction or year.

## Approval and failures

Keep personal tax data only in authorized private storage. No FinanzOnline login or submission.
Missing tax year, residency or key income document blocks a complete case, but a partial inventory may be returned.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Trace each category to source document and confirm totals are not duplicated.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.1 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
