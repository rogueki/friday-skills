---
name: friday-austria-funding-scout
description: Find current Austrian funding programs by region and project with official dated source evidence; no application.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, funding, austria]
---

# friday-austria-funding-scout

## Routing

Use to discover possible federal, state or municipal funding. Do not use to decide one applicant's final eligibility.

## Inputs and capability

Inputs: Project type, municipality/state, applicant type, budget, intended start and submission window. Required capability: official-web.read for federal, state and municipal program pages; a general web fetch may only support discovery, not replace official evidence. mock uses synthetic program pages; read_only and live research and draft a shortlist only. No application adapter is presumed.

## Procedure

1. Search official federal, state and municipality program pages for the project class; capture publisher, effective period, page update and retrieval UTC date.
2. For each program extract institution, region, target group, prerequisites, amount/formula, deadline, combinability and required documents with direct source.
3. Filter closed or inapplicable programs and rank remaining candidates by fit; mark unknown budget, availability or funding exhaustion.

## Approval and failures

No application, purchase or contractor engagement. Do not rely on blogs as primary evidence.
If official page is unavailable or stale, do not claim the program is open; list verification gap.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Open every shortlisted official source and cross-check deadline, region and applicant type.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.1 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
