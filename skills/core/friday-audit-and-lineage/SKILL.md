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

Use when an outcome needs a reproducible decision and action trail. Inputs: operator request ID, route, skill/agent/model when known, source IDs and retrieval times, tool calls, proposed actions, approvals, artifacts, timestamps and authoritative receipts. Do not infer unknown model or reasoning details.

1. Begin a [lineage chain](references/lineage-record.md) at the trusted request. Record each material decision and tool call with actor, time, mode, target, intent, source references and evidence ID. Distinguish planned, dispatched, acknowledged and verified states; do not place proposals in `actions_taken`.
2. For every external write, link the exact action fingerprint, target, risk tier, approval decision/expiry, capability and idempotency key. Recheck approval immediately before dispatch. Record an opaque approval ID; never store a token, cookie, second factor or full sensitive payload.
3. Link derived artifacts to source IDs and transformations, with a content digest when safe. A source claim is not an observed outcome. Redact sensitive data before any local record, event or export while preserving enough IDs to reconcile.
4. Obtain a receipt from the system that owns the action. For a parent task mutation, keep task ID/version and response or fresh GET evidence; for an external provider, keep its provider receipt. The local Hermes Kanban journal and mock delivery records are only local observations. The checked parent audit/activity APIs are read-only: do not claim durable parent audit persistence.
5. On timeout or ambiguous response, mark outcome `unknown`, freeze dependent writes and reconcile with the authoritative system. Missing or contradictory receipts are gaps, never success. Full completion of a high-risk action requires verified effect and its required audit evidence.

Output the normalized result with redacted lineage references, verified effects, pending approvals and explicit gaps. If no durable audit adapter exists, label the artifact local and unpersisted; a well-formed JSON file is not an external audit receipt.
