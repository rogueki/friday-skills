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
