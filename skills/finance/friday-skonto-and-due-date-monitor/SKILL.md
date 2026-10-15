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

1. Record the ledger source, as-of time, coverage window and invoice revision. Select only open, unpaid and undisputed obligations; deduplicate on independent supplier ID plus invoice number, then resolve conflicting rows against the authoritative ledger. Paid, void, disputed, duplicate and unknown-status rows stay out of actionable totals and are listed separately. A missing or stale ledger means current status is unknown.
2. For each candidate, trace issue/due/discount dates and discount base/rate to an invoice clause or independently reviewed record. Compare date-only values in the declared business time zone; state the as-of date and days remaining. Do not infer a precise bank cut-off or calendar adjustment from a due date alone. Recompute gross × rate ÷ 100 or net × rate ÷ 100 as the terms specify, round once to cents, and label savings *possible* until eligibility is verified.
3. Rank by the earlier of documented discount deadline and due date, then by amount at risk. Show invoice identity, source, open-status freshness, proposed next review and separate liquidity note; do not infer cash availability from invoice data.
4. Return a one-time alert list. A daily monitor requires a configured scheduler, persistent deduplication key/window and a working delivery adapter with receipt. Otherwise report `NOT_CONFIGURED` for recurrence and delivery; a local result or dashboard mapping is not a sent alert.

## Approval and failures

No automatic payment or invented reminder delivery. A scheduler is a separate capability.
Stale ledger, ambiguous discount base, time zone or amendments produce partial results without precise savings claims. If a send or schedule attempt has uncertain outcome, reconcile its provider receipt before retrying to avoid duplicate alerts. No payment action follows an alert.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recalculate boundary dates and sample discounts; confirm invoice is still open.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 14.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
