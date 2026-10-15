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

1. Confirm source IDs/hashes, audience, purpose, privacy/rights scope, target length and aspect ratio. Resolve missing assets and unavailable codecs before proposing a render. Use a reviewed `friday-family-highlight-selector` list or build an equivalent selection without assuming person identity or publication consent.
2. Draft a scene-by-scene storyboard, then an edit decision list: source ID, in/out points, order, target duration, transition, caption evidence, crop policy and soundtrack. Preserve uncertainty in dates or names rather than putting a guess into captions. Check selection and timeline coverage before media processing.
3. Build a rights ledger per visual and audio asset, including who supplied it, allowed audience/use, license or permission evidence and unresolved restrictions. Silence is the safe default if music rights are unknown; do not substitute an unlicensed track. Paid generation, remote upload or publication needs separate exact destination and cost approval.
4. When a verified local renderer exists, request `friday-approval-policy` for the exact output path and payload, render a preview to a new file and leave originals intact. Review scene order, crop, names, transitions, flicker and audio, then lock revisions and export a distinct final file. Without renderer, provide the storyboard and edit decision list only.
5. Independently probe and play or decode the complete exported file, checking frame size, duration, codec, sound levels or intentional silence, source ledger, and end-frame integrity. A renderer exit code alone is insufficient. Record failed export and repair steps without overwriting the last accepted version.

**Mode and capability:** mock: storyboard only with synthetic assets; read_only: timeline and render command proposal; live: an available local media tool may render to a new path after output/capability approval. This package has no real media renderer, probe, rights checker or exporter. Missing encoder yields an edit decision list rather than a fictional video.

**Risk and approval:** Remote generation or publication requires separate consent for every person and destination where relevant. Do not embed sensitive GPS or unreviewed names in captions. A paid asset purchase or external upload is tier 3.

**Workflow source:** The preview, locked timeline and independent playback gates are adapted as procedure ideas from the MIT-licensed [Hermes AI presenter video skill](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/ai-presenter-video/SKILL.md). This family-media skill does not include that skill's scripts, providers or presenter-specific assumptions.

**Output and verification:** Output preview/final paths only if files were created, otherwise edit plan; include source and rights ledgers, render settings, review state and playback/probe evidence. Preserve previous exports for rollback. A local `friday.skill.*` lifecycle record is an internal draft, never proof of dashboard delivery.
