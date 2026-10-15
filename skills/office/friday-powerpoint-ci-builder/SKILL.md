---
name: friday-powerpoint-ci-builder
description: Build or repair PowerPoint brand styling from an authorized template, including layouts, typography and reusable chart rules.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, office, powerpoint, branding]
---

# PowerPoint CI builder

Use for a brand-consistent presentation template or deck styling. Do not use to invent a brand, rewrite the argument or claim that a generated PPTX retains every advanced Office feature.

**Inputs:** approved brand guide and PPTX template, logo assets and rights, target deck, required slide sizes/layouts, permitted fonts, chart/icon rules, output path, mode and Windows Office Worker or equivalent capability status.

1. Inventory theme, master/layout variants, placeholders, theme colors, font availability, spacing, logo safe area, chart palette, footer and page number rules. Record missing or conflicting guidance rather than silently selecting new branding.
2. Make a copy of the original and plan edits by slide/layout. Keep reusable rules in master/layout where the available worker safely supports it; otherwise document per-slide exceptions. Preserve notes, charts, embedded media and accessibility metadata when possible.
3. Apply only supported edits through an authorized local capability. Avoid round trips through libraries known to drop unsupported effects. Render representative title, content, data and closing slides at the target aspect ratio.
4. Compare before and after against guide and originals: logo placement, alignment, font substitution, contrast, charts, footer and page numbers. Send the full deck to `friday-presentation-qa` for final QA.

**Mode/capability:** `mock` yields a style specification with synthetic assets; `read_only` audits template/deck; `live` may produce a separate file after checking a healthy local worker and authorized workspace. Reads are Tier 0, a new reversible file Tier 1, external sharing Tier 2. Do not upload proprietary templates or logos without authorization.

**Output:** style rules, new artifact path if created, deviations and visual comparison evidence. **Failure:** Missing template, licensing, font or render capability leaves a design spec or `partial` result, not a verified deck.
