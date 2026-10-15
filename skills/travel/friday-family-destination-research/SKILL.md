---
name: friday-family-destination-research
description: Compare family destinations by season, safety, child suitability, cost and logistics using dated sources.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# family destination research

**Use:** Use for choosing destinations for a family trip. Do not present live prices or availability without current sources.

**Inputs:** Trip window, current family profile, departure point, budget, candidate regions, official travel advice, weather and transport data capability.

## Procedure

1. Confirm source provenance, current capability and trip context. Build a shortlist with travel time, seasonality, weather, accommodation fit, child activities, medical access, transport and cancellation conditions. For safety and entry rules, prefer current official country sources and note checked date. Separate stable destination attributes from time-sensitive price and inventory. For each option cite actual observed sources and state uncertainty. Compare tradeoffs against the family's constraints; filter out exclusions before ranking.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: synthetic comparison only; read_only: sourced shortlist; live: read permitted current sites or travel APIs if available. If a live source is absent, mark price/availability unknown and use dated indicative ranges only if clearly labeled.

**Risk and approval:** Do not infer health needs from family demographics. Respect website terms and rate limits; no anti-bot bypass or account login by default. Booking and payment are separate tier 3 actions.

**Output and verification:** Output comparison table with dated source links, score rationale, missing evidence and recommendation. Verify price and availability at the provider before any booking decision; flag stale source dates. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.

## Research sequence

1. Take the minimal, dated output of `friday-family-travel-profile`. Reconfirm departure area, calendar dates, party ages at departure, budget currency and hard exclusions before searching. Do not silently relax a hard constraint to make a destination rank well.
2. For each destination, separate official travel/entry advice and medical access from tourism claims. Record country or region, source URL, publisher, retrieval time, validity window and the exact question supported. Check transit countries and seasonal conditions when they alter the trip.
3. Estimate door-to-door travel burden including transfers and likely waiting, plus weather range, family room fit, child activities, food, mobility, emergency access and cancellation flexibility. Mark unknown values explicitly; use `friday-trip-price-comparator` for offer-level arithmetic.
4. Show a short ranked set with hard-constraint pass/fail, evidence date, tradeoffs and unresolved checks. An indicative price is never a current quote, and a search result is not proof of inventory.

## Stop and recovery

If current official safety or entry information is unavailable, leave that criterion unverified and do not give an unconditional safety or entry recommendation. If no live offer reader exists, return destination research without a current price or availability claim. Recheck volatile facts before handing an option to booking preparation.
