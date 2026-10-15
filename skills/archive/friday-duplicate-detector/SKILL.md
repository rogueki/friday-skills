---
name: friday-duplicate-detector
description: Distinguish byte-identical files from visually similar image or video variants and prepare review groups without deletion.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# Duplicate detector

Use an inventory from `friday-archive-inventory` to identify repeated data. Return review groups; do not remove, hard-link, overwrite or silently select a keeper.

## Inputs and capability

Require inventory scan ID, allowed roots, item identities, supported hash/decoder capabilities, compute budget and privacy scope. Reject stale or changed entries until re-read. Preserve different roots and backup copies as distinct occurrences even when bytes match.

## Procedure

1. Partition candidates by byte size. Stream SHA-256 for candidate files when reads are allowed, recording read failures and files changed between stat and hash. Same size or name is a hint only. Group `exact_byte_match` only when current byte counts and cryptographic digests match; rehash before consequential decisions.
2. Separately, use metadata and supported perceptual image hashes to form `near_image` groups. Record algorithm/version, transformations, threshold and distance per pair. EXIF edits, RAW/JPEG exports, crops and color changes can affect similarity. Do not call these byte duplicates.
3. If a video adapter exists, compare duration, frame or scene fingerprints and audio tracks with stated tolerances; distinguish re-encoding, excerpt and different edit. Unsupported video remains `not_evaluated`, not unique.
4. Build review groups with stable IDs, paths, size, dimensions/duration, capture-time provenance, hash or similarity evidence, backup/retention context and uncertainty. A keeper suggestion may cite resolution, intactness or user favorites, but awaits human review.
5. Include ungrouped errors and ambiguous groups. Archive copies, sidecars and differing metadata may be intentional.

## Output and verification

Return separate `exact_byte_match`, `near_image`, `near_video`, `candidate_only` and `not_evaluated` collections with method/version, evidence and review status. Never combine similarity scores with cryptographic equality. Include scan ID for revalidation.

## Mode, capability and approval

`mock` exercises exact SHA-256 grouping on synthetic records. The current archive mock has no perceptual image or video comparison; report those as unavailable. `read_only` needs a real local adapter. Deletion, link replacement or metadata edits require exact selection, verified backup and appropriate approval. Local `friday.skill.*` records are drafts, not published dashboard events.
