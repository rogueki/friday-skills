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

**Hermes handoff:** The installed Hermes `powerpoint` skill documents `pptx_from_template.py` for filling an existing template and `pptx_read.py` for read-back. Use those only after checking the bundled scripts, `python-pptx`, template compatibility and authorized paths in the active runtime. Friday's brand inventory and comparison remain separate checks; the script's success does not prove master/layout fidelity. See [Hermes workflows](../../../docs/HERMES_WORKFLOWS.md).

**Mode/capability:** `mock` yields a style specification with synthetic assets; `read_only` audits template/deck; `live` may produce a separate file after checking a healthy local worker and authorized workspace. Reads are Tier 0, a new reversible file Tier 1, external sharing Tier 2. Do not upload proprietary templates or logos without authorization.

For the repository's synthetic E2E7 mock, `adapters/presentation_mock.py` creates a new three-slide editable PPTX from synthetic labels and checks its OOXML parts. If a local LibreOffice/OpenOffice CLI successfully converts that file to PDF, rasterize and inspect all three pages. Missing or failed rendering is `partial`, even when PPTX creation succeeded. This mock does not apply an approved brand template, preserve an existing deck, exercise PowerPoint COM, or verify animations.

**Output:** style rules, new artifact path if created, deviations and visual comparison evidence. **Failure:** Missing template, licensing, font or render capability leaves a design spec or `partial` result, not a verified deck.

## Brand implementation record

- Create a template inventory keyed by master/layout and slide number: slide dimensions, theme color values, named font faces and licensed substitutes, logo file/hash and safe area, margins/grid, chart colors, icons, footer and page-number behavior. Flag missing rights or assets before use.
- Map every approved rule to the location actually changed. Verify title, body, table/chart and appendix examples on every relevant layout; a change to one slide is not evidence that the master or all layouts changed.
- Save a new PPTX, reopen it, render all slides and compare with baseline images at the same size. Record missing-font substitutions, overflow, contrast and broken/changed notes, links, charts or media. Preserve the source hash and report unsupported elements as deviations.
- The repository E2E7 adapter generates synthetic labels with `python-pptx`; its OOXML validation and optional PDF/PNG smoke render do not test this template workflow or Windows Office Worker. If the worker or required fonts are absent, stop at specification/audit status `partial`.
