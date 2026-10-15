# F.R.I.D.A.Y. Hermes Kanban Observer

Author: RogueKI. This optional standalone plugin targets Hermes Agent v0.20.5
and records a small local journal of Kanban task lifecycle events. It never
publishes events, edits tasks, calls the dashboard, or performs network actions.

## Hook contract

The plugin uses Hermes `ctx.register_hook(hook_name, callback)` with keyword
payloads and a `**kwargs` callback. It subscribes only to the three observer
hooks:

| Hook | Hermes payload additions intentionally discarded |
|---|---|
| `kanban_task_claimed` | `assignee` |
| `kanban_task_completed` | `assignee`, `summary` |
| `kanban_task_blocked` | `assignee`, `reason` |

The journal stores exactly `event_kind`, `task_id`, `run_id`, `board`,
`profile`, and UTC `timestamp`, plus an internal hash key for duplicate
suppression. Identifiers must match a short ASCII identifier allowlist;
invalid task IDs are dropped and invalid optional IDs are stored as null.
Prompt text, summaries, reasons, assignees, event payloads, secrets and raw
exception messages are never stored.

Hermes v0.20.5 source confirms these are observer-only hooks whose return
values are ignored. `kanban_task_claimed` fires in the dispatcher process;
completion normally fires in the worker process; blocked fires in the process
that caused the transition. Therefore this journal is cross-process local
storage, but it is not a guaranteed complete central event stream unless the
plugin is loaded in every relevant Hermes process/profile. The blocked
dependency-wait path can fire before its surrounding transaction exits. Hook
callbacks should remain quick; SQLite uses a five-second busy timeout.

## Opt-in installation

Copy `plugins/friday_kanban_observer/` into
`<HERMES_HOME>/plugins/friday-kanban-observer/`, then explicitly add
`friday-kanban-observer` under `plugins.enabled` in that Hermes profile's
`config.yaml`. For example:

```yaml
plugins:
  enabled:
    - friday-kanban-observer
```

The observer is not enabled by this repository and does not edit Hermes
configuration. The plugin is trusted local code; Hermes plugin enablement is
not a sandbox.

## Journal path

Set `FRIDAY_KANBAN_OBSERVER_DB` to an **absolute path outside this repository**
whose parent directory already exists, for example:

```powershell
$env:FRIDAY_KANBAN_OBSERVER_DB = Join-Path $env:LOCALAPPDATA 'hermes\state\friday-kanban-observer.sqlite3'
```

When that variable is absent, the plugin uses
`$HERMES_HOME/state/friday-kanban-observer.sqlite3`, provided `HERMES_HOME` is
absolute and the `state` directory already exists. The database is not opened
or created at import or registration time; it is created on the first valid
event. No missing directories are created. Relative paths, repository paths,
symlink/non-file targets, and invalid configuration fail closed. On POSIX the
database file is restricted to mode `0600`; Windows inherits the parent
directory ACL. Corrupt databases are left untouched and the event is dropped.
The hook callback catches journal errors so they cannot affect the task
transition.

## Verification and limits

Run the focused unit tests from the repository root:

```powershell
python -m unittest discover -s tests -p test_kanban_observer.py -v
```

These tests exercise a fake Hermes context, metadata allowlisting, discarded
content fields, duplicate suppression, unsafe/unconfigured paths and corrupt
database handling. They do not run a real Kanban worker, prove all process
topologies load the plugin, or guarantee delivery if SQLite is unavailable.

Hermes source references checked locally against the installed v0.20.5 source:
`hermes_cli/plugins.py` (`VALID_HOOKS`, `PluginContext.register_hook`, hook
callback invocation) and `website/docs/user-guide/features/hooks.md` (payload
and lifecycle timing table). This plugin is separate from
`plugins/friday_local` and has no dependency on its mock tools.
