---
name: friday-presentation-qa
description: Check a produced presentation for visual, factual, accessibility, playback and export defects before delivery.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, office, presentation, quality]
---

# Presentation QA

Use for acceptance review of an actual deck or export. Do not claim QA complete from a storyboard, XML inspection or a few slides when the full deck is available.

**Inputs:** deck and source file, intended delivery platform, screen size, branding and accessibility requirements, claim/source ledger, mode, rendering and PowerPoint playback capability.

1. Record file hash, slide count, fonts and media dependencies. Render every slide at delivery aspect ratio; inspect overflow, clipping, low contrast, tiny text, alignment, page numbers, image rights and missing assets. Sample each master/layout type closely.
2. Compare numbers, chart labels, citations and claims with the supplied source ledger. Flag any untraceable factual change for the owner; do not infer source accuracy from attractive formatting.
3. If animations exist, check reveal order, speaker logic and reduced-motion/static export using actual playback capability. Test the target export and reopen the produced artifact where possible.
4. Log each defect with slide number, severity, evidence and suggested fix. Recheck repaired slides and dependent layouts before closure.

**Mode/capability:** `mock` uses sample artifacts and labels limits; `read_only` reviews without edit; `live` may save an authorized QA report or revised export but not alter the original. Reads are Tier 0; local report/export Tier 1; external distribution Tier 2. Do not upload confidential decks to unapproved renderers.

For the local synthetic E2E7 adapter, distinguish OOXML package checks from rendered-slide checks. Its PDF page count, extracted text and sampled pixel variance are automated smoke checks, not human visual review, accessibility review or native PowerPoint playback. A failed or unavailable renderer leaves the scenario `partial` and the missing QA items `NOT_RUN`.

**Output:** PASS/FAIL/NOT_RUN matrix, slide findings, verified export paths and normalized result. **Failure:** When rendering, fonts or playback are unavailable, mark those checks NOT_RUN and status `partial`; never equate successful file open with visual approval.
