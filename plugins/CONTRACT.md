# F.R.I.D.A.Y. plugin boundary

Author: RogueKI. The optional `plugins/friday_local` directory is a native Hermes
v0.20.5 standalone plugin. Its four tools perform mock policy evaluation,
allowlisted synthetic fixture reads, in-memory proposals, and in-memory lifecycle
records. The repository does **not** install or enable it in an active Hermes
profile. No handler has a send, payment, booking, home control, file mutation,
network publishing, or Control API transport.

## Reproducible opt-in layout

The plugin imports the repository's `shared` Python package. Stage `shared/`
and `fixtures/` under a dedicated support directory; putting the entire repo
root on `PYTHONPATH` would also shadow Hermes's own `plugins` package. Set
`FRIDAY_SKILLS_ROOT` and the process `PYTHONPATH` to the support directory.
The plugin validates that `shared` resolves inside that directory; it never
changes `sys.path` itself. Copy `plugins/friday_local/` into
`<HERMES_HOME>/plugins/friday_local/`, then add `friday-local` to
`plugins.enabled` in that profile's `config.yaml`. Start Hermes outside the
repository checkout so Python does not import the checkout's `plugins` or
`shared` package through the current directory. Example for an **isolated**
PowerShell profile (replace the repository path):

```powershell
$repo = 'C:\Users\ByteNinja\Downloads\JARVIS_Installer\Skills'
$env:HERMES_HOME = Join-Path $env:TEMP ('friday-hermes-plugin-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force (Join-Path $env:HERMES_HOME 'plugins') | Out-Null
$support = Join-Path $env:HERMES_HOME 'friday_support'
New-Item -ItemType Directory -Force $support | Out-Null
Copy-Item -Recurse (Join-Path $repo 'shared') (Join-Path $support 'shared')
Copy-Item -Recurse (Join-Path $repo 'fixtures') (Join-Path $support 'fixtures')
Copy-Item -Recurse (Join-Path $repo 'plugins\friday_local') (Join-Path $env:HERMES_HOME 'plugins\friday_local')
$env:FRIDAY_SKILLS_ROOT = $support
$env:PYTHONPATH = "$support;$env:PYTHONPATH"
Set-Content -Path (Join-Path $env:HERMES_HOME 'config.yaml') -Value "plugins:`n  enabled:`n    - friday-local`n"
Set-Location $env:HERMES_HOME
hermes plugins list
```

Treat the plugin and local checkout as trusted code. Hermes discovers a user
plugin only after explicit enablement; no project plugin opt-in is used here.
`plugins.enabled` is not a security sandbox. A future external action must be
guarded synchronously **inside its own handler** and fail closed on policy or
approval errors. Hermes `pre_tool_call` hooks may fail open on exception or
timeout and are not an enforcement boundary.

`shared/input_trust.py` is a host-only mock-proposal helper. The four
model-invokable `friday_local` tools do not accept its `HostRequest` or
`SourceEnvelope` objects and do not claim authenticated provenance. The
`friday_mock_propose` tool remains an in-memory advisory proposal, not an
authorization decision. A future trusted F.R.I.D.A.Y. handler must call the
binding helper with host-owned objects and separately apply capability,
approval and idempotency checks before any real effect. Other Hermes tools and
plugins are outside this boundary.

The local lifecycle type is defined by `shared/schemas/event.schema.json` and
is not a `rogue-friday` AsyncAPI event. `dashboard_mapping` returns an intended
task/activity operation with `publishable: false`; no network publishing occurs.
The synthetic fixture allowlist is fixed in `friday_local/__init__.py`; the
underlying package may contain additional fixtures that these tools cannot read.

Official Hermes plugin reference: <https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/plugins.md>.
