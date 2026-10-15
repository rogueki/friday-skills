---
name: friday-booking-preparation
description: Prepare a verified family booking summary and draft without making a purchase.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# booking preparation

**Use:** Use when an option is chosen and details need review before reservation. Do not complete checkout.

**Inputs:** Selected offer, provider, traveler names from trusted user input, travel dates, party count, final price, cancellation terms, required documents and mode.

## Procedure

1. Confirm source provenance, current capability and trip context. Match offer against source and fresh provider availability. Verify spelling and dates against user-supplied documents without copying full document numbers into logs. Summarize included luggage, rooms, transfers, payment schedule, refund and cancellation cutoffs. Create a redacted booking draft or checklist and highlight unresolved mismatches. Present the exact provider, travelers, dates, currency and amount for explicit review.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: fictional booking draft; read_only: checklist; live: an authenticated provider adapter may prepare a draft only if it does not submit or reserve. If capability semantics are unclear, stop before sending data.

**Risk and approval:** Booking, accepting terms and payment are tier 3 with action-bound approval and second factor immediately before submission. Never infer consent from a prior option choice or stale quote.

**Output and verification:** Output reviewed summary, discrepancies and pending approval state. Verify submitted booking only from a provider confirmation after a separate authorized action; no draft is a booking. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.
