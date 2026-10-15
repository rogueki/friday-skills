# Capability contract

A skill requests a capability; an authenticated adapter reports whether it exists **now**. Discovering a `SKILL.md` or seeing a tool name is not capability evidence. The local reference is `shared/schemas/capability.schema.json`; the optional gate is `shared.policy.capability_available`, which must be explicitly called by a trusted integration.

[`registry/skill_capabilities.json`](../registry/skill_capabilities.json) maps all 101 procedures to logical `required` read interfaces and `conditional` interfaces for optional branches or writes. [`registry/capabilities.yaml`](../registry/capabilities.yaml) is generated from this manifest and catalogs 63 IDs. All catalog entries currently say `live_available: false` and `mock_available: false`: synthetic policy/scenario fixtures exist, but no provider adapter is installed by this registry. A `required` read interface may be bypassed only when the procedure explicitly accepts supplied verified evidence. Every conditional live action needs a fresh capability check and its own policy gate.

The current record carries `name`, `mode`, `status`, `authenticated`, `rate_limited`, `permissions` and UTC `checked_at`. Optional `synthetic` identifies mock data; `authorized_workspace` marks a permitted local draft location. The Python helper accepts only `healthy`, authenticated, non-rate-limited records of the requested mode with the required permission, checked within five minutes. `mock` reads require `synthetic: true`; write permission is only available in `live`. An offline, stale, degraded or unknown record fails closed.

The public GeoSphere forecast is a narrow exception to credential-based authentication. A `weather.read` record from `geosphere-weather` may set `authenticated: false` and `public_read: true` only for a read-only HTTPS forecast response from the exact GeoSphere endpoint. The helper still checks mode, freshness, status and read permission; this exception never authorizes a write or any other capability. The weather plugin produces this record only after a successful adapter call. Public access is not a general bypass for other adapters.

The GMX and CalDAV adapters add explicit transport paths and synthetic fixtures. Their presence does not change the static registry flags: no authenticated provider session, trusted approval gateway or per-account capability reporter has been installed. The mail plugin can read one UID only after operator opt-in and credentials; the calendar plugin currently serves synthetic reads only. Neither plugin exposes a write tool.

The Loxone status plugin exposes only synthetic, read-only fixture data. Its `authenticated: false` marker is intentional; the plugin does not assert a current `loxone.read` capability. A separately authenticated Miniserver provider must satisfy the documented snapshot contract before the static availability flags change.

```json
{"name":"mail.read","mode":"mock","status":"healthy","authenticated":true,"rate_limited":false,"permissions":["read"],"checked_at":"2026-10-15T12:00:00Z","synthetic":true}
```

This is a **fixture example at its timestamp**, not a current or live mail capability. A real adapter must supply its own narrowly scoped record, declare the target/account outside logs, verify authentication and refresh on expiry or error. It must check actual adapter permissions, not grant them because a skill asks. Missing support yields `blocked` or a clearly labeled draft/mock result. Never silently substitute a different user's account, host or provider.

Service categories in the plan include mail, calendar, contacts, payment preparation/execution, Loxone read/write, weather, Office worker, voice, filesystem and dashboard Control API. Each requires separate implementation and proof. The current repository includes local policy/mock code, not a full set of connectors. See [configuration](CONFIGURATION.md) and [operations](OPERATIONS.md).
