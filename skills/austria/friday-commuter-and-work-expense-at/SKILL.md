---
name: friday-commuter-and-work-expense-at
description: Assess Austrian commuting and work-expense candidates using tax-year rules and documented travel/work facts.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, commuter]
---

# friday-commuter-and-work-expense-at

## Routing

Use for Pendlerpauschale, Pendlereuro, work tools, home office, training or business trips. Do not use for family benefits.

## Inputs and capability

Inputs: Tax year, work sites, commuting days and routes, employer reimbursements, home-work pattern, receipts and travel logs. Required capability: official-web.read for current BMF guidance and any official Pendlerrechner interface when applicable; document.read handles supplied logs and receipts. mock uses synthetic journeys; read_only and live calculate supported candidates only. No employer or FinanzOnline write connector is presumed.

## Procedure

1. Confirm tax year, claimant/worker, employment periods, actual work sites, work/telearbeit days, changing routes and employer payments. Record the evidence source, covered period and hash for each log, payslip, receipt or employer statement. A planned commute is not proof it occurred.
2. Retrieve applicable BMF guidance for that year, including [Pendlerpauschale](https://www.bmf.gv.at/themen/steuern/arbeitnehmerveranlagung/pendlerfoerderung-das-pendlerpauschale/allgemeines-zum-pendlerpauschale.html), the official [Pendlerrechner](https://pendlerrechner.bmf.gv.at/) where required and [Telearbeitspauschale FAQ](https://www.bmf.gv.at/themen/steuern/arbeitnehmerveranlagung/was-kann-ich-geltend-machen/werbungskosten/home-office-pauschale.html) when relevant. Record URL, rule/effective year, update date, retrieval UTC time and source snapshot/hash. The BMF states terminology changed from Homeoffice to Telearbeit in 2025; apply the source relevant to the tax year, never a timeless label or rate.
3. Separate ordinary commute, business travel, work equipment, training and telearbeit by day, purpose and source. For commuting, capture the official calculator output/reference only when the real inputs and applicable year are known; no invented route or calculator result. For other expenses, link professional use, receipt, employer reimbursement and period.
4. Reconcile days with work calendar and employer records. Detect overlapping commute/telearbeit or business travel days, repeated receipts and amounts already paid or considered by the employer. Show each conflict before computing.
5. For each candidate output `met`/`not_met`/`unknown`, source IDs, formula/version and assumptions. Calculate only after verified rule, official calculator result where applicable and complete facts; otherwise state `amount: unknown` and request the exact missing evidence.

## Approval and failures

Do not assume a flat allowance or deductibility. No filing or employer declaration.
Missing route, work-day count, employer reimbursement or current rule means no precise amount; provide evidence checklist. Do not launch a calculator using guessed personal data, send anything to an employer or file a return.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work and blocked for missing required capability. Never put a proposal in actions_taken. Positive check: sampled days match payroll/work records, reimbursements are subtracted or flagged, and formula cites the applicable official year. Negative check: missing official calculator output, duplicate travel day, changed receipt hash, unsupported work purpose or stale rule prevents a precise claim.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
