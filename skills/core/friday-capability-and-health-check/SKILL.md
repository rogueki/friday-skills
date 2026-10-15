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

1. Resolve the named capability to a configured adapter and trusted health endpoint. Record adapter ID, source, check time, current mode, status, authentication, rate-limit state and explicit `read`/`write` permissions. An installed `SKILL.md`, registry row, import or old successful call proves none of these.
2. Apply `capability_available` from `shared/policy.py` to the requested permission and exact mode. A check older than five minutes or dated in the future fails. `mock` reads require a synthetic fixture; `read_only` allows observation and local drafts; external writes need `live` plus a separate approval gate. Degraded, offline, unauthenticated, rate-limited, unknown or insufficient-permission records fail closed. Public GeoSphere weather reads are the narrow documented authentication exception.
3. Return a decision for the requested operation, not a global claim that the service is healthy. If a trusted health endpoint is absent, use `unknown` and block the dependent operation. Offer an alternative only after separately checking its current source, mode, permission and risk boundary; preserve whether the result is synthetic or observed.

Output a normalized result with capability name, adapter/source, checked time, mode, requested permission, availability decision and reason. Verify the response origin and timestamp before using it; recheck immediately before a write. An earlier read probe is not write permission. A local `friday.skill.*` record is not a delivered Dashboard health notice.
