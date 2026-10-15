---
name: friday-family-highlight-selector
description: Select balanced family trip, birthday and school highlights across people and moments for a requested story.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# family highlight selector

**Use:** Use when the goal is a small, balanced highlight set from a family event. Do not use for broad defect grading or final video rendering.

**Inputs:** Event-tagged media manifest, participants only if voluntarily supplied, duration or photo-count target, privacy boundaries and available local analysis.

## Procedure

1. Confirm source provenance, current capability and approved scope. Build an event timeline and clusters for arrival, activities, candid moments and closing. Sample across days, scenes and participants without forcing equal counts or inferring unprovided identities. Combine quality evidence from photo curation with story value and user favorites. Include a few varied formats; flag gaps and ask for human review of sensitive or uncertain selections. Export a selection manifest suitable for a video or photobook plan.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: synthetic timeline; read_only: ranked shortlist; live: approved local adapter may create copies or a non-destructive album. If event labels are absent, group by capture window and disclose the weak inference.

**Risk and approval:** Children's images and school context stay private. Publication, sharing and cloud sync require a separate exact-recipient approval. Do not interpret facial appearance as consent.

**Output and verification:** Output selected IDs, event coverage and exclusions with reasons. Verify selected paths still match source hashes and no excluded private item appears. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
