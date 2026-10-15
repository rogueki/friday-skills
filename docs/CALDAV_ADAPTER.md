# CalDAV calendar adapter

This optional adapter belongs to the separate RogueKI F.R.I.D.A.Y. skill package. It has not been connected to `rogueki/rogue-friday` or a real calendar account.

## Scope

- `adapters/caldav_calendar.py` implements a bounded `calendar-query` `REPORT` for one explicitly named HTTPS calendar collection and account. It requests `DAV:getetag` and `CALDAV:calendar-data`, a VEVENT time range of at most 31 days, and accepts at most 100 calendar objects and 1 MB of response data.
- `mock` reads a labelled synthetic fixture. `read_only` and `live` reads require an explicitly injected authenticated transport. There is no default network transport and no credential lookup.
- One simple VEVENT per calendar object is supported. UTC timestamps, all-day `VALUE=DATE`, and TZID values backed by the host's IANA timezone database can be parsed. Floating/ambiguous/nonexistent local times, recurrence, weak ETags, unsafe XML and objects outside the requested window fail closed. Windows hosts need an IANA timezone source such as Python's `tzdata` package for non-UTC TZIDs.
- The optional Hermes `friday-caldav` plugin registers **one read tool**. Its default is `mock`. Its external modes currently return `transport_required`; an operator must wire a trusted authenticated transport and assess account permissions before enabling real reads. It registers no write tool.

## Write boundary

The adapter has `write_event` for a caller with a trusted approval gateway. It accepts only `live` create/update. The caller must supply an authenticated transport, a fresh `calendar.write` capability, a host-owned `ApprovalLedger` and one-use grant ID bound to the target, calendar bytes and idempotency key, plus a durable absolute SQLite operation journal path. The old `approval` mapping is no longer accepted. Grant consumption is atomic and occurs before the operation journal reservation and request. Create uses a deterministic `.ics` resource URL plus `If-None-Match: *`; update requires a strong ETag and sends `If-Match`. A pending/uncertain key is never sent again automatically, even after process restart. Reconcile against the server before a new mutation. The operation journal stores the fingerprint and minimal receipt, no calendar contents or credentials. See [approval boundary](APPROVAL_LEDGER.md).

The local ledgers do not prove the caller's identity or the approval's provenance. A production gateway must own those checks, its own audit trail, transport authentication, redirect blocking and per-account permissions. The injected transport must reject redirects and enforce the exact allowlisted HTTPS origin. No real calendar operation was performed in this package's tests.

## Status and verification

`python -m unittest discover -s tests -p 'test_caldav_adapter.py' -v` exercises read parsing, time windows, conflicts, approval failures, ETags and replay behavior without network. `python -m unittest discover -s tests -p 'test_hermes_caldav_plugin.py' -v` checks the opt-in read tool. A provider-specific integration and write gateway remain open work before live use.

Standards: [RFC 4791 CalDAV calendar-query and calendar-data](https://www.rfc-editor.org/rfc/rfc4791.html), [RFC 5545 iCalendar VEVENT/time rules](https://www.rfc-editor.org/rfc/rfc5545.html), [RFC 7232 conditional requests and entity tags](https://www.rfc-editor.org/rfc/rfc7232.html).
