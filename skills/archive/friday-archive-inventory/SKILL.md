---
name: friday-archive-inventory
description: Inventory disks and folders read-only with file types, sizes, date ranges, duplicates suspicion, damage and backup evidence.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# archive inventory

**Use:** Use for the first survey of an archive or drive. Do not reorganize or delete in this skill.

**Inputs:** Approved root paths, device identifiers, exclusion list, access rights, hash/probe capability, backup inventory and operating mode.

## Procedure

1. Confirm provenance, path scope and capability. Walk only allowed roots without following unexpected junctions or symlinks. Record volume ID, path, size, type, modification time, capture date where present, readable status and errors. Aggregate by directory, type and period. Identify duplicate *suspects* by size/name or hash if explicitly computed. Record backup evidence with its observation date; unknown is not backed up. Keep inaccessible locations in a gap list.
2. Classify any proposed write through `friday-approval-policy` and bind approval to exact paths and payload before execution.

**Mode and capability:** mock: synthetic tree; read_only: inventory manifest and summary; live: read adapter may scan but no filesystem writes except approved report. Missing permissions yield partial coverage.

**Risk and approval:** Read-only on first pass. Avoid reading private content when metadata suffices; do not transmit filenames, GPS or file content externally without authorization.

**Output and verification:** Output volume coverage, counts, bytes, date ranges, unreadable items, backup status and inventory timestamp. Verify sampled counts against source and report traversal errors; stale backup claims require fresh evidence. Local `friday.skill.*` records are drafts, not published dashboard events.
