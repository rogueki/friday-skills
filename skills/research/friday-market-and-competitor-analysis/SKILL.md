---
name: friday-market-and-competitor-analysis
description: Compare a defined market and competitors by current offer, price, position and evidence-backed opportunities and risks.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, research, market]
---

# Market and competitor analysis

Use when a product or venture needs a market map, competitor comparison or positioning choice. Do not use for investigating one shop's legitimacy or treating a small public sample as a full market census.

**Inputs:** target customer, geography, category and use case, price unit/currency, comparison period, named competitors, decision criteria, mode and permitted web/data capabilities.

1. Define the market boundary and comparable offer unit, including taxes, subscription terms, service levels and channel. Explain how competitors were sampled and which segments are excluded.
2. Gather current first-party offerings/prices and dated primary market data. Keep a source ledger for each row; distinguish list prices from observed checkout prices and claims from measured performance.
3. Normalize comparable features and price bases. Analyze strengths, weaknesses, gaps, barriers, substitutes, likely biases and change over time. Use scenarios where market size or future demand is uncertain.
4. Recommend a defensible positioning or next experiment tied to the user's constraints. State what evidence would invalidate it and when prices/data should be refreshed.

**Mode/capability:** `mock` compares synthetic vendors; `read_only` analyzes authorized public/provided data; `live` can save a local comparison. Research is Tier 0, local artifact Tier 1; purchasing data, subscriptions or contacting rivals requires separate approval and capability. Respect crawl limits and terms; do not automate account creation or access controls.

**Output:** comparable market table, source/date ledger, opportunity-risk analysis, uncertainty and normalized result. **Verification/failure:** Reopen sampled primary offer pages and recalculate normalized prices. If a competitor's price is inaccessible or outdated, leave it unknown rather than estimate it as fact.

## Comparison contract

Record sampling frame, direct competitors, substitutes and excluded segments; a convenient public sample is not a market census. Each comparable offer row needs source ID, exact plan/SKU, geography, availability and retrieval date. Normalize currency, tax, shipping, setup fee, introductory discount, renewal price, contract length, usage limit and service level across the same horizon. Show arithmetic and assumptions; a list price is not a verified checkout price. Leave unavailable values `unknown` rather than filling them from nearby products.

For market size, use dated primary statistics with population and method or label an explicit scenario; do not extrapolate from a handful of storefronts. Separate observed offer features from inferred positioning and opportunities. State which price or demand change would reverse the recommendation. The single-page web extraction adapter cannot create a market census, normalize prices or guarantee that a vendor's checkout terms were observed.
