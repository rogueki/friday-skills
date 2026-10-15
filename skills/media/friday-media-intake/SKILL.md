---
name: friday-media-intake
description: Register new family photos and videos with metadata, hashes and corruption checks while preserving originals; skip curation or moving.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# media intake

**Use:** Use when new photo or video files must be inventoried before curation or archiving. Do not move, rename, delete or upload originals during intake.

**Inputs:** Authorized source roots, file list, privacy scope, supported metadata/hash reader, storage capacity and operating mode.

## Procedure

1. Establish the authorized root, exclusions, privacy scope and actual reader capability before scanning. If there is no local filesystem/metadata adapter, request an existing manifest and produce an intake plan; do not claim to have found new files. Reject paths outside the root, junction/symlink escapes and unexpected network mounts.
2. For every readable item record a stable source ID, original path, byte size, extension, observed format, filesystem modification time, metadata reader and observation time. Hash the complete bytes with streaming SHA-256. Recheck size and modification time after reading; if either changed, mark the item unstable instead of treating the first hash as durable.
3. Keep embedded capture timestamp, its UTC offset or timezone evidence, and filesystem time as separate fields. Do not infer a local timezone from the machine clock or sort uncertain timestamps as exact. Record device metadata only when useful; keep GPS in restricted local fields only when the user permits it, and omit coordinates from ordinary summaries.
4. Probe only supported formats using read-only handles or copies. Distinguish unsupported codec/RAW, missing parser, unreadable file, truncated or failed decode, and probable corruption. A failed thumbnail alone does not prove source corruption. Do not repair, rename, move or delete originals in intake.
5. Produce the manifest and a gap list for inaccessible/unstable/unsupported items. Before any report write or external transfer invoke `friday-approval-policy` for the exact target and payload; keep this separate from approval to read the source.

**Mode and capability:** mock: synthetic media only; read_only: manifest in memory or approved local report, no mutations; live: only an installed, verified file adapter may produce a local manifest. This package has no real media scanner or parser. Missing parser, hash tool or permissions yields partial entries with explicit reason.

**Risk and approval:** GPS and family identities are sensitive. Strip precise location from ordinary summaries and do not send media or metadata to a remote model without a trusted, approved path. Any destination write uses approval policy; external upload needs its own bound authorization.

**Output and verification:** Output manifest with source IDs, paths, times with uncertainty, hash algorithm, coverage, unsupported/unreadable/probably corrupt counts and errors. Compare enumerated count with manifest plus gap count; rehash a sample only when actual source access exists. Unstable files require a fresh scan. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
