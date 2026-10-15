---
name: friday-funding-eligibility-check
description: Check a specific Austrian funding candidate against documented applicant and project facts; no approval guarantee.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, funding, funding]
---

# friday-funding-eligibility-check

## Routing

Use after a program is identified to assess a particular project's fit. Do not use for broad discovery or submitting an application.

## Inputs and capability

Inputs: Program/version, applicant type, address/region, project scope, quotes/costs, start dates, permits and official rules. Required capabilities: official-web.read for the named program's current rule/version and document.read for supplied project evidence. mock checks synthetic programs; read_only and live issue a provisional matrix only. No grant-application or contractor-purchase adapter is assumed.

## Procedure

1. Verify the official program version, effective dates, available budget status and exclusion rules at review time.
2. Build a requirement matrix comparing applicant, site, cost, start/contract dates, technical specifications and combining rules to evidence.
3. Classify each condition met, unmet or unknown; return likely fit, missing documents and next safe step without promising funding.

## Approval and failures

No application, contract signature or purchase. External filing needs actual adapter and approval by its action tier.
Unclear start-date rule or absent official program document prevents positive eligibility conclusion.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Trace every met condition to both official rule and project evidence; revisit live availability before action.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.2 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
