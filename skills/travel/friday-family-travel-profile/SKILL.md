---
name: friday-family-travel-profile
description: Maintain a revisable family travel preference profile with age-at-trip, budget and privacy controls.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, travel, family]
---

# family travel profile

**Use:** Use when creating or updating reusable family travel preferences. Do not research destinations or book travel.

**Inputs:** User-supplied travelers and birth dates or ages, trip date, home/start point, budget currency, mobility, food, lodging and consent scope.

## Procedure

1. Confirm source provenance, current capability and trip context. Record adults and children as user-supplied facts, never assume the plan's example of two adults and ages six/eight is still true. Calculate each child's age at planned departure only if birth data and date are supplied; otherwise ask for current ages when needed. Store budget ceiling, school-holiday constraints, accommodation, meals, transport and exclusions with source/date. Keep medical or organizational notes only when explicitly provided and necessary. Let the user inspect, correct and remove profile fields.
2. Route any proposed external or persistent action through `friday-approval-policy` with exact target, payload and current terms.

**Mode and capability:** mock: fictional profile; read_only: proposed profile update; live: write only via approved secure profile adapter. If no profile store exists, return a transient summary and do not claim persistence.

**Risk and approval:** Children's ages, health and family location are sensitive. Minimize retention, avoid logs and public exports. Persistent changes need authorized exact-field action; sharing the profile externally needs separate approval.

**Output and verification:** Output field-value-source-date table, missing fields and retention status. Verify saved values by reading them back through the adapter, or label the profile unsaved. Internal `friday.skill.*` records are local lifecycle drafts, not dashboard publications.

## Profile contract

- Record the requested travel window as local calendar dates with its destination timezone when known. Keep the source and observation date for every preference; separate hard constraints from wishes and unanswered questions.
- Compute age **at departure**, not from a fixed example or the current date. If a birthday or trip date is unknown, label the age unknown and ask only for the minimum detail needed for age-dependent fares or entry rules. Never derive a birth date from an approximate age.
- Represent the party as counts until named travelers are necessary for a separately approved booking step. Do not include identity numbers, full birth dates, medical details, or precise home addresses in a comparison handoff.
- Hand off a minimal profile: party/age bands, departure area, dates or flexibility, budget and currency, mobility/meal/lodging constraints, exclusions, provenance and missing fields. Mark `saved: false` unless a trusted profile store confirms a write and readback.

## Stop and recovery

If children have aged since a saved profile, dates changed, or a constraint conflicts with the budget, mark the dependent recommendation stale and request an updated value. If consent or a secure store is absent, keep only a transient response; a conversation summary is not proof of saved profile state.
