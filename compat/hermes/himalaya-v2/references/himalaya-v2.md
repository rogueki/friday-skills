# Himalaya 2.2.1 reference for Friday

The Friday dashboard manages a single account `friday` through the companion
framework. Its generated v2 file is `~/.config/himalaya/config.toml`. Keep
passwords in the framework's separate mode-0600 files. Do not copy example
passwords into a skill, chat, command line or repository.

The v2 shape uses `[accounts.friday]`, `imap.server = "imaps://host:993"`,
`smtp.server = "smtp://host:587"` with `smtp.starttls = true` or
`smtp.server = "smtps://host:465"`, and `imap.sasl.plain.*` /
`smtp.sasl.plain.*`. Mailbox aliases use `mailbox.alias.sent`, etc. The older
`backend.type`, `message.send.backend.type` and `folder.aliases.*` keys do not
describe the Friday v2 profile. Use the dashboard rather than hand-editing a
managed profile.

The interactive v2 wizard is `himalaya configure`. The v2 CLI commands are:

| Goal | v2 command |
| --- | --- |
| Accounts | `himalaya account list --json` |
| Mailboxes | `himalaya --account friday mailbox list --json` |
| Inbox | `himalaya --account friday envelope list --mailbox INBOX --json` |
| Search | `himalaya --account friday envelope search --mailbox INBOX from sender@example.com --json` |
| Read | `himalaya --account friday message read --mailbox INBOX ID` |
| Draft RFC 5322 | `himalaya --account friday message compose --to recipient@example.com --subject Subject --body Text` |
| Send reviewed RFC 5322 | `himalaya --account friday message send --no-save /absolute/path/message.eml` |

`message send` is an external effect. A timeout, process crash or nonzero exit
does not prove no delivery. Keep an unknown outcome and investigate before
another attempt. `--no-save` avoids a separate Sent-copy operation but may
leave no server-side Sent record; provider behavior varies. No automatic
retry or test email is part of setup.

IMAP/SMTP password authentication works only where the provider permits it.
Some providers require app passwords or OAuth; this managed password form
does not grant OAuth. Verify the provider's current requirements before
claiming a mailbox is ready.
