---
name: friday-video-editing
description: Build a rights-aware edit decision list and guide manual CapCut or verified local export.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, content-studio, media]
---

# friday-video-editing

**Use:** For Content Studio social-video edit decisions and reviewed exports. Do not use to claim an automated CapCut integration or to publish a clip.

**Inputs:** Authorized source manifest, rights, aspect ratio, duration, frame rate, narration, captions, output path and mode.

1. Verify assets, rights and target platform. Preserve originals. Build an edit decision list with source IDs, in/out timecodes, transitions, crops, title-safe captions and audio levels.
2. Give named assets and edit decisions to a human CapCut workflow. A saved CapCut key does not prove a public automation API; do not claim or invoke one.
3. If a verified local renderer is available, export a new preview and then a distinct final file after review. The legacy `Content-Studio/engine/content_engine.py` is read-only reference material, not an installed renderer in this Skills package.
4. Play the exported video and probe duration, codec, final frame, subtitle legibility and audio. Keep the previous accepted export for rollback.

**Mode and capability:** mock yields an edit plan; read_only checks assets; live may render only with an installed verified local tool and approved output path. `media.read` is required; `media.render` and `file.write` are conditional.

**Output and verification:** Deliver the edit decision list and rights ledger. Include actual output paths only for files that exist and have passed playback/probe checks.
