---
name: friday-duplicate-detector
description: Group exact and near duplicate archive files without automatically deleting any version.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# duplicate detector

**Use:** Use when asked to find repeated files or likely duplicate media. Do not decide archive moves or quality rankings alone.

**Inputs:** Inventory manifest, source roots, hash capability, supported image/video similarity tools, allowed compute budget and mode.

## Procedure

1. Confirm provenance, path scope and capability. Compare size as a cheap candidate filter, then streaming cryptographic hashes for exact duplicates. Compare metadata, perceptual image hashes and video fingerprints only when adapters exist and mark these as similarity, never equality. Group variants by format, edits, metadata and dimensions; preserve source IDs and confidence. Prepare review groups with a suggested canonical candidate and explain why, including backup location and provenance.
2. Classify any proposed write through `friday-approval-policy` and bind approval to exact paths and payload before execution.

**Mode and capability:** mock: synthetic groups; read_only: duplicate report; live: local analysis only, with no deletion. If perceptual tooling is absent, report exact-hash groups and defer near duplicates.

**Risk and approval:** No automatic deletion or dedupe links. A same hash proves byte equality, not that every path is disposable; retention and backup must be reviewed separately.

**Output and verification:** Output groups, method, hashes or similarity score and unresolved variants. Verify a sample of exact groups by recomputing hashes and do not collapse distinct files based on names or timestamps. Local `friday.skill.*` records are drafts, not published dashboard events.
