---
name: friday-skonto-and-due-date-monitor
description: Prioritize open invoice due dates and documented skonto windows; schedule checks only with a real hook.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, finance, skonto]
---

# friday-skonto-and-due-date-monitor

## Routing

Use for imminent invoice deadline or skonto review. Do not use for a broad finance briefing or payment execution.

## Inputs and capability

Inputs: Open invoice ledger with status/as-of time, due/discount dates and terms, time zone, optional scheduler. Required logical capability: finance.invoice-ledger.read for current unpaid status; scheduler.run and notification.deliver are additional, separately verified requirements for recurring alerts. mock reads synthetic ledger rows, read_only produces a one-time report, and live may schedule only through configured hooks; none of these modes grants payment execution.

## Procedure

1. Select unpaid and undisputed invoices; deduplicate by identity and reconcile latest status.
2. Calculate days to due and documented discount deadlines in the stated time zone; rank potential savings by date and amount.
3. Return one-time alerts. Ongoing checks require configured scheduler or hook and deduplication window.

## Approval and failures

No automatic payment or invented reminder delivery. A scheduler is a separate capability.
Stale ledger or ambiguous discount base produces partial results without precise savings claims.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recalculate boundary dates and sample discounts; confirm invoice is still open.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
