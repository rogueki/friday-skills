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

1. Check official BMF rules and any applicable official commuter calculator for the tax year; record effective/update/retrieval dates.
2. Separate commuting, work equipment, home office, training and business travel; match each claim to days, route, necessity, employer payment and receipts.
3. Calculate only supported candidates with formula and assumptions; flag overlapping reimbursements and unresolved commuting facts.

## Approval and failures

Do not assume a flat allowance or deductibility. No filing or employer declaration.
Missing route, work-day count, employer reimbursement or current rule means no precise amount; provide evidence checklist.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Reconcile claimed periods to work calendar and sample travel/receipts; tie formulas to official sources.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
