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

1. Confirm the original ID/path/hash, requested correction, privacy scope, output format and actual local editor capability. Read orientation, color profile, bit depth and pixel dimensions only when a decoder exists. If not, give a proposed recipe with those properties explicitly unknown.
2. Define bounded exposure, white-balance, sharpening, denoise, crop and perspective adjustments. Preserve faces and context when cropping; flag loss of people or important details for review. Do not smooth, reshape, age or otherwise alter a person without an explicit scoped instruction.
3. Preview from the original, keeping before/after or parameter evidence. For a write, request `friday-approval-policy` bound to the exact original hash, derivative path and settings. Write a new derivative or sidecar; never overwrite the sole original or chain repeatedly compressed derivatives. Keep source metadata only as needed and omit GPS from any shared export.
4. Open or decode the complete derivative, inspect dimensions, color and crop, compare with the requested correction, and rehash the original to confirm it is unchanged. If decode or visual review is unavailable, label output unverified and stop before calling it complete.

**Mode and capability:** mock: adjustment recipe on synthetic image; read_only: suggested parameter set; live: trusted local editor may write a derivative after target preview. This package has no real photo editor or decoder. Missing editor returns recipe and no edited-file claim.

**Risk and approval:** Explicit permission is needed for manipulative changes to people, especially children. Do not use an external image service without authorized transfer. Never overwrite the sole original.

**Output and verification:** Output derivative path only after creation, otherwise recipe; include original hash, parameters, crop and privacy choices, review state and decode/visual evidence or explicit gap. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
