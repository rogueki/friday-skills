# Local records and Dashboard delivery

Contract basis: [`docs/DASHBOARD_EVENTS.md`](../../../../docs/DASHBOARD_EVENTS.md), [`docs/CONTRACTS.md`](../../../../docs/CONTRACTS.md) and the parent AsyncAPI pinned at `d2432d6`. Recheck the current parent before any live adapter. `shared/schemas/event.schema.json` is a local record schema, not the parent event envelope.

| Source state | Local record | Parent operation in checked contract | Delivery claim |
|---|---|---|---|
| Skill starts/progresses | `friday.skill.started` / `.progress` | With a real task, authenticated POST/PATCH may update supported task fields; the parent emits its task event. | Only after a validated response; UI visibility still unverified. |
| Approval pending | `friday.skill.waiting_approval` | A parent task may be set to supported `waiting` if the current task contract and business state allow it. | Local waiting record is not an approval-system receipt. |
| Skill completes | `friday.skill.completed` | A real task may move to `review` or `done` through PATCH after outcome evidence. | Require task ID, fresh version and underlying completion proof. |
| Skill fails | `friday.skill.failed` | A real task may move to `failed` if appropriate. | Do not convert a recoverable or unknown outcome into final failure without evidence. |
| No real task / stand-alone activity | Local record only | The checked parent exposes `jarvis.activity.appended` as an event but no activity append REST endpoint. | `not_delivered`; do not fabricate an event. |
| Hermes Kanban hook | Local sanitized SQLite journal only | No automatic parent task correlation or delivery. | `observed_local`, never `published`. |

The parent task status set is `triage`, `todo`, `ready`, `running`, `waiting`, `review`, `done`, `failed`, `cancelled`. Local result/status terms such as `partial`, `blocked` and `waiting_approval` are not automatically parent status values. Choose a supported parent status deliberately and retain the richer local state. Likewise, the plan's `skill.*`, `agent.*`, `tool.*`, `notification.*` and orb states are design targets, not existing parent endpoint names. Do not write them directly to `/api/v1/events` or a WebSocket.

## Delivery evidence

Store a redacted local event ID and operation fingerprint before dispatch. `mock` records and read-only previews remain `not_delivered`. For a parent mutation, require the trusted adapter's validated 200/201 response with task ID and version, then read back if the result needs durable confirmation. Mark the transport state `accepted` only for that evidence; mark Dashboard rendering `observed` only after an actual UI/read-side check tied to the same task. On timeout, 5xx or malformed response mark `unknown`; on a definitive rejection mark `failed`. Reconcile unknown outcomes with a GET and the same operation key before retrying. Never count the local event, mapping hint, observer journal or generated JSON as a delivery acknowledgement.
