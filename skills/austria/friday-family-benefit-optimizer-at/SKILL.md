---
name: friday-family-benefit-optimizer-at
description: Screen Austrian family tax benefits against current official rules and documented household facts; no eligibility guarantee.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, family]
---

# friday-family-benefit-optimizer-at

## Routing

Use for family-related Austrian benefits such as Familienbonus Plus or Mehrkindzuschlag. Do not use for commuter deductions.

## Inputs and capability

Inputs: Tax year, family relationship, child ages and residence, benefit periods, household and income facts, prior claims. Required capability: official-web.read for tax-year BMF and oesterreich.gv.at guidance, plus document.read only for privately supplied family evidence. If official access is absent, use dated user-supplied official material or mark rules unverified. mock uses synthetic facts; read_only and live perform analysis only, with no claim or submission.

## Procedure

1. Confirm tax year, claimant/residency, each child's identity and month-by-month relevant household/benefit periods. Keep child identifiers private. Separate facts proved by official records, household statements and missing facts; do not infer family-benefit receipt from a child's age alone.
2. Retrieve primary guidance for the *tax/benefit year*, including the BMF [Familienbonus Plus](https://www.bmf.gv.at/themen/steuern/arbeitnehmerveranlagung/steuertarif-steuerabsetzbetraege/familienbonus-plus.html) and [Steuerabsetzbeträge](https://www.bmf.gv.at/themen/steuern/arbeitnehmerveranlagung/steuertarif-steuerabsetzbetraege/uebersicht-steuerabsetzbetraege.html-1). Record exact URL, covered year, publication/update or effective date when stated, retrieval UTC time and a source snapshot/hash. A general page for another year is a lead, not proof.
3. Build separate candidate rows for Familienbonus Plus, Mehrkindzuschlag, childcare-related items and other relevant family measures. For each, list year-specific rule conditions, evidence IDs, `met`/`not_met`/`unknown`, any overlapping benefit or co-claim, and a precise question for the owner. Childcare receipts alone do not prove tax deductibility.
4. Check claimant/co-claimant allocation and benefits already considered by an employer or previous filing, without assuming household members may disclose each other's data. Flag duplicates across children, parents, periods and other tax skills. The BMF guidance notes that a Familienbonus Plus considered by an employer still needs separate attention in the annual assessment; verify the applicable year before acting.
5. Estimate a candidate effect only when the official formula for that year, tax context and every necessary input are verified. Label the arithmetic as an estimate and distinguish tax reduction from cash benefit. Otherwise use `amount: unknown`; never promise entitlement or refund.

## Approval and failures

No definitive entitlement or automatic claim. Sensitive family records stay private; submission remains tier 3 elsewhere.
If current rule or relevant household fact is missing, mark candidate uncertain and do not invent rate or eligibility. A conflicting parent claim, missing benefit period or out-of-year source requires review; no claim, payroll change or filing action follows.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work and blocked for missing required capability. Never put a proposal in actions_taken. Positive check: each candidate cites the right year's official rule and owner-bound period evidence, with co-claims reconciled. Negative check: unknown receipt period, unverified rule, contradictory allocation or duplicate benefit keeps eligibility and amount undetermined.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
