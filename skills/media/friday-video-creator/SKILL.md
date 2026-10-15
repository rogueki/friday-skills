---
name: friday-video-creator
description: Plan and render a reviewed family film or highlight reel from authorized media with rights-safe audio.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, media, family]
---

# video creator

**Use:** Use for a family film, short reel or year recap that needs storyline, scene plan, rendering and review. Do not use solely to select still photos.

**Inputs:** Approved source manifest, target audience, length, aspect ratio, story beats, music license evidence, local encoder capability, output path and mode.

## Procedure

1. Confirm source provenance, current capability and approved scope. Select media with the highlight selector, draft a timeline and shot list, then specify transitions, captions, audio levels and credits. Confirm music and image rights before incorporation; silence is the fallback. Render to a new file while originals remain untouched. Create preview, collect corrections, then export the reviewed version. Validate codec, duration, frame size, audible levels and that every input came from the approved set.
2. Before any effect beyond a local draft, invoke `friday-approval-policy` with exact targets and payload; honor the mode boundary.

**Mode and capability:** mock: storyboard only with synthetic assets; read_only: timeline and render command proposal; live: an available local media tool may render to a new path after output/capability approval. Missing encoder yields an edit decision list rather than a fictional video.

**Risk and approval:** Remote generation or publication requires separate consent for every person and destination where relevant. Do not embed sensitive GPS or unreviewed names in captions. A paid asset purchase or external upload is tier 3.

**Output and verification:** Output preview path or edit plan, source and rights ledger, settings and review state. Verify the playable output independently; a successful process exit is insufficient. Preserve previous exports for rollback. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
