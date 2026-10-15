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
