---
name: friday-kie-media
description: Prepare and request reviewed image or video generations through the F.R.I.D.A.Y. kie.ai server adapter.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, content-studio, media]
---

# friday-kie-media

**Use:** For a reviewed Content Studio image or short video. Do not use for unreviewed paid generation or publication.

**Inputs:** Approved prompt, image/video kind, aspect ratio, rights evidence, cost expectation, review owner and mode.

1. Prepare a short prompt and obtain an explicit decision for the paid request. The Dashboard server supports `grok-imagine/text-to-image` and `kling-2.6/text-to-video` with a fixed 5-second video and sound off. Check current provider pricing before quoting cost.
2. Only when the Content Studio toggle and server key are configured, send the confirmed request to F.R.I.D.A.Y.'s `POST /api/v1/content-studio/kie/tasks` with an Idempotency-Key. The dashboard API, not this Hermes skill, owns the key. No direct browser or skill-side provider secret.
3. Poll `GET /api/v1/content-studio/kie/tasks/{id}` for that task. A timeout after creation means unknown outcome; use the recorded task ID or investigate before any new paid request.
4. Inspect result media and usage before adding it to the content plan. HTTPS result links are provider references; local download and media verification require a separate adapter.

**Mode and capability:** mock only describes the request; read_only reviews prompt and status; live needs an authenticated dashboard API bridge, configured key and exact payment confirmation. This Skills repository does not itself ship that bridge. `media.render` and `file.write` are conditional capabilities.

**Output and verification:** Return task ID, model, prompt version, state, consumed credits if reported, result links and review outcome. Verify the returned media independently.

Official API: https://docs.kie.ai/market/grok-imagine/text-to-image ; https://docs.kie.ai/market/kling/text-to-video ; https://docs.kie.ai/market/common/get-task-detail
