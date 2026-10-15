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

1. Confirm source provenance, current capability and approved scope. Outline chapters and page rhythm, then distribute hero images and supporting moments across event dates. Check resolution at intended print size, crop-safe areas, bleed and color profile against actual vendor requirements. Draft titles and captions from verified facts, mark unknown dates and missing images. Prepare a page manifest or export proof; request review of all family names and visible private details.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: synthetic layout outline; read_only: page plan and missing-assets report; live: available local design tool may generate a proof after output-path approval. No vendor spec means label print settings provisional.

**Risk and approval:** Printing and checkout are tier 3 actions requiring bound approval and second factor. Sharing assets with a vendor requires explicit destination and data preview. Do not expose children or addresses in sample/public previews.

**Output and verification:** Output chapter table, page map, image IDs, captions, resolution warnings and export status. Verify every image exists, page count fits, and proof renders before declaring ready. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
