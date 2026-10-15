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

## Day-plan contract

- Normalize travel dates to destination local dates and attach an IANA timezone to timed events. Preserve an explicit offset for transport legs across zones or daylight-saving transitions; never infer a local arrival date by adding flight duration to a departure clock.
- Put confirmed transport and reservations first, with source, confirmation state and cancellation deadline. For each day choose at most one main activity; add meals, rest, child-appropriate duration, travel time and a weather fallback. Arrival and departure days need wider buffers.
- For every venue or route, keep `verified_at`, source and status: confirmed, checked suggestion or unverified. A map estimate is not a guaranteed connection; recheck hours, disruptions, admission and last entry before departure.
- Detect overlapping fixed events, transfer gaps shorter than realistic travel plus buffer, opening hours outside the proposed window, and activities beyond age or mobility constraints. Return an explicit conflict list rather than a polished but infeasible itinerary.

## Stop and recovery

When weather/maps/venue access is absent, produce a flexible draft with timings marked `to_verify`. If a fixed booking conflicts with a proposed plan, keep the booking fixed and offer options for human choice. No calendar write, reservation change or location sharing follows from merely producing a plan.
