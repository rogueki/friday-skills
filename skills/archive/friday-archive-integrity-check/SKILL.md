---
name: friday-archive-integrity-check
description: Reconcile archive source, destination and backup against a manifest by count, bytes, hashes, readability and structure without repairing files.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# Archive integrity check

Use after a copy batch, backup or periodic audit. It verifies evidence and proposes repairs; it does not execute migration, restoration or deletion.

## Inputs and capability

Require a trusted baseline manifest with scan/operation ID, source and destination roots, expected path/size/SHA-256 for each item, known journal states, backup evidence, time and requested `full` or `sample` coverage. Without a baseline, report inventory observations only and make no intact-archive claim.

## Procedure

1. Re-identify allowed roots and current paths. Reject traversal, unexpected junction/symlink targets and changed identities. Account for every expected ID; compare normalized target paths and find missing, extra, wrong-location and case/Unicode collision items.
2. For full verification, stream source and destination bytes independently, compare size and SHA-256 to pinned expected values, then compare counts and total bytes. A same count or successful copy command alone is insufficient. For samples, state selection method, sample size and unsampled population; do not promote sample success to full coverage.
3. Probe readability with available decoders separately from byte integrity. A hash match does not establish usable image/video content; an unavailable decoder yields `not_evaluated`. Record I/O errors, changing files, algorithm and observation time.
4. Verify backup coverage and freshness via snapshot manifest and actual sample read/restore evidence where available. Separate `backup_unverified` from file corruption.
5. Reconcile journal states with current data. A `copying` or `unknown` item remains unresolved even if a destination path exists until independently read back. Stop any cleanup while exceptions remain.
6. Build a repair queue with exact source IDs, observed and expected hashes/paths, proposed safe restoration source and risks. Restoration or removal requires a new action-bound approval and separately capable adapter.

## Output and verification

Return `verified_full`, `verified_sample`, `partial` or `blocked`; baseline ID, coverage, expected/actual counts and bytes, hash and readability outcomes, backup confidence, exception classes, journal reconciliation and repair queue. Declare full integrity only when every expected item is checked, no unresolved exceptions remain and sources are preserved as planned.

## Mode, capability and limit

`mock` verifies synthetic three-record in-memory copy by counts, bytes and SHA-256, including corrupt or partial target failure. It does not probe real media, backup restore or host filesystems. `read_only` may inspect a real archive with available adapter; no repair is performed. Local `friday.skill.*` records are drafts, not published dashboard events.
