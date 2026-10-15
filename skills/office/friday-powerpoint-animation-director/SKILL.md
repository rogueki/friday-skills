---
name: friday-powerpoint-animation-director
description: Design and verify purposeful PowerPoint builds and transitions for a particular talk and audience.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, office, powerpoint, motion]
---

# PowerPoint animation direction

Use when a deck's reveal sequence, transitions or timing support a presenter. Do not animate solely for decoration or claim a static PPTX preview proves playback.

**Inputs:** deck copy, speaker notes and run-of-show, slide order, audience and venue, presentation duration, accessibility constraints, target PowerPoint version, mode and Office automation capability.

1. Assign each proposed animation a communication purpose: reveal a comparison, prevent reading ahead or show causality. Prefer none when the static slide is already clear.
2. Specify object order, trigger, duration, delay and transition per slide; keep similar sequences consistent. Avoid long automatic advances where the speaker needs control, and provide a reduced-motion/static reading path.
3. Copy the source deck before edits. Apply supported effects only through a confirmed Windows Office Worker capable of handling animation metadata. Do not use a generic PPTX library if it may discard existing animations.
4. Verify actual slideshow playback and exported static view on representative and edge slides. Check reveal order against notes, chart labels, contrast and total time; route layout defects to presentation QA.

**Mode/capability:** `mock` produces an annotated cue sheet; `read_only` inspects animations where supported; `live` creates a new version in an authorized workspace. Review is Tier 0; local reversible output Tier 1; publication/sharing Tier 2. Keep original and brand assets private.

**Output:** slide/object cue sheet, revised artifact if produced, playback evidence and known unsupported effects. **Failure:** If Office playback or edit capability is absent, return `partial` and a precise animation spec; never mark a motion change visually verified from file metadata alone.

## Cue and playback contract

- Identify objects by slide number plus stable visible label; specify start condition (`on-click`, `with-previous` or `after-previous`), order, duration, delay and exit behavior. Include a speaker cue and the reason for each effect. Time the complete sequence against the talk, including pauses.
- Maintain a static export that carries the full meaning and a reduced-motion path. Check contrast and focus/read order for each intermediate state; do not hide essential labels until after a timed transition.
- Before editing an existing deck, record file hash and animation inventory and choose a tool proven to retain its unsupported effects. After editing, compare object count, notes and animated sequence on every affected slide in target PowerPoint playback. A PDF or static render verifies final appearance only.
- If Windows Office automation or playback is unavailable, leave the original untouched, deliver the cue sheet, mark application/playback `NOT_RUN` and overall execution `partial`. The E2E7 synthetic PPTX has no native animation evidence.
