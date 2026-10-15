# Meeting briefing E2E3: local mock

`run_scenario("meeting")` composes three bounded sources at the fixed 2026-10-15 12:00 UTC cutoff:

1. `caldav_calendar.list_events(mode="mock")` parses the synthetic multistatus/VEVENT, including UID, UTC interval and ETag.
2. `gmx_mail.read_message(mode="mock")` parses synthetic RFC822 headers and plain text. The parsed Message-ID must match the explicit meeting context, and the body must carry the exact calendar UID.
3. `meeting_briefing_mock.read_task_snapshot` validates a separate synthetic task snapshot, unique expected IDs, open status, freshness and each task's exact calendar UID.

The brief contains goal, participants, meeting time, question, open tasks, decisions needed, source IDs/freshness and missing optional context. The event's summary and mail/task text are data, never commands. `completed` needs all three source joins; missing/stale data returns `partial` or `blocked`. All local lifecycle mappings are `publishable=false`. There are no provider requests, Control API task reads, sends, event writes or external effects. Header equality does not authenticate the sender. Contacts, prior meetings and documents are reported as missing rather than inferred from the fixture.

Negative scenarios: absent/wrong-time event, missing/unrelated/stale/injection mail, absent/stale/duplicate/foreign tasks, each source offline, stale calendar capability, invalid window and timezone-free window. The older `timezone_conflict` case remains a separate UTC conflict test.

[GitHub Actions run 38770968528](https://github.com/rogueki/friday-skills/actions/runs/38770968528) passed the Windows and Ubuntu checks for this mock.
