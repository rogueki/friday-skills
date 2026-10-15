---
name: friday-speaker-identity-policy
description: Interpret speaker-verification states for voice requests and apply fail-closed identity policy; use when authorization depends on who is speaking.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, voice, identity, security]
    related_skills: [friday-voice-interaction-policy, friday-approval-policy]
    requires_tools: []
    config:
      - key: friday.speaker.mode
        description: Speaker verification mode
        default: read_only
required_environment_variables: []
---

# Speaker identity policy

Voice biometrics and liveness/replay detection are external services. This skill interprets their explicit result; it cannot identify a person from wording, familiarity, a transcript, or a voice sample by itself.

**When to use:** Use this policy whenever an action depends on whether the current voice speaker is the account owner, when a voice session returns an identity state, or when replay/liveness uncertainty affects authorization. Do not use it for ordinary requests whose authorization does not depend on speaker identity.

**Inputs:** host-authenticated verifier result, verifier/attestation source, result and expiry timestamps, session ID, challenge/utterance binding, requested action and risk tier, configured mode, available independent approval factors. Do not ingest raw voiceprints, embeddings or audio into the skill context.

Accept only these states: `verified_owner`, `unknown`, `rejected`, `replay_suspected`, `verification_unavailable`. Require a trusted verifier capability to bind the result to this session and utterance/challenge and report validity. A copied transcript, caller-provided JSON or previous-turn result is not an attestation. Missing, expired, malformed or conflicting evidence becomes `verification_unavailable`; never turn it into `verified_owner`.

1. `verified_owner` is valid only for the bound fresh utterance/session. It permits consideration of owner-scoped actions under the applicable capability, tier and approval policy; it is not an approval grant.
2. `unknown` allows neutral clarification/public information only. `rejected` denies owner-only actions and should not disclose account state. `replay_suspected` stops the voice action, invalidates this voice attempt and points to a trusted alternate channel. `verification_unavailable` denies privileged voice action while verifier health is unresolved.
3. On speaker handoff, session resume or a fresh command requiring owner scope, obtain a new trusted result. Never reuse a cached result solely because the voice sounds familiar.
4. A verified speaker is not sufficient approval for Tier 3. Require the independent hard approval and second factor through a trusted non-voice mechanism; if absent, return `waiting_approval`.
5. Never enroll, remove, or alter voice profiles through this procedure. Such changes require a separately designed, explicitly approved identity-management flow.

**Modes:** `mock` accepts only clearly labeled fixtures and can never authorize a live action. `read_only` can report the state and propose next steps. `live` still requires a real verifier capability and all tier gates.

**Output:** accepted state or `verification_unavailable`, verifier provenance and binding/freshness outcome, allowed scope (if any), denied actions, independent approvals required, and minimal evidence reference. Do not output biometric samples, templates, challenge secrets or raw audio.

**Risk and approval:** Identity is an input to policy, not an approval grant. Tier 2 needs explicit confirmation. Tier 3 requires a separate hard gate plus second factor; voice alone never qualifies.

**Failure:** On any uncertainty deny privileged action and disclose a neutral reason. Do not fall back to text similarity or another model's guess.

**Verification:** Exercise all five states plus missing attestation, stale result, different session/utterance, replay indication and Tier 3 voice-only attempt. Confirm only the allowed scope proceeds. No successful identity claim without an actual trusted verifier observation; no verifier adapter or biometric enrollment is implemented by this policy.
