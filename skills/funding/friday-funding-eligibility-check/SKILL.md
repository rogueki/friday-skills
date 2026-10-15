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

Inputs: Named program and rule version, applicant profile/legal form, project and site, itemized quote/costs, order/start/application dates, permits and evidence. Required capabilities: `official-web.read` for the responsible institution's current program rules and `document.read` for supplied project evidence; both are currently unavailable as live/mock adapters in the capability manifest. The `example.invalid` heat-pump fixture checks only a synthetic contract. Output is a provisional decision matrix, never official eligibility, reserved funds or an application.

## Procedure

1. Resolve the exact funding institution, program ID/version and effective rules from its page and documents. Check whether the current call is accepting applications, deadline and budget availability separately; a general Transparenzportal listing or historical PDF does not prove these. Record retrieved-at UTC and conflicts between sources. If the program was merely suggested by a scout, first verify the responsible institution's page.
2. Build a row per rule: rule text/link/version; applicant, address/land, project type, technical parameters, eligible vs excluded cost lines, minimum/maximum, quote/permit/evidence, order/start/payment/application sequence, submission window, stacking/de-minimis or other combination restrictions where applicable; matched project document and exact page/field; status `met`, `unmet`, `unknown`, or `not_applicable`, with reason. Avoid treating absence of evidence as an adverse fact.
3. Evaluate negative paths first: wrong region or applicant class, excluded technology, closed call, deadline passed, prohibited prior order/start, and incompatible funding. A decisive `unmet` rule means not eligible under the checked version; an `unknown` critical rule means no positive conclusion. Show possible programs only as separately sourced leads, routed to the scout for discovery.
4. Return a provisional fit statement only when all critical rules are evidenced, along with unknowns, missing documents, timing hazards, source/version, and the next safe step (ask institution, obtain document, or prepare draft). Recheck call and rules immediately before any later application process.

## Approval and failures

No application, contract signature or purchase. External filing needs actual adapter and approval by its action tier.
Unclear start/order-date rule, missing official program document, unknown funding availability or contradictory evidence prevents a positive conclusion. If either required read capability is unavailable, return `blocked`; supplied evidence may be reviewed locally with an explicit freshness gap. No application connector or filing is installed.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for a useful but inconclusive matrix, blocked for missing required capability, and never put proposals in actions_taken. Trace every `met` condition to both official rule and project evidence. Verify dates and arithmetic independently; `potential_fit` in the synthetic test fixture is not an Austrian program approval.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.2 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
