---
name: friday-media-quality-review
description: Flag visibly damaged, empty, badly exposed or very similar media for human archive review.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# media quality review

**Use:** Use to assess archive media usability, separate from selecting family highlights or deduplicating byte-identical files.

**Inputs:** Inventory IDs, approved local media paths, objective criteria, codec/decoder capability, privacy rules and mode.

## Procedure

1. Confirm provenance, path scope and capability. Probe file readability, duration/frame count for clips and dimensions for images. On local previews, score blur, exposure, blank frames and compression defects with stated thresholds; treat artistic blur and dark scenes as review cases. Link near-identical sequences without asserting identical content. Assign flags and explanations; retain a manual review bucket for unsupported formats and subjective judgments.
2. Classify any proposed write through `friday-approval-policy` and bind approval to exact paths and payload before execution.

**Mode and capability:** mock: synthetic flags; read_only: review queue; live: local analysis may create temporary previews in an approved location, then clean them safely. Missing decoder yields unreviewed, not unusable.

**Risk and approval:** Do not delete, quarantine or upload. Family faces and locations stay within authorized privacy scope. Quality flags cannot override user favorites.

**Output and verification:** Output per-item flags, score evidence and limitations. Verify every flagged file path/hash against inventory and sample false-positive candidates with human review. Local `friday.skill.*` records are drafts, not published dashboard events.
