---
name: friday-archive-reorganization-plan
description: Design a conflict-aware archive target tree and reversible copy or move manifest before execution.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# archive reorganization plan

**Use:** Use to plan broad archive restructuring across disks or folders. Do not execute migration.

**Inputs:** Current inventory, desired taxonomy and naming rules, destination capacity, filesystem limits, backup status, duplicate review and mode.

## Procedure

1. Confirm provenance, path scope and capability. Propose target tree by year, event and media type while preserving unknown-date and unclassified buckets. Build item-level old/new path mapping, operation type, source hash and collision policy. Check destination space including temporary copy overhead, path length, reserved names, case sensitivity and cross-volume behavior. Sequence small batches; calculate downtime and interruption points. Document backup prerequisite and rollback mapping, including how to restore original paths if a batch fails.
2. Classify any proposed write through `friday-approval-policy` and bind approval to exact paths and payload before execution.

**Mode and capability:** mock: synthetic plan; read_only: dry-run only; live: may validate destination metadata but no migrations. Missing inventory or backup proof blocks execution readiness.

**Risk and approval:** Plan creation is tier 0/1; bulk migration is tier 2 and needs a separate action-bound approval. Never silently choose overwrite or delete.

**Output and verification:** Output dry-run manifest, conflict list, capacity calculation, backup evidence and rollback procedure. Verify all source IDs mapped once, all target paths unique after normalization and every source hash is available or marked unresolved. Local `friday.skill.*` records are drafts, not published dashboard events.
