---
name: friday-photo-curator
description: Rank and group family photos for review by image quality, duplicates, bursts and event context without automatic deletion.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# photo curator

**Use:** Use when a user asks which photos to keep or highlight from an existing collection. Do not replace an archive inventory or infer a person's identity.

**Inputs:** Source manifest or approved read paths, event context, desired output count, local visual-analysis capability, privacy preferences and operating mode.

## Procedure

1. Confirm source provenance, current capability and approved scope. Group exact duplicates by hash, then near duplicates and bursts using capture time and local image similarity if available. Score focus, exposure and composition independently; describe score reasons and keep technically imperfect but meaningful moments eligible. Use face expression signals only through a consented local capability, never identity recognition by default. Produce representative picks and a review queue for ambiguous groups. Separate selection from physical quarantine or deletion.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: synthetic scored examples; read_only: selections and proposed quarantine list; live: only an approved adapter may create review copies or quarantine after exact-path preview. If visual analysis is absent, fall back to metadata grouping and manual review.

**Risk and approval:** Never delete automatically. Keep originals and private family media local unless separately authorized. Treat score as advisory, especially for children and emotional significance.

**Output and verification:** Output ranked groups with reasons, confidence and original paths. Verify every pick exists and duplicates are represented accurately; disclose unscored or undecodable items. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
