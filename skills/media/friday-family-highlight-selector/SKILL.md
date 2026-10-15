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

1. Fix event boundaries, target count or duration, audience, privacy scope and source manifest. Respect supplied event tags; when absent, make only a tentative capture-window grouping and identify uncertain timestamps.
2. Build a chronology with opening, main moments and closing. Balance dates, locations, activities, candid moments and user favorites. Include a few imperfect but meaningful images when they tell the event better than polished repetitions; do not force equal representation of people or infer unprovided identity, age or relationships.
3. Use `friday-photo-curator` evidence for quality and burst alternatives if available. Keep its technical rank distinct from story value. Mark likely duplicates and give a human a choice when a person, school context, embarrassment or privacy concern changes the selection.
4. Deliver a shortlist plus alternates, coverage table and missing-moment report with stable media IDs. Do not create a video, photobook, public album or shared link here. Before any local album write or transfer, invoke `friday-approval-policy` for the exact output and recipients.

**Mode and capability:** mock: synthetic timeline; read_only: ranked shortlist; live: an approved local adapter may create copies or a non-destructive album. This package has no real media selector or album writer. If event labels are absent, group by capture window and disclose the weak inference.

**Risk and approval:** Children's images and school context stay private. Publication, sharing and cloud sync require a separate exact-recipient approval. Do not interpret facial appearance as consent.

**Output and verification:** Output selected and alternate IDs in story order, event coverage, exclusions with reasons and items needing human review. Reconcile IDs and hashes against the source manifest; check every excluded private item is absent from the deliverable. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
