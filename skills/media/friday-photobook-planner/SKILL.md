---
name: friday-photobook-planner
description: Create a family photobook chapter and page plan with image selection, captions and print preparation.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# photobook planner

**Use:** Use when the deliverable is a planned or export-ready photobook. Do not place a print order or make a generic media inventory.

**Inputs:** Theme, source selection manifest, desired format/page count, print vendor specifications if provided, captions, privacy scope and mode.

## Procedure

1. Confirm approved source IDs/hashes, theme, audience, page count, target format, privacy boundaries and available layout/export capability. Obtain real vendor trim, bleed, color and resolution specifications if print readiness is requested; otherwise mark print settings provisional.
2. Design chapters and page rhythm with hero and supporting images distributed across the event chronology. Produce a page map with page number, image ID, intended crop, caption source, layout and blank/missing asset status. Avoid repeating one burst unless the story calls for it.
3. Check each placed image's effective resolution at the actual printed size, crop-safe area, bleed, orientation and color profile against the supplied vendor specification. Unknown pixel dimensions or absent vendor specifications remain unresolved warnings, never a print-ready pass.
4. Draft titles and captions only from verified context. Mark uncertain dates and names, and ask for human review of family identities, children's images, school names, addresses and any exposed private detail. Create a proof only through an available local layout tool after exact output-path approval.
5. Reconcile page count and asset IDs with the manifest, inspect every page of a rendered proof for missing images, clipped captions and crop errors, and record review corrections. A validated proof prepares export; placing or paying for an order is a separate tier-3 action requiring exact vendor, price, recipient and second-factor approval.

**Mode and capability:** mock: synthetic layout outline; read_only: page plan and missing-assets report; live: available local design tool may generate a proof after output-path approval. This package has no real layout renderer, proof checker or ordering adapter. No vendor spec means label print settings provisional.

**Risk and approval:** Printing and checkout are tier 3 actions requiring bound approval and second factor. Sharing assets with a vendor requires explicit destination and data preview. Do not expose children or addresses in sample/public previews.

**Output and verification:** Output chapter table, page map, image IDs, captions, resolution/privacy warnings and proof/export status. Declare print-ready only with real vendor specs, complete proof rendering and per-page review evidence; never equate a page plan with an order. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
