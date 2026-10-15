---
name: friday-archive-integrity-check
description: Compare source, destination and backup manifests by hashes, counts, readability and tree structure.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# archive integrity check

**Use:** Use after migration, backup or periodic archive audit. Do not perform the migration or automatic repair.

**Inputs:** Inventory and migration manifests, current destination roots, hash algorithm, sample or full-scan scope, backup evidence and mode.

## Procedure

1. Confirm provenance, path scope and capability. Normalize manifest IDs and path mappings. Count files and bytes by branch, compare SHA-256 to recorded source hashes, and probe supported media readability separately. Detect missing, extra, changed, unreadable and wrong-location files. Verify backup sample or backup manifest rather than trusting a configured backup job. Distinguish full verification from sampling and record scan errors. Produce a repair queue with exact affected IDs and suggested safe restoration source.
2. Classify any proposed write through `friday-approval-policy` and bind approval to exact paths and payload before execution.

**Mode and capability:** mock: synthetic manifests; read_only: compare and report; live: local reads only unless a separate repair adapter/action is approved. Missing source manifest limits findings to baseline-free inventory.

**Risk and approval:** Integrity checking must not mutate evidence. Restoration, deletion or replacement of files requires separately approved exact targets and backup validation.

**Output and verification:** Output match rate, exceptions, coverage, backup confidence and repair queue. Rehash a sample of matches and ensure every expected ID is accounted for before declaring the archive verified. Local `friday.skill.*` records are drafts, not published dashboard events.
