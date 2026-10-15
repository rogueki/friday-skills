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

1. Confirm manifest IDs/hashes, approved roots, target volume, backup evidence and actual local file adapter. Use embedded capture date only with timezone/uncertainty preserved; place unknown or conflicting dates in a review bucket, not the current month by default.
2. Choose `YYYY-MM_Event` or `YYYY-MM-DD_Location_Event` and sanitize labels for target filesystem rules, path length, case folding and reserved names. Reject traversal, symlink/junction escape, target inside source, and same-name or same-case collisions. Distinct hashes must never be silently merged under one path.
3. Produce a dry-run mapping with stable ID, original path, proposed path, byte size, SHA-256 and naming evidence. Include count, required free space, backup status, collisions and exact rollback map. Stop on missing backup or capacity evidence where a bulk move is planned.
4. For execution, request `friday-approval-policy` bound to the complete manifest and paths. Prefer copy-first to a new path, rehash and verify target count/bytes, record operation state and retain originals. A move or original cleanup is a separately reviewed action; do not infer permission for deletion from copy approval.
5. On partial runs, reconcile logged state against actual source and target hashes before retry. Do not overwrite or repeat an uncertain operation blindly. Return unresolved conflicts for human selection.

**Mode and capability:** mock: synthetic mapping; read_only: dry-run manifest; live: file adapter may copy or move only approved exact paths, with resume and conflict handling. This package has only a synthetic in-memory E2E6 archive copy scenario, no real media organizer or filesystem migration adapter. Missing adapter or backup evidence leaves a plan.

**Risk and approval:** Moving personal media can disrupt links and sync. Large bulk moves are tier 2; destructive removal is a separate higher-risk action. Never merge different hashes under one name.

**Output and verification:** Output mapping, naming evidence, conflicts, backup/capacity state and rollback instructions. Complete only after target count, bytes and hashes match, sources remain intact under copy semantics, and operation log reconciles; otherwise report partial/blocked. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
