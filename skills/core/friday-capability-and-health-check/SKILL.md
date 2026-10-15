---
name: friday-capability-and-health-check
description: Verify fresh adapter availability, authentication, mode and permission before a F.R.I.D.A.Y. task uses an integration.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, capability, core]
---

# Capability and health check

Use before any adapter-backed operation or after a capability error. Do not assume that installed skill text implies a running service. Inputs: named capability, desired read/write permission, mode, trusted health response and current UTC time.

1. Query the adapter through its trusted interface, if configured. Inspect presence, status, authentication, read/write permission, rate limit and timestamp. A response older than five minutes is stale under `shared/policy.py`.
2. Enforce mode: `mock` only synthetic reads, `read_only` observations and drafts, `live` required for external writes. A degraded, offline, unauthenticated, rate-limited or unknown capability is unavailable.
3. Report an actionable alternative only if it is actually configured and fits the same risk boundary. Otherwise block the dependent operation and allow independent safe steps.

Output a normalized result with capability name, checked time, mode, permission and reason. Verify the record's origin and freshness. If no health endpoint exists, report `unknown`; do not turn a successful command-line import into proof of online authentication.
