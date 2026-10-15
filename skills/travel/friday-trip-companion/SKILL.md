---
name: friday-trip-companion
description: Provide day-of-trip plans and alternatives using current local conditions without exposing family location unnecessarily.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# trip companion

**Use:** Use during an active trip for schedule, weather, routes, opening hours and nearby alternatives. Do not modify bookings unasked.

**Inputs:** Current city or coarse area, date/timezone, confirmed reservations, mobility and child needs, weather/maps/venue capability and consent.

## Procedure

1. Confirm source provenance, current capability and trip context. Start from confirmed plan and current local time; check weather, transport disruptions, venue hours and travel times from fresh sources. Suggest one practical route and a low-effort alternative, with meal/rest time. Where location access is absent, use the user-supplied area and state the limitation. Flag changes that threaten a reservation and offer next steps without cancelling or rebooking autonomously.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: synthetic city/date; read_only: live-source suggestions if authorized; live: only available adapters may update reminders or calendar after bound approval. Missing real-time sources yields a plan labeled unverified.

**Risk and approval:** Location and family movement are sensitive. Use the least precise location necessary, avoid persistent tracking and do not send whereabouts to unapproved parties. Paid bookings or cancellations require tier 3 approval.

**Output and verification:** Output timestamped day plan, source freshness, routes and fallback. Verify opening hours and weather close to departure; clearly mark any unchecked suggestion. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.

## On-trip check

1. Resolve the user's current **local** date and IANA timezone. Use a coarse location supplied for this request unless the user has explicitly enabled a narrower live location source. Do not keep movement history.
2. Distinguish confirmed tickets/reservations from a draft itinerary. Read current weather, transport status, venue hours and route duration only through available authorized readers. Record source and observation time for each volatile fact; state when a value is a forecast or estimate.
3. Build a short day plan with one primary activity, transfer and queue buffers, meal/rest windows, child-friendly fallback and a low-effort indoor option. Flag a late arrival, closure or disruption against fixed reservations, and show the time by which the family must decide.
4. For urgent safety or medical concerns, provide the relevant local emergency contact only from a verified source and encourage direct local help. Do not invent a provider alert, dispatch or reservation change.

## Stop and recovery

If sources are stale or offline, use the last confirmed reservations and mark route/weather/hours `unverified`; suggest checking the operator or venue directly. Reminders, itinerary edits, cancellations, rebooking and paid activities are separate action proposals with the applicable approval tier. No live tracking or silent notification is part of this skill.
