---
name: friday-error-recovery
description: Recover from F.R.I.D.A.Y. tool and adapter failures with bounded retries, idempotency and partial-success accounting.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, recovery, core]
---

# Error recovery

Use after an actual failure or ambiguous timeout. Do not retry a successful operation or use this skill to override an approval denial. Inputs: error class, operation, attempt count, idempotency key, observed side effects, adapter health, mode and approval state.

1. Classify the observed response as retryable transient, authentication required, approval required, invalid input, external outage, partial success or nonrecoverable. Record operation stage (`before_dispatch`, `after_dispatch`, `response_validation`) and evidence; a timeout or malformed success after dispatch is an **unknown side-effect state**, not evidence of failure.
2. For a possibly dispatched write, freeze dependent writes and query the authoritative system using the original idempotency key, object ID or provider receipt. Compare target, payload fingerprint and resulting state. If reconciliation is unavailable or inconclusive, stop with `partial` or `blocked` and a specific manual check; never create a second operation with a fresh key.
3. Retry only a proven transient failure whose effect is known absent or whose adapter guarantees replay with the same key. Recheck current capability, mode, action-bound approval and expiry before dispatch. Use at most two retries with bounded backoff; 401/403, approval denial, invalid input, 409 conflict and unknown outcome require diagnosis or reconciliation, not blind retry.
4. Keep a ledger of verified completed steps, unresolved effects and untouched steps. Compensation is a new risk-classified action with its own approval when required. Do not call local mock receipts or task proposals provider success.

Output normalized `partial`, `blocked` or `failed` result and a precise next step; use `completed` only after fresh authoritative evidence resolves the failure and all acceptance conditions. Preserve opaque correlation IDs, not secrets or raw provider payloads.
