# Important mail E2E mock (§32 E2E1)

Run `python -c "from shared.scenarios import run_scenario; print(run_scenario('important_mail_e2e'))"` for the waiting-approval path. Use `variant='approved'` only to exercise a synthetic one-use grant and a separate local delivery simulation. The original `important_mail` scenario remains available with its existing output contract.

The new path reads pinned RFC822 bytes with the GMX mock reader, checks the expected From header, exact subject and body, UID, parsed Message-ID and parsed date, and classifies this one synthetic fixture as P1. It uses the parsed Message-ID as the thread ID and the checked body/date for the summary. The From comparison does **not** authenticate the sender. A synthetic `calendar.read` capability passes the shared policy check before the CalDAV mock fixture is queried in a 2026-10-15 11:45–12:45 UTC window. The flow prepares a local alert mapping and an exact recipient/subject/body draft. Without a synthetic grant it stops at `waiting_approval`. With one, a temporary `ApprovalLedger` consumes the bound grant and the flow records `delivered=false`, `transport=none` and `external_effects=0`. The GMX SMTP sender is never called.

Variants `injection` and `calendar_unavailable` block before a proposal; the latter fails the shared mock-capability check. `forged_approval`, `expired_approval`, `changed_recipient` and `changed_draft` block before mock delivery. Tests also prove a changed Message-ID or malformed date blocks the summary, grant replay is rejected and fixture names are allowlisted.

The local audit entries and `dashboard_mapping(publishable=False)` are previews only. This flow does not authenticate an operator, publish to the parent Dashboard, read a real GMX account, or send a message. The synthetic `approved` variant is a test input, not a real approval or live-mail capability.

[GitHub Actions run 38769561045](https://github.com/rogueki/friday-skills/actions/runs/38769561045) passed the Windows and Ubuntu test jobs for this mock.
