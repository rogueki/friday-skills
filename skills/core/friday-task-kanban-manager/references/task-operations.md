# Task operations and evidence

Contract basis: [`docs/CONTROL_API_TASKS.md`](../../../../docs/CONTROL_API_TASKS.md), read from the pinned parent snapshot `d2432d6`. Recheck the live parent contract before integration. This file guides a skill; it does not grant access or implement a gateway.

| Operation | Required capability and proof | Allowed action |
|---|---|---|
| Plan locally | No task adapter; trusted request | Record acceptance criteria, board choice, owner/profile, dependency IDs and proposed fields. No server task ID. |
| Observe Hermes Kanban | Observer enabled in each relevant process | Read sanitized `kanban_task_claimed/completed/blocked` metadata from the local journal. This is incomplete observation and never a parent task update. |
| Read parent task | Valid viewer session and `task.read` | `GET /api/v1/tasks/{id}`. Check ID, version, freshness and response. |
| Create parent task | Valid operator session, CSRF, `task.write`, `live`, stable key | `POST /api/v1/tasks` with `Idempotency-Key` and only `title`, `description`, `priority`, `agentId`, `model`, `dueAt`, `labels`. Require a validated 201 snapshot. |
| Update parent task | Same write preconditions, current version | `PATCH /api/v1/tasks/{id}` with `If-Match: <positive task version>` and only `title`, `description`, `status`, `priority`, `agentId`, `dueAt`, `labels`. Require a validated 200 snapshot of the same ID. |
| Publish Dashboard event | No direct skill operation | The parent service owns `jarvis.task.*`; no WebSocket send from this skill. |

The checked API statuses are `triage`, `todo`, `ready`, `running`, `waiting`, `review`, `done`, `failed`, `cancelled`. Priority is `P0` through `P4`. `If-Match` is a version number, not a quoted ETag. The current client exposes create, update and get only; no list, pause, resume, retry or cancellation method. `cancelled` is a status value but this file does not imply a tested cancellation workflow. Board, assignee/profile, dependencies, acceptance criteria, progress comments and artifact links have no corresponding create/update field in the checked client. Keep them in the local task plan or use another verified contract when available; do not encode them as fabricated API fields.

## Transition procedure

1. Keep the trusted request ID and an operation key before dispatch. For CREATE, persist the exact key and payload fingerprint outside the short-lived client instance if durable retry behavior is required.
2. For UPDATE, GET the task, compare version and current status, decide the desired supported next state, then PATCH with that version. A 409 requires a fresh GET and a new decision; never overwrite a concurrent update blindly. The checked schema enumerates statuses but does not prove every transition is legal.
3. After the response, correlate task ID and version. Where completion or a consequential action matters, use a fresh read and underlying artifact/provider evidence. A 200 response alone proves an accepted task mutation, not the real work.
4. On timeout, transport failure, 5xx or malformed mutation response, record `unknown_outcome`. For an UPDATE, GET the known ID and compare intended fields and version. For a CREATE without returned ID, reconcile through a trusted server-side idempotency lookup if one exists; this client has none. Keep the same key and payload, and do not invent a new key or blindly resend. Escalate if no authoritative reconciliation path exists.

Classify each action with [`docs/CONTRACTS.md`](../../../../docs/CONTRACTS.md). A board-local write within authorized scope may be tier 1. An external notification remains tier 2; payments, contracts, credentials and similar high-risk actions remain tier 3. Task state must not be used to bypass those approvals.
