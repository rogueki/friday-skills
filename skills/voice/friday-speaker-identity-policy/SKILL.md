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

**Inputs:** verifier result, result timestamp/session binding, requested action and risk tier, configured mode, available independent approval factors.

Accept only these states: `verified_owner`, `unknown`, `rejected`, `replay_suspected`, `verification_unavailable`. Require the verifier to bind its result to the current session and to report freshness. Never turn missing or malformed results into `verified_owner`.

1. `verified_owner` permits only the owner-scoped actions allowed by the applicable tier and current session policy.
2. `unknown`, `rejected`, `replay_suspected`, and `verification_unavailable` deny owner-only actions. For `replay_suspected`, stop the voice action and recommend a trusted alternate channel; do not reveal whether a protected account exists.
3. A stale, unbound, conflicting or unavailable verifier result is equivalent to `verification_unavailable` (fail closed).
4. A verified speaker is not sufficient approval for Tier 3. Require the independent hard approval and second factor through a trusted non-voice mechanism; if absent, return `waiting_approval`.
5. Never enroll, remove, or alter voice profiles through this procedure. Such changes require a separately designed, explicitly approved identity-management flow.

**Modes:** `mock` accepts only clearly labeled fixtures and can never authorize a live action. `read_only` can report the state and propose next steps. `live` still requires a real verifier capability and all tier gates.

**Output:** state, freshness/session-binding check, allowed scope (if any), denied actions, independent approvals required, and verification evidence. Do not output biometric samples or secrets.

**Risk and approval:** Identity is an input to policy, not an approval grant. Tier 2 needs explicit confirmation. Tier 3 requires a separate hard gate plus second factor; voice alone never qualifies.

**Failure:** On any uncertainty deny privileged action and disclose a neutral reason. Do not fall back to text similarity or another model's guess.

**Verification:** Confirm one of the five accepted states, current session binding and freshness, and that only the allowed scope proceeds. No successful identity claim without an actual verifier observation.
