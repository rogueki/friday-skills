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

Inputs: Project type (energy, renovation, heating, PV/storage, family, mobility or relevant digitalization), municipality/state, applicant type, budget, intended order/project start and submission window. Required capability: `official-web.read` for federal, state and municipal program pages. The Austrian [Transparenzportal](https://transparenzportal.gv.at/tdb/tp/startpage) is a discovery index; the responsible institution's exact program page/rules decide current terms. The installed capability manifest reports no live or mock official-web adapter. A supplied URL or general web result is only a lead until independently checked against official program evidence. The synthetic `example.invalid` grant fixture is test data, never a real listing. This skill produces a shortlist only.

## Procedure

1. Normalize applicant status, exact municipality/land, project category, eligible cost estimate and dates; ask for missing decision-critical facts. Search Transparenzportal plus relevant federal, land and municipal institutions. Record search date and coverage, including levels not checked; do not treat a catalog hit as an active call.
2. Open each responsible institution's program-specific rules and application notice. Record program name/ID and version, institution, geographic scope, applicant target group, eligible project/costs, start/order-before-application condition, funding amount or formula/cap, deadlines, available-budget/exhaustion status, stacking/combination rules, required evidence, page publication/update and retrieval UTC timestamp. Attach a direct source to each decisive field, and distinguish a rule's effective date from the page's update date.
3. Classify each candidate `potential_match`, `ruled_out` or `unverified`. A known closed call, wrong region/group or excluded project is ruled out with the exact rule. Missing current call, funds, deadline or authoritative rule is unverified; never promote it to `open` or `eligible` from a cached or secondary page. Rank only candidates whose critical fit conditions are evidenced, and show unresolved conditions separately.
4. Output a per-program table with all §16.1 fields, exact links, last check, reason for rank, missing documents and next verification action. Explicitly note federal/land/municipal search gaps; avoid implying exhaustive coverage.

## Approval and failures

No application, purchase or contractor engagement. Do not rely on blogs as primary evidence.
If official page is unavailable, outdated or conflicts with a catalog, preserve the discrepancy and do not claim the program is open. If `official-web.read` is unavailable, return `blocked` for a current search; a locally supplied page can be analyzed as unverified material, not silently upgraded to live research.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work and blocked for missing required capability. Never put a proposal in actions_taken. Re-open shortlisted official rules and cross-check deadline, geographic scope, applicant type and live call status at the stated retrieval time. A shortlist is not a funding decision.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.1 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
