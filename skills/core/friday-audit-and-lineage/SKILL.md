---
name: friday-audit-and-lineage
description: Assemble redacted action, source, approval and artifact lineage for F.R.I.D.A.Y. tasks when an audit trail is required.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, audit, core]
---

# Audit and lineage

Use for a task requiring a reproducible action trail. Do not equate a local narrative with a durable audit log. Inputs: request ID, route, skill/tool calls, source IDs, timestamps, approvals, artifacts and adapter acknowledgement.

1. Record each decision as time, actor/component, mode, intended action, observed outcome and evidence ID. Link derived artifacts to source IDs and transformations; separate proposed from executed steps.
2. Record approval fingerprint/decision/expiry without secrets or authentication factors. Redact tokens, credentials and personal data before storage. Reference sensitive records by opaque ID only.
3. Check gaps: a write needs capability, approval where required, idempotency key and authoritative response. Mark missing evidence explicitly.
4. If a durable audit adapter exists, submit through it and verify its receipt. Otherwise output a local, unpersisted audit artifact and state that persistence is unavailable.
5. E2E1 records a local decision trail and a local mock-delivery record. Mark the latter `delivered=false`, `transport=none` and `external_effects=0`; local dashboard mappings have `publishable=false`. Neither is a parent Dashboard or provider receipt.

Return normalized result with lineage references and gaps. A missing audit trail for a high-risk action blocks the claim of full completion; reconcile from the authoritative system before retrying.
