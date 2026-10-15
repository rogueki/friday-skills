---
name: friday-photo-curator
description: Rank and group family photos for review by image quality, duplicates, bursts and event context without automatic deletion.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# photo curator

**Use:** Use when a user asks which photos to keep or highlight from an existing collection. Do not replace an archive inventory or infer a person's identity.

**Inputs:** Source manifest or approved read paths, event context, desired output count, local visual-analysis capability, privacy preferences and operating mode.

## Procedure

1. Check manifest provenance, source IDs/hashes, event scope and the local decode/analysis capability. If images cannot actually be decoded, group only by supplied metadata and label visual quality unassessed.
2. Group byte-identical files only on full hashes. Treat perceptual similarity as a separate, fallible signal: same hash means identical bytes; similar pixels can differ in edits, crops or content. Cluster bursts with capture-time uncertainty, then present ambiguous pairs for human review rather than auto-merging.
3. Assess sharpness, exposure and composition as separate observations with the image ID, crop and algorithm or human reviewer. Where a consented local face-expression capability exists, use it only as an advisory signal; never infer names or relationships from faces. Preserve emotionally important, technically imperfect frames as candidates.
4. Build representative picks, alternates and a review queue; mark why each was included or excluded. An exclusion is a curation decision, not a deletion decision. If quarantine is requested, present exact paths/hashes, reversibility and a separate approval proposal. Never invoke deletion as part of curation.
5. Before writing a review album, derivative or quarantine copy, invoke `friday-approval-policy` with exact targets and payload. No write proceeds through a missing adapter or an unbound approval.

**Mode and capability:** mock: synthetic scored examples; read_only: selections and proposed quarantine list; live: only an approved adapter may create review copies or quarantine after exact-path preview. This package has no real image decoder, similarity scorer or quarantine adapter. If visual analysis is absent, fall back to metadata grouping and manual review.

**Risk and approval:** Never delete automatically. Keep originals and private family media local unless separately authorized. Treat score as advisory, especially for children and emotional significance.

**Output and verification:** Output ranked groups, pick and alternate IDs, separate exact/near/burst evidence, reasons, uncertain cases and original paths. Check all picks against manifest hashes and ensure no unsupported image got an invented visual score. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
