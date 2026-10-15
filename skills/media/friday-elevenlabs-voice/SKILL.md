---
name: friday-elevenlabs-voice
description: Prepare reviewed narration and request MP3 speech through the F.R.I.D.A.Y. ElevenLabs server adapter.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, content-studio, media]
---

# friday-elevenlabs-voice

**Use:** For approved narration and MP3 synthesis. Do not use for unauthorized voice imitation or automatic publication.

**Inputs:** Reviewed text, voice ID with use rights, language, pronunciation, target duration, cost decision and mode.

1. Fact-check and approve a short narration. Confirm the voice has permission for the intended audience and commercial use.
2. When configured, call the authenticated F.R.I.D.A.Y. server `POST /api/v1/content-studio/elevenlabs/speech` with `text`, `voiceId`, `confirmed: true` and an Idempotency-Key. The server uses ElevenLabs `eleven_multilingual_v2`, MP3 44.1 kHz/128 kbps, and a server-only key. This skill never handles a key.
3. Save the returned MP3 to a new reviewed output path. Do not retry automatically after timeout or unknown outcome; a second call may cost money.
4. Listen from beginning to end; inspect clipping, pronunciation, pauses and duration, then hand the accepted file to the edit plan.

**Mode and capability:** mock produces script and request only; read_only checks text/rights; live requires authenticated dashboard API bridge and configured ElevenLabs key. This Skills repository has no standalone bridge or downloader. `voice.speak` and `file.write` are conditional capabilities.

**Output and verification:** Provide approved script, voice ID, response file path only if saved, and playback evidence. Never claim a generated MP3 from a mock.

Official API: https://elevenlabs.io/docs/api-reference/text-to-speech/convert
