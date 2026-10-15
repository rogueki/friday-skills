---
name: friday-photo-enhancement
description: Apply reversible exposure, white balance, sharpening, denoise, crop and perspective corrections to approved photo copies.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# photo enhancement

**Use:** Use for specific technical photo corrections. Do not use for identity, body, age or other person manipulation without an explicit scoped instruction.

**Inputs:** Original image paths and hashes, requested corrections, acceptable crop boundaries, local editor capability, output format and operating mode.

## Procedure

1. Confirm source provenance, current capability and approved scope. Read originals and determine color profile, bit depth and orientation. Preview bounded adjustments for exposure, white balance, sharpening, noise, crop and perspective. Save non-destructively to new paths or sidecar instructions; preserve metadata only when appropriate and omit GPS from shared exports. Present before/after or adjustment parameters for review. Re-run a correction from the original, never from a repeatedly compressed derivative.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: adjustment recipe on synthetic image; read_only: suggested parameter set; live: trusted local editor may write a derivative after target preview. Missing editor returns recipe and no edited-file claim.

**Risk and approval:** Explicit permission is needed for manipulative changes to people, especially children. Do not use an external image service without authorized transfer. Never overwrite the sole original.

**Output and verification:** Output derivative path, original hash, parameters and review status. Verify opening the derivative, dimensions and color integrity, and compare source hash before and after to confirm it was untouched. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
