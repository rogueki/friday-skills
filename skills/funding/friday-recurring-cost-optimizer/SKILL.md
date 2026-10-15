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

Inputs: Recurring bill/contract inventory, usage and seats, renewal/notice dates, minimum service requirements, switching effort and desired horizon. `document.read` and configured `finance.subscription-ledger.read` are required for a bill-backed portfolio; `official-web.read` is required before claiming a current provider alternative. The manifest currently lists no live/mock adapter for these capabilities. A user-supplied list can support an explicitly unverified worksheet, not a verified saving. Scope includes electricity/gas/heating, internet/mobile, software and business tools; insurance only where policy coverage and exclusions can be compared by an appropriate specialist. Energy-only quote calculations belong to `friday-energy-tariff-scout`.

## Procedure

1. Reconcile each recurring charge to a bill/contract, billing frequency, service owner, period, VAT basis, usage/seats, discounts and one-time fees. Deduplicate statement charges and aliases; mark possible duplicates as questions until identity is checked. Record contract source, term, renewal/notice deadline and consequences of missing notice.
2. Identify low-risk improvements first (unused seats, duplicate subscriptions, downgrade) and compare alternatives against the user's minimum coverage, speed, uptime, support, data portability, geographic reach or insurance benefits. For energy, pass the same region/consumption to the tariff scout. Capture dated official provider terms and verify availability for the account and location; no generic promotional price is a personalized offer.
3. Compute baseline and candidate cost over the *same* 12-month and relevant contract-term horizon: recurring charges + startup/exit fees + overlap + taxes − only earned bonuses/credits. Subtract switching effort/cost and any lost benefit to state net savings; separately show non-monetary service impact. Model renewal after an introductory discount and a no-switch scenario. Rank by evidenced net savings, deadline urgency and disruption risk, with unknowns as ranges rather than precise euro claims.
4. Produce a decision table per contract: baseline evidence, candidate/source/date, comparable total, net saving/range, service tradeoff, binding and notice evidence, action deadline, missing facts, and proposed inquiry or change draft. Leave cancellation/switch/purchase unexecuted.

## Approval and failures

No cancellation, purchase or switch; messages are tier 2, contracts tier 3 with real adapters and approvals.
If a contract, notice clause or usage record is missing, present a question and provisional estimate rather than exact saving or cancellation date. A payment stream alone does not prove a cancellable contract. If required reads are unavailable, return `blocked` for a verified portfolio analysis; no external provider or account is changed.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work and blocked for missing required capability. Never put a proposal in actions_taken. Reconcile annualized baseline to bills and independently recompute net savings, including transition cost and service loss; disclose source coverage and incomplete contracts.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.4 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
