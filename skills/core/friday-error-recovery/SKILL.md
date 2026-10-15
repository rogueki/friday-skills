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

1. Classify as transient, authentication required, approval required, invalid input, external outage, partial success or nonrecoverable. Read the actual error and logs; never infer a reason from timeout alone.
2. For an external write with ambiguous outcome, query the authoritative system by idempotency key or object ID before considering retry. If reconciliation is unavailable, stop and report unknown state.
3. Retry only transient failures, with the same idempotency key, still-valid approval and fresh capability. Limit to at most two retries with backoff; after repeated identical failure, change diagnosis rather than looping.
4. Record successful substeps and untouched substeps separately. Do not roll back without a defined, authorized compensation action.

Output normalized `partial`, `blocked` or `failed` result and a precise next step. Verify recovery from the authoritative response and close the parent task only when all acceptance conditions are met.
