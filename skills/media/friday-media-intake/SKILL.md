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

1. Confirm source provenance, current capability and approved scope. Enumerate only approved roots with symlink and exclusion rules. Record original path, byte size, extension, capture time with timezone and uncertainty, device metadata, optional GPS only when needed and consented, and a streaming SHA-256 hash. Compare capture time with filesystem time without silently replacing one with the other. Decode or probe supported formats on a copy or read-only handle; classify unreadable files separately from unsupported codecs. Write an intake manifest with stable source IDs and provenance. Route organization or repair to their own skills.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: synthetic media only; read_only: manifest in memory or approved local report, no mutations; live: verified file adapter may produce a local manifest, with no automatic relocation. Missing parser, hash tool or permissions yields partial entries with explicit reason.

**Risk and approval:** GPS and family identities are sensitive. Strip precise location from ordinary summaries and do not send media or metadata to a remote model without a trusted, approved path. Any destination write uses approval policy; external upload needs its own bound authorization.

**Output and verification:** Output manifest, unsupported/corrupt counts, hash algorithm and exceptions. Verify sampled hashes and file counts against the scanned source. If a file changes during hashing, mark it unstable and rescan; never claim it is corrupt merely because parsing failed. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
