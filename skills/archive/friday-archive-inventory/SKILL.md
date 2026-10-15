---
name: friday-archive-inventory
description: "Archive census: file types, sizes, dates and duplicates. Flag unreadable items and check backup evidence; read-only, no file moves."
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# Archive inventory

Use for the first survey of a disk or archive. This skill produces evidence for `friday-duplicate-detector` and `friday-archive-reorganization-plan`; do not move or delete files.

## Inputs and capability

Require allowed roots and volume identifiers, exclusions, scan time, read capability and report destination. Record whether source can change during scanning. An unknown root or unavailable adapter is blocked, not an empty archive. Start with metadata. Hash or decode content only when scope and adapter permit it. Keep filenames, GPS, faces and private content local unless separate disclosure is authorized. Check backup evidence independently: snapshot ID, covered roots, observation time and restore or sample read. A configured job or old status alone means `backup=unverified`.

## Procedure

1. Walk allowed roots without following symlinks, Windows junctions, mount points or reparse points into another location. Record links and access failures as coverage gaps. Track volume and stable file identity where available; a path alone is unstable across renames.
2. Record `source_id`, volume, relative path, type, size, modified time and timestamp provenance. Prefer embedded capture time only when parsed and timezone known; keep filesystem time separately. Unknown dates remain unknown.
3. Mark read errors, changed-during-scan files and unsupported formats. Record successful SHA-256 with algorithm and observation time. Size, name or timestamp coincidences are duplicate suspects only.
4. Aggregate counts and bytes by root, directory, type and period. Keep skipped, inaccessible, changing and unreadable counts distinct. Flag corruption only with valid read or decoder evidence; unreadable alone does not prove corruption.
5. Reconcile totals with traversal log and sample source entries. Changed entries need rescan before planning.

## Output and verification

Return `scan_id`, scan window, roots/volumes, exclusions, adapter and coverage, per-item records, counts/bytes, date provenance, errors, link boundaries, duplicate suspects and backup evidence. State `complete`, `partial` or `blocked` and why. Plans must reference the scan ID and recheck stale identities.

## Mode, capability and approval

`mock` uses pinned synthetic fixture only. For an explicitly allowed, local absolute root, the opt-in `adapters/local_archive_reader.py` supplies a bounded real read-only file/hash inventory with scan ID, UTC window and applied limits; see `docs/LOCAL_ARCHIVE_READER.md`. Its `complete` state includes a genuinely empty root; `partial` requires coverage review. A scan ID correlates one run, not immutable content. It supplies filesystem timestamps only, not media dates, EXIF, corruption findings or backup status. Windows concurrent path-swap safety is not guaranteed. Inventory grants no write permission; a report write needs a separately approved path. `adapters/archive_e2e_mock.py` is the separate three-record in-memory E2E6 simulation, not this adapter or a Hermes runtime test. Local `friday.skill.*` records are drafts, not published dashboard events.
