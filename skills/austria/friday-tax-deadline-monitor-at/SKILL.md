---
name: friday-tax-deadline-monitor-at
description: Track Austrian tax filing, response and appeal deadlines from dated official rules and case-specific notices.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, tax]
---

# friday-tax-deadline-monitor-at

## Routing

Use for tax due dates and notice windows. Do not use for invoice due dates or final return quality review.

## Inputs and capability

Inputs: Tax type/year, filing channel, notice or Bescheid delivery dates, advisor status, jurisdiction and scheduler capability. Required capabilities: official-web.read for current BMF rules and document.read for case-specific notices; scheduler.run and notification.deliver are separate requirements for an ongoing watch. mock uses synthetic notices, read_only returns a one-time timeline, and live may schedule only through verified hooks. No filing adapter is presumed.

## Procedure

1. Read current official BMF/oesterreich.gv.at deadline rules and case-specific notices; record legal applicability and retrieval time.
2. Compute each deadline from the correct trigger and calendar convention; distinguish statutory date, extension and user-specific notice date.
3. Return prioritized timeline and evidence. Recurring alerts require actual scheduler/hook, deduplication and protected notification target.

## Approval and failures

No automated submission or appeal. A reminder is not legal proof of timely receipt.
Unknown service date or conflicting extensions means provisional deadline and urgent verification, not a fabricated date.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recalculate triggers and compare to authoritative notice/rule; verify scheduler acknowledgement before claiming monitoring.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.5 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
