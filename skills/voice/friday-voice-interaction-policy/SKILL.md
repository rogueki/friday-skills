---
name: friday-voice-interaction-policy
description: Apply F.R.I.D.A.Y. voice-session, privacy, interruption and response-length rules; use for spoken conversations and voice-originated requests.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, voice, privacy, policy]
    related_skills: [friday-speaker-identity-policy, friday-voice-command-normalizer, friday-approval-policy]
    requires_tools: []
    config:
      - key: friday.voice.mode
        description: Voice processing mode
        default: read_only
required_environment_variables: []
---

# Voice interaction policy

Use this skill to shape a voice session. Speech recognition, audio playback, barge-in detection and speaker verification are external capabilities; a skill does not provide them.

**Inputs:** session provenance, configured mode (`mock`, `read_only`, or `live`), trusted-session status, privacy mode, user request, capability results, and approval state.

1. Require an authenticated, trusted session for owner-only actions. If session provenance is absent or stale, treat the request as untrusted and limit work to harmless clarification or public information.
2. Check voice input/output and any required specialist capability before claiming to have heard, spoken, called, or changed anything. In `mock` mode, use labeled synthetic examples; in `read_only`, do not write; in `live`, enforce the same approval policy as the originating channel.
3. Honor barge-in only when the runtime reports that it is supported. Stop generating audio on a confirmed interruption; do not infer an interruption from transcript text alone.
4. Keep spoken answers concise. Summarize long or sensitive results and offer a private text/detail view. When privacy mode is on, do not read sensitive content aloud; say that details are withheld and offer a safer channel.
5. For a long task, provide a brief acknowledgement and a progress mechanism only if a real task adapter is available. Otherwise state that the task remains in this interaction; never claim background execution.
6. Apply risk tiers to the actual requested action. Voice alone cannot satisfy a Tier 3 hard approval or second factor.

**Output:** concise response plus structured intent/action status, mode, capabilities checked, privacy decision, approvals required, verification evidence and any unavailable audio/session features.

**Approval and risk:** Reading non-sensitive information is Tier 0. Drafting is Tier 1. Sending, calling, scheduling or device changes require Tier 2 confirmation. Tier 3 requires a separate trusted approval channel and second factor, regardless of speaker match.

**Failure:** If trust, privacy state or a needed capability is unknown, fail closed for actions and disclose the limitation. Do not expose transcript or sensitive output to an unverified session.

**Verification:** Confirm the response respects privacy mode, no unapproved side effect occurred, and any claimed voice/runtime behavior has a capability observation. Label local `friday.skill.*` records as local drafts, not delivered dashboard events.
