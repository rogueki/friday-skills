---
name: friday-trip-price-comparator
description: Calculate comparable family trip total costs including baggage, transfers, food, fees and cancellation terms.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# trip price comparator

**Use:** Use when the decision is between concrete travel offers. Do not book or pay.

**Inputs:** Offer URLs or quotes, travel dates, party composition, currencies, exchange-rate source/time, included items and refund terms.

## Procedure

1. Confirm source provenance, current capability and trip context. Capture each quote with provider, timestamp, exact occupancy and fare conditions. Normalize base price plus luggage, seats, transport, transfers, lodging taxes, meals, parking, activities, insurance and payment fees. Convert currency using a dated source and keep original currency visible. Compare cancellation fees and refundability separately from headline price. Highlight exclusions, assumptions and volatile inventory; rank by total and flexibility, not only displayed cheapest fare.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: synthetic offers; read_only: calculation; live: read current offers if an adapter is available. Without fresh quote access, use supplied offers with age warning and never state present availability.

**Risk and approval:** Financial totals are estimates until checkout. Do not enter payment information or accept terms here. Booking/payment remains tier 3 with exact-price approval.

**Output and verification:** Output itemized totals, source and timestamp per line, exchange rate, cancellation matrix and confidence. Recompute arithmetic and compare provider checkout total before authorization. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.

## Comparable-offer contract

1. Bind each quote to provider, offer ID or URL, retrieval timestamp, travel dates in the relevant local zones, party and child ages, occupancy, fare class, currency, included items, availability and terms source. Reject a quote whose dates, capacity or age band differ from the requested trip.
2. Build one row per cost: fare, seats, baggage, transfer, accommodation and local tax, meals, parking, activities, insurance, card/payment fees and mandatory surcharges. Mark `included`, sourced amount, estimated amount or `unknown` for each. Do not turn an unknown mandatory line into zero. Sum with decimal currency arithmetic, not binary floats.
3. If currency differs, show the original total and a dated conversion with rate source and possible exchange/card spread. Compare refundable amount, cancellation cutoff in the provider's timezone, change charges and deposit schedule as separate decision columns.
4. Recompute line items and state the all-in total only when mandatory costs are known. Sort by verified comparable total, then family fit and flexibility; otherwise show a range or incomplete comparison without a false cheapest winner.

## Recheck gate

Any quote lacking a source or retrieval time, an expired or changed price, missing occupancy, unknown required fee, or unavailable inventory is ineligible for a booking draft. A fresh quote is still a snapshot: `friday-booking-preparation` must independently recheck provider availability, final checkout total and terms. The E2E5 adapter exercises synthetic fixture arithmetic only; it does not contact a provider or validate a real currency conversion.
