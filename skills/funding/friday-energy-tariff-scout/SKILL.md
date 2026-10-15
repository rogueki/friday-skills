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

Inputs: Austrian postcode **and network operator**, customer class, comparison date, annual grid import and gas use or interval profile, current tariff/invoice, contract term, PV self-consumption and grid export volumes, and desired horizon. `official-web.read` is required for dated provider terms and [E-Control Tarifkalkulator](https://www.e-control.at/unsere-services/tarifkalkulator) comparison; `document.read` supports supplied bills, `meter.read` is optional for intervals. The capability manifest currently has no live/mock tariff or official-web adapter. E-Control is an official comparison lead; record the user's exact inputs and result date, then corroborate contract-specific conditions with dated provider sheets. No tariff-switch connector is installed.

## Procedure

1. Confirm postcode/network operator and customer/usage class; reconcile annual import/export and billed period to a bill or meter record. Do not substitute generation for export or subtract self-consumed PV twice. Run or inspect the E-Control comparison for the same inputs, date and tariff class, then open current provider price sheets. Record effective dates, gross/net basis, retrieval UTC, dynamic-index formula if any, and whether the result includes network charges/taxes.
2. For each tariff calculate an auditable annual ledger: fixed supplier charge + import kWh by applicable rate/time band + network fixed/volumetric charges + levies/taxes and other applicable fees − *earned and contractually available* bonuses; compute export remuneration separately using export kWh and applicable feed-in terms. Avoid double-counting charges already included in an all-in figure. Keep VAT basis consistent and label every unknown rather than insert a default rate.
3. Compare current contract, candidate first year and renewal years over the same usage horizon. Account for bonus vesting, price guarantee expiry, variable/index risk scenarios, contract binding, cancellation notice, transition overlap/fees, PV import/export terms and service conditions. A current promotional price is not a guaranteed renewal price. Give a range or sensitivity table when critical charges, interval data or later prices are unknown.
4. Rank by comparable total annual cost and user constraints, not headline Arbeitspreis. Show calculation inputs, each subtotal, source, assumptions, unknowns and exact possible savings versus the evidenced baseline; recommend a manual verification step before any switch.

## Approval and failures

No tariff switch, purchase or contract. Contract changes are tier 3 with real adapter and hard approval.
Missing network operator, consumption or tariff terms yields ranges/unknowns, never fabricated exact savings. If `official-web.read` is unavailable, a current market comparison is `blocked`; an uploaded bill alone supports only baseline analysis. No price, provider or tax rate may be hardcoded from an old example.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work and blocked for missing required capability. Never put a proposal in actions_taken. Independently recompute totals from the shown rows and verify each dated provider term; distinguish observed E-Control output from a manually estimated scenario.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 16.3 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
