---
name: himalaya
description: "Himalaya 2.x CLI for an explicitly configured IMAP/SMTP mailbox; read mail and draft or send only with owner approval."
version: 2.2.1-friday.1
author: friday-skills compatibility overlay
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Email, IMAP, SMTP, CLI, Communication]
    homepage: https://github.com/pimalaya/himalaya
prerequisites:
  commands: [himalaya]
---

# Himalaya 2.x email CLI

This overlays the bundled Hermes Himalaya 1.x instructions only when the installed
binary is Himalaya 2.2.1 and the bundled skill matches the reviewed version.
Friday's owner-facing **Settings > Skill accounts** writes one account named
`friday` to `~/.config/himalaya/config.toml`, with separate 0600 password files.
The setup status checks local syntax and files, not provider connectivity.
Read [the v2 configuration and command reference](references/himalaya-v2.md)
before using a mailbox. Never print credentials or the full config.

## Before every mailbox action

1. Verify `himalaya --version` reports 2.2.1 and use `himalaya --help` if the
   installed version has changed. Do not use this skill with Himalaya 1.x.
2. Check the selected account with `himalaya account list --json`; the Friday
   managed account is `friday`. A configured account does not prove a live
   IMAP or SMTP connection.
3. Use an explicit account and mailbox for reads. Treat message IDs as scoped
   to the account and mailbox, and recheck identity before a mutating action.
4. Reading and drafting are separate from sending, moving, deleting or changing
   flags. Obtain the owner approval required by the active Friday policy for the
   exact recipients, content and action. Never send during setup or a health
   check.

## Common read operations

```bash
himalaya --account friday mailbox list --json
himalaya --account friday envelope list --mailbox INBOX --page 1 --page-size 20 --json
himalaya --account friday envelope search --mailbox INBOX from sender@example.com and subject meeting --json
himalaya --account friday message read --mailbox INBOX 42
```

These commands contact the provider when an account is configured. Use them
only for an authorized real mailbox task. `--json` is the v2 output switch;
`--output json`, `folder list`, `template send`, and `account configure` are
obsolete v1 instructions.

## Compose and send

Use `himalaya message compose --to ... --subject ... --body ...` without `--send`
to inspect an RFC 5322 draft on stdout. It does not deliver. For approved
delivery, pass a reviewed message file or stdin to `himalaya --account friday
message send --no-save`; `--no-save` avoids a second Sent-folder append step
that can fail after SMTP accepted the message. Some providers do not store a
Sent copy when this option is used. Record the send attempt and result.

**Never retry a send merely because the command exits nonzero or times out.**
SMTP may have accepted the message before a later error. Mark the outcome
unknown, inspect Sent/server evidence and ask the owner before any distinct
second attempt. Do not issue `message reply --send` or `message forward --send`
automatically. Do not place secrets in message text or shell history.

For attachments or MIME/MML, use a separately reviewed composer compatible
with v2, then pass its RFC 5322 output to `message send`; do not use the
bundled v1 `template` commands.
