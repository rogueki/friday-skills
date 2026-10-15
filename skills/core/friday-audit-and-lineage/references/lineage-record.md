# Redacted lineage record

Keep these logical fields for each consequential step; an implementation may use a different validated schema. Do not claim this reference defines an installed parent audit endpoint.

| Field | Content |
|---|---|
| `request_ref` | Opaque trusted request ID and time; no raw sensitive prompt. |
| `route` | Selected skill, agent and model/reasoning level only when observed, with decision reason. |
| `source_refs` | Source ID, type, retrieval time, trust class and safe content digest; claims remain claims. |
| `operation_ref` | Stable operation ID, action, target, mode, risk tier, capability result, idempotency key reference. |
| `approval_ref` | Opaque approval ID, exact action fingerprint, target, tier, decision, expiry and immediate pre-dispatch check result. Never authentication material. |
| `effect` | Proposed, dispatched, unknown, acknowledged or verified; include timestamp and authoritative receipt ID. |
| `artifact_refs` | Output ID/digest, source IDs and transformation steps. |
| `gap` | Missing receipt, stale capability, contradictory source or unresolved mutation outcome with next reconciliation action. |

Use `shared/schemas/action.schema.json`, `approval.schema.json` and `result.schema.json` for local records. `actions_taken` contains observed actions only; a draft or approval request belongs to `actions_proposed` or `approvals_required`. A task mutation's 200/201 response and version may prove accepted task state, while underlying work still needs its own evidence. An external provider receipt must come from that provider, not from the local mock. The optional Hermes Kanban observer supplies only task ID/run ID/board/profile/event kind/timestamp; it does not prove the provider action or parent Dashboard activity. The checked parent activity/audit APIs are read-only, so no parent audit write is available here.

Before retaining or exporting, redact credentials, cookies, second factors, raw email/document contents, banking details and unnecessary person data. Preserve opaque IDs and non-secret hashes for correlation; a hash is not anonymization when the input is guessable. If an action is `unknown`, keep the original key/fingerprint and block dependent writes until authoritative reconciliation. Mark each evidence source `local`, `server` or `provider`; never promote a local narrative to a durable external receipt.
