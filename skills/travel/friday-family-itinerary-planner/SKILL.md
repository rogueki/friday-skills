---
name: friday-family-itinerary-planner
description: Build a flexible family itinerary with rest, meals, weather alternatives and arrival buffers.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# family itinerary planner

**Use:** Use after destination and travel dates are known to plan daily activities. Do not compare booking prices.

**Inputs:** Destination, travel dates, travelers' current ages/preferences, lodging area, transport mode, reservation times, opening hours and weather source.

## Procedure

1. Confirm source provenance, current capability and trip context. Anchor fixed arrivals, departures and existing reservations. Add realistic transfer and check-in buffers, meals, rest periods and age-appropriate activity lengths. Limit each day to a manageable main activity, add optional nearby alternatives and a rainy-weather fallback. Check current opening hours and travel times where tools exist; otherwise mark them to verify. Distinguish confirmed bookings from proposals and include accessible or mobility alternatives when requested.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: fictional days; read_only: draft itinerary; live: may read maps, weather and venue data through available adapters. Calendar writes or reservations require a separate approved action.

**Risk and approval:** Do not expose real-time family location to unapproved services. Never schedule children into unsafe or age-inappropriate activities based on unverified marketing claims.

**Output and verification:** Output day plan, fixed versus optional events, buffers, source-check dates and contingencies. Verify no time overlaps, unrealistic transfers or missed reservation constraints. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.
