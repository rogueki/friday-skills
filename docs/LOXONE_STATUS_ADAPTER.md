# Loxone Status Adapter

Author: RogueKI. This is a bounded, read-only adapter contract for plan §17.1
(`jarvis-loxone-status`). It has **no Loxone wire client**. `mock` reads the
labelled synthetic fixture; `read_only`/`live` require an explicitly injected
authenticated provider callback and cannot silently open a socket or obtain
credentials. There is no write or command API.

## Snapshot contract

The injected provider object must set `authenticated = True` only after a
successful authenticated read session. Its `read_snapshot(allowlisted_control_ids,
timeout_seconds)` method returns exactly:

```json
{"version":1,"observed_at":"2026-10-15T12:00:00Z","controls":[
  {"id":"ctrl-room-temp","room_id":"room-living","kind":"temperature","value":21.4,"unit":"°C","updated_at":"2026-10-15T12:00:00Z"}
]}
```

IDs must match `[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}`. Callers must provide an
explicit list of 1–100 unique control IDs. Provider output outside that list is
rejected. Each returned control must have a timezone-aware timestamp no more
than five minutes old or 60 seconds in the future. Timestamps, units and ranges
are validated; output is sorted and contains only IDs, normalized kinds, values,
units and timestamps. Room names, labels, raw provider records, credentials,
access state and alarm descriptions are not accepted. Door/window/alarm values
are boolean only; alarm details cannot be represented. Numeric ranges are
constrained by kind. This is a data minimization boundary, not an authorization
implementation: the injected provider must enforce the user's Loxone ACL too.

Supported kinds/units: temperature °C, humidity %, light %, shading %, heating
°C, PV W, battery %, consumption W; door/window/alarm use unit `boolean`.

## Loxone interoperability

Official Loxone API documentation describes a changing Miniserver API and points
developers to `Communicating with the Miniserver`. Its current revision 16.0
documents authenticated RFC6455 WebSocket setup, encrypted token exchange, and
the LoxAPP3 structure file. It does not establish a stable provider-neutral
read payload for the exact set of §17.1 room/temperature/window/energy/alarm
fields used here. Therefore this repository does not claim that a live Miniserver
is currently interoperable with this adapter. A separately reviewed provider
must translate Loxone structures/events into the snapshot contract, preserve TLS
certificate verification and Miniserver ACLs, and be tested against a versioned
Miniserver before `live_available` can be asserted.

Primary sources (checked 2026-10-15):

- [Loxone API overview](https://www.loxone.com/enen/kb/api/) — notes that the
  interface can change when Config/Miniserver is updated.
- [Communicating with the Miniserver, revision 16.0](https://www.loxone.com/wp-content/uploads/datasheets/CommunicatingWithMiniserver.pdf)
  — WebSocket RFC6455, credentials and encrypted/token-based connection steps;
  HTTPS/WSS and certificate verification requirements.
- [Loxone Miniserver](https://www.loxone.com/enus/kb/miniserver/) — identifies
  the LoxAPP3 structure file used by the user interface.

## Hermes plugin

`plugins/friday_loxone_status` exposes one read tool. Default `register(ctx)`
uses the synthetic fixture (`synthetic: true`, `authenticated: false`). A trusted
host can call `register(ctx, transport=provider, allowed_control_ids=[...])`.
Both arguments are required together; the host must supply a fixed list of
1–100 unique control IDs and an already authenticated provider implementing the
snapshot contract above. The tool accepts only `control_ids`, checks that every
requested ID belongs to the host list before calling the provider, and sends
only the requested subset to `read_status(..., mode="read_only")`. The model
cannot choose mode, host, credentials or additional control IDs. Only a fresh,
valid provider snapshot is returned as `loxone.read` with `authenticated: true`,
`synthetic: false`, `checked_at` and a provider-neutral `source`. Errors expose
only stable codes; provider details are never forwarded. No write tool exists.

This host injection and fake-transport test coverage do not establish live
Miniserver interoperability. A reviewed and authenticated Loxone transport and
versioned hardware validation are still required. Registration alone does not
make the live Loxone capability available.

Tests use only the local fixture and injected Python callbacks. They perform no
network requests and never access an active Hermes profile.
