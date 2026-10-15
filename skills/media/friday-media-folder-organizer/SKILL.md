---
name: friday-media-folder-organizer
description: Propose and execute reversible media folder names by capture date and event with path-hash mapping.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# media folder organizer

**Use:** Use to organize already inventoried media into dated event folders. Do not perform broad archive migration or choose favorites.

**Inputs:** Verified intake manifest, naming mode YYYY-MM_Event or YYYY-MM-DD_Location_Event, target root, collision policy, free space, backup status and mode.

## Procedure

1. Confirm source provenance, current capability and approved scope. Normalize dates from trusted capture metadata, keeping unknown-date items in an explicit review bucket. Sanitize event/place labels for the target filesystem. Build a dry-run mapping of old path, new path and SHA-256; detect same-name collisions, cross-volume copies and symlinks. Obtain bound approval for actual moves. Prefer copy-first with rehash, then mark original cleanup as a separate decision. Record completed operations and rollback mapping.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: synthetic mapping; read_only: dry-run manifest; live: file adapter may copy or move only approved exact paths, with resume and conflict handling. Missing adapter or backup evidence leaves a plan.

**Risk and approval:** Moving personal media can disrupt links and sync. Large bulk moves are tier 2; destructive removal is a separate higher-risk action. Never merge different hashes under one name.

**Output and verification:** Output mapping, conflicts and rollback instructions. Verify counts and hashes at destination before considering a move complete; recover from partial runs using the operation log. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
