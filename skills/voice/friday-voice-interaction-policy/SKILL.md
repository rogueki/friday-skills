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

**Inputs:** runtime-supplied session ID, authenticated principal and trust source, authentication and last-presence timestamps, configured mode (`mock`, `read_only`, or `live`), privacy mode, transcript provenance, request, capability results, and approval state. Missing timestamps or an unknown session policy mean no owner action. The host defines and enforces the freshness window; the skill cannot refresh or authenticate a session.

1. Require an authenticated owner principal, current-session binding and a host-confirmed fresh trust decision for owner-only actions. Recheck after resume, device change, speaker change or a long-running task; do not carry an old approval or identity decision into a new session. If any input is absent, stale or conflicting, limit the reply to harmless clarification or public information.
2. Check voice input/output and any required specialist capability before claiming to have heard, spoken, called, or changed anything. In `mock` mode, use labeled synthetic examples; in `read_only`, do not write; in `live`, enforce the same approval policy as the originating channel.
3. Honor barge-in only on a runtime event bound to this session and current playback turn. Request cancellation of queued speech and mark it undelivered only after the runtime confirms cancellation; otherwise report playback as unverified. Re-evaluate the new utterance through identity, intent and approval checks. Do not infer interruption or successful cancellation from transcript text.
4. Keep spoken answers short and summarize complex results. For private data, consider both privacy mode and the output device/location supplied by the trusted host; if privacy mode is on or the environment is uncertain, withhold names, financial details, codes, addresses and other sensitive content from speech. Offer a trusted private text channel without silently sending details there.
5. For a long task, acknowledge once and return a task ID/progress channel only after a real task adapter accepts it. On progress or completion, recheck session, speaker and privacy state before speaking a result. If no adapter accepts the task, state that work remains in this interaction; never claim background execution.
6. Apply risk tiers to the actual requested action. Voice alone cannot satisfy a Tier 3 hard approval or second factor.

**Output:** concise response plus structured intent/action status, session/trust freshness outcome, mode, capabilities checked, privacy decision, approvals required, playback state (`not_started`, `playing`, `interrupted`, or `delivered` only when observed; otherwise `unverified`), task ID only when accepted by a real adapter, verification evidence and unavailable features. Keep transcript and sensitive content out of public telemetry.

**Approval and risk:** Reading non-sensitive information is Tier 0. Drafting is Tier 1. Sending, calling, scheduling or device changes require Tier 2 confirmation. Tier 3 requires a separate trusted approval channel and second factor, regardless of speaker match.

**Failure:** If trust, privacy state or a needed capability is unknown, fail closed for actions and disclose the limitation. Do not expose transcript or sensitive output to an unverified session.

**Verification:** Confirm the response respects privacy mode, every claimed playback/interruption/task transition has a host observation, and no unapproved side effect occurred. Test unknown/stale session, changed speaker, interrupted speech and task-resume cases before enabling a live adapter. Label local `friday.skill.*` records as local drafts, not delivered dashboard events.

The weather E2E4 local mock returns text suitable for a voice answer but sets `voice_playback={"status":"NOT_RUN","played":false}`. Do not report that the answer was spoken or heard unless a separate runtime confirms playback and session provenance.
