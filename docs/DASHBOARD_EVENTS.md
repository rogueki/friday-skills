# Dashboard event integration

`shared/schemas/event.schema.json` defines **local** lifecycle records with types `friday.skill.started`, `.progress`, `.waiting_approval`, `.completed` and `.failed`. `shared/runtime.py` records mock examples and `dashboard_mapping` returns a `publishable: false` hint. Neither function sends a dashboard event.

The [checked rogue-friday AsyncAPI snapshot](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/asyncapi/jarvis-events.yaml) specifies `jarvis.task.created`, `.updated`, `.progress`, `.completed`, `.failed` and `jarvis.activity.appended`. It does **not** define `friday.skill.*` or `jarvis.skill.*` as publishable event names. Recheck the current companion contract before implementation; this repository remains read only with respect to it.

A future trusted adapter should:

1. Correlate a skill invocation with a real task ID if a task was created. For longer work, create/update a real Kanban task through an authenticated Control API operation, not by emitting fabricated WebSocket messages. The transport-injected [Task-Client](CONTROL_API_TASKS.md) covers the parent POST/PATCH/GET contract in mock tests only.
2. Translate verified task progress and completion to the exact current `jarvis.task.*` operation/payload. The checked parent API has no activity-append endpoint; standalone local skill records remain local. The optional [Hermes Kanban observer](KANBAN_OBSERVER.md) journals sanitized metadata locally, but does not publish it.
3. Keep `queued`, `working`, `waiting`, `waiting_approval`, `completed`, `partial`, `failed` and `blocked` as internal UI/task states only where the server schema permits them. Map unsupported states deliberately rather than inventing protocol values.
4. Verify server acknowledgement, delivery and correlation before recording `published`. Deduplicate retries with an event/operation key; preserve failure evidence when delivery is uncertain.
5. Mark completion only after the underlying outcome has verification evidence and no pending approval. A generated JSON file, mapped hint or local mock audit does not prove the dashboard displayed anything.

Do not include raw email, secret, bank or family content in event/activity text. The action/result schemas and [contracts](CONTRACTS.md) define the local fields. Event transport and dashboard icon/orb mapping need a real integration and end-to-end test.
