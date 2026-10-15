---
name: friday-tax-review-at
description: Review an Austrian tax draft for evidence coverage, double counts and tax-year rule currency before human sign-off.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, tax]
---

# friday-tax-review-at

## Routing

Use for final quality review of an assembled tax draft. Do not use for first document intake or FinanzOnline submission.

## Inputs and capability

Inputs: Tax year, complete draft, source index, calculations, current official rule citations, unresolved questions and user review status. Required capabilities: document.read for the completed draft/source index and official-web.read for tax-year BMF rules, or dated official copies with provenance. mock reviews synthetic cases; read_only and live produce a local gate report only. No FinanzOnline submit capability is inferred.

## Procedure

1. Freeze the reviewed draft revision and source index. Confirm owner, residency, tax year, filing type and scope against intake. For every material entry trace draft position -> category decision -> calculation -> evidence ID/hash/owner/period -> applicable official BMF rule snapshot. Record URL, covered/effective year, issue/update date and retrieval UTC time. An unverified current rule is a finding, not a silent pass.
2. Recompute totals independently from evidence, preserving source amounts separately from proposed tax amounts. Find duplicate IDs/hashes, overlapping claimant/child periods, employer reimbursements already considered, missing receipts, inconsistent dates or currencies, and mismatches between source and draft. Sample high-value entries plus every disputed/unknown item; record coverage, not just a generic `checked` flag.
3. Compare family and commuter candidate outputs with the draft: `unknown` and `candidate` must never become verified entitlement or precise deduction without source-backed condition review. Check the applicable year's official form guidance only as documentary context; do not assert current FinanzOnline field IDs from a demo or a stale copy.
4. Return a gate table per entry with `verified`, `needs_correction`, `needs_professional_review` or `unresolved`, evidence/rule references and owner action. Separate factual reconciliation from legal interpretation. Produce a human-review checklist; preserve the original draft and all findings so corrections can be compared by revision.
5. Mark ready for **human review** only when all material evidence and year-specific rule sources are current, totals reconcile and no unresolved issue remains. Record who reviewed which revision and when, if supplied. Human sign-off is not tax authority acceptance, submission, or legal certainty.

## Approval and failures

No submission. Filing is tier 3 and requires a real adapter, hard approval and second factor.
Absent source, outdated rule, changed evidence hash, unresolved double count or missing user review blocks ready-for-review status; preserve draft with findings. No login, upload, approval proposal for submit or submission occurs here. A `Tier 3` path would belong to a separate verified host workflow with hard approval and second factor.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for usable findings and blocked for missing required capability. Never put a proposal in actions_taken. Positive check: source-to-draft links, hashes, tax year, official source snapshots and independent totals match; all material gates are resolved before human-review-ready. Negative check: changed hash, missing receipt, duplicate, year mismatch, stale rule, uncertain form schema or sum mismatch yields explicit findings and never a filing-ready or submitted state. `adapters/austria_tax_e2e_mock.py` is synthetic evidence of a non-executable checklist only.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.6 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
