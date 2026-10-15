---
name: friday-archive-reorganization-plan
description: Produce a reversible item-level archive copy plan with path, capacity, backup and conflict checks; do not execute it.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# Archive reorganization plan

Use after a current `friday-archive-inventory` to propose a target structure. This skill prepares a reviewable manifest, never executes copies or moves.

## Inputs and capability

Require scan ID and coverage, exact source identities/hashes, approved target root and volume, naming/taxonomy rules, available capacity, filesystem behavior and fresh backup evidence. Unreadable or changing sources are unresolved, not silently omitted. Duplicate and quality reports are optional annotations, not permission to exclude originals.

## Procedure

1. Draft a target tree by year/event/type with explicit unknown-date and unclassified buckets. Map every source ID exactly once to source path, intended target, operation `copy_only_no_overwrite`, expected bytes/hash and rollback reference. Keep sidecars and related RAW/JPEG files linked.
2. Normalize Unicode consistently and test target uniqueness under target filesystem case folding. Reject traversal, absolute/foreign roots, Windows reserved names, trailing spaces/dots, path length violations, symlink/junction escapes and existing target conflicts. A rename rule must resolve each collision visibly; never overwrite automatically.
3. Estimate destination bytes including temporary copy, filesystem overhead and safety margin. Recheck free space and writeability near execution; a current estimate is not a future guarantee. Identify cross-volume operations and do not assume atomic rename across volumes.
4. Record backup snapshot, coverage, observation time and restore evidence. Missing or stale backup keeps the plan `not_ready`. Separate any future original cleanup from the copy manifest.
5. Divide into bounded batches with sequence, failure stop points, source revalidation, journal location and rollback manifest for newly created copies only. Explain what must happen after interruption before rerun.
6. Produce the canonical manifest and fingerprint of action, exact target and payload. Submit it for trusted host Tier 2 approval only when a real file adapter, backup and readiness checks exist. A plan or model answer is not an approval.

## Output and verification

Return target tree, source-to-target table, conflicts, capacity math, backup evidence, readiness `ready_for_review`/`not_ready`, required approval, batch plan, rollback map and unresolved items. Verify all source IDs accounted for, no normalized target collisions and no implicit delete/overwrite. Any revision changes the approval fingerprint.

## Mode, capability and limit

`mock` can produce the pinned in-memory copy manifest and simulated approval proposal in `adapters/archive_e2e_mock.py`. It checks selected path/case/reserved-name and capacity cases but does not inspect real filesystems, symlinks or Unicode-equivalent targets exhaustively. `read_only` returns a dry run. Local `friday.skill.*` records are drafts, not published dashboard events.
