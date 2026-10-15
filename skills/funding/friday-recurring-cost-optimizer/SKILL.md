---
name: friday-recurring-cost-optimizer
description: Find defensible savings across recurring bills using usage, contract and switching costs; no cancellations.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, funding, recurring]
---

# friday-recurring-cost-optimizer

## Routing

Use for multi-category recurring cost optimization. Do not use for only energy tariff pricing or contract deadline extraction.

## Inputs and capability

Inputs: Recurring bill inventory, usage, contract terms, cancellation dates, service constraints and desired savings horizon. Required capabilities: document.read for bills/contracts and, if configured, finance.subscription-ledger.read for recurring charges; official-web.read is needed before citing current provider alternatives. mock uses synthetic subscriptions, read_only and live prepare a savings comparison or drafts only. No cancellation or purchase adapter is presumed.

## Procedure

1. Normalize annual cost by category (energy, internet, mobile, optional insurance, software) and identify duplicates or unused seats.
2. For each candidate, compare realistic alternatives including fees, taxes, service loss, switching effort and notice/binding; cite dated official provider terms.
3. Rank net savings and friction, then prepare inquiry or change drafts with owner decision points.

## Approval and failures

No cancellation, purchase or switch; messages are tier 2, contracts tier 3 with real adapters and approvals.
If a contract or usage record is missing, present a question and provisional estimate rather than exact saving.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Reconcile baseline bills and independently recompute annualized net savings.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
