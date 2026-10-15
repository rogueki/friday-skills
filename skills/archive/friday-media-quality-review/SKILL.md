---
name: friday-media-quality-review
description: Review archive media readability and measurable quality problems with transparent thresholds and human judgment, without deletion.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# Media quality review

Use to prioritize human review of damaged or low-quality archive media. It does not select family highlights, declare variants duplicates or erase source files.

## Inputs and capability

Require inventory IDs and source hashes, approved local paths, available image/video decoders, criteria, privacy scope and mode. Verify current identity before decoding. Unsupported format, inaccessible file and transient read failure are different outcomes.

## Procedure

1. Probe container/readability and record decoder/version, error and byte integrity separately. For still images measure dimensions and decode result; for clips measure duration, frame count, streams and sample timestamps. Empty or truncated content is a technical finding only when probe evidence supports it.
2. On authorized local previews, calculate blur score, clipping/underexposure percentage, blank frames, compression or silence with declared algorithms and thresholds. State sampled frame positions and coverage. Dark scenes and deliberate soft focus require human review.
3. Place repeated bursts or related clips in review sets with source IDs and similarity evidence. Do not claim exact duplicates without byte hashes from `friday-duplicate-detector`.
4. Mark each item `technical_failure`, `quality_review`, `acceptable_on_checked_criteria` or `not_evaluated`. Preserve favorites, edits, RAW originals, sidecars and protected family moments for human judgment. Show possible false positives when privacy permits.
5. Reconcile queue with inventory IDs and rescan changed items. Negative quality scores cannot remove an item from a migration plan without review.

## Output and verification

Return source ID/hash, codec/decoder, checks run, thresholds, measurements, preview location if approved, coverage, flags, confidence limits and review decision. Keep GPS/faces and thumbnails local; temporary preview cleanup needs a separately controlled action.

## Mode, capability and approval

`mock` is specification-only unless a quality fixture/decoder exists; current archive E2E mock does no image or video decoding. `read_only` needs a trusted local media adapter. Preview write, quarantine, upload, repair or delete is a separate scoped action and approval. Local `friday.skill.*` records are drafts, not published dashboard events.
