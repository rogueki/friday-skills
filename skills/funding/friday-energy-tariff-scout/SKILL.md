---
name: friday-energy-tariff-scout
description: Compare current Austrian energy tariff total costs using consumption and contract terms; no switch.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, funding, energy]
---

# friday-energy-tariff-scout

## Routing

Use for electricity or gas offer comparison. Do not use for broad subscription optimization or physical home energy control.

## Inputs and capability

Inputs: Postal area/network, annual or interval consumption, current tariff, contract term, PV feed-in pattern and comparison date. Required capability: official-web.read for dated provider price sheets and E-Control material, with document.read for a supplied usage bill; meter.read is optional for an interval profile. mock uses synthetic tariffs, read_only and live compare costs only. No provider-switch connector is presumed.

## Procedure

1. Retrieve dated provider tariff sheets and official E-Control comparison/reference data where applicable; record region, tax inclusion and retrieval time.
2. Calculate annual total using base, energy, network and applicable fees, bonus conditions, duration and consumption profile; separate feed-in revenue.
3. Show first-year and renewal-year scenarios, price guarantees, binding, notice periods and unknown charges. Rank by transparent total rather than headline work price.

## Approval and failures

No tariff switch, purchase or contract. Contract changes are tier 3 with real adapter and hard approval.
Missing network region, load profile or tariff terms yields ranges/unknowns, never fabricated exact savings.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work, blocked for missing required capability, waiting_approval for a concrete gated proposal. Never put a proposal in actions_taken. Recompute scenario totals and verify dated source terms before recommending a shortlist.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
