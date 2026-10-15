---
name: friday-archive-migrator
description: Run an exact approved archive copy batch with source recheck, durable journal, hash verification and safe resume when a real adapter exists.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, archive, files]
---

# Archive migrator

Use only after `friday-archive-reorganization-plan` supplies a reviewed item-level manifest. A plan alone does not grant execution. Prefer copy-first; leave originals in place.

## Inputs and capability: execution gate

Require trusted host file adapter, current source identities/hashes, target root identity, sufficient free space including temp overhead, verified backup and a durable journal. Obtain Tier 2 approval bound to canonical manifest fingerprint, operation, destination, source set and expiry. Reject stale, denied, replayed or mismatched grants; changed plan needs a new grant. Overwrite, broad move or original deletion is a separate higher-risk action and never implicit here.

## Per-item state machine

1. Before each batch, recheck root containment, symlink/junction boundaries, case/Unicode collision, source identity/hash, destination absence, backup freshness, capacity and approval. Abort without side effects if any prerequisite fails.
2. Append and flush a journal record with operation ID, manifest hash, source ID/path/hash, destination, temp path, timestamp and state `planned`. Record state changes durably as `copying`, `copied`, `verified`, `finalized` or `failed`; never describe an unwritten state as persisted.
3. Copy to a unique temporary file on the destination volume. After full byte count and SHA-256 readback match, finalize without overwrite using an atomic operation supported by that filesystem. If atomic no-clobber finalization is unavailable, block and choose a reviewed alternative. Preserve metadata only when explicitly specified and verify it separately.
4. Reopen the final path, verify bytes/hash and record final state. Preserve source throughout. On retry, inspect journal **and** filesystem: skip only a finalized file whose present bytes/hash match; reconcile temp or unknown state before retry. Never blindly overwrite an existing destination.
5. On failure or interruption, stop the batch and report state as `partial` or `unknown`, not complete. Keep source and backup. A rollback manifest may identify only copies created by this operation; removal of a verified new copy needs a separately scoped approval. Do not roll back by deleting an ambiguous pre-existing file.

## Output and verification

Return manifest/grant IDs, per-item state, committed journal location, source and destination hashes, copied/verified bytes, conflicts, stopped reason, remaining work and rollback candidates. Complete only after `friday-archive-integrity-check` independently reconciles every expected item, counts and hashes.

## Mode, capability and limit

`read_only` emits execution preview. Existing `adapters/archive_e2e_mock.py` uses in-memory bytes and a simulated test grant only; its `partial_copy` case detects a missing target but does not implement durable journaling, real resume, atomic finalization or filesystem rollback. Without a real trusted adapter and journal, execution is blocked. Local `friday.skill.*` records are drafts, not published dashboard events.
