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
