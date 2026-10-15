# Configuration

Put the source tree at `C:\Users\ByteNinja\Downloads\JARVIS_Installer\Skills`. For a Windows Hermes process, edit `%USERPROFILE%\.hermes\config.yaml`:

```yaml
skills:
  external_dirs:
    - 'C:\Users\ByteNinja\Downloads\JARVIS_Installer\Skills\skills'
  write_approval: true
  guard_agent_created: true
```

For Hermes inside WSL, use the actual Linux mount instead, often `/mnt/c/Users/ByteNinja/Downloads/JARVIS_Installer/Skills/skills`. Check the mount with `ls` first. Configure **one** reference to this physical directory; do not use both `create_dir` and `external_dirs` for the same copy. Preserve the rest of an existing Hermes config. [Installation](INSTALLATION.md) has verification steps. The exact config keys follow the [official Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills); confirm against the installed version.

`write_approval: true` gates agent-created or edited skill files through Hermes' skill management path. It is **not** an approval gate for mail, payments, files, APIs or dashboard writes. Those require the trusted adapter policy described in [approvals](APPROVALS.md).

Keep connector tokens in the adapter's environment or secret store, outside Git. Do not put credentials, personal profiles, account IDs or banking details in `SKILL.md`, config examples, fixtures or result/event payloads. The package has no universal `FRIDAY_LIVE=true` switch; each integration must report a fresh capability record. `mock`, `read_only` and `live` are operation modes, not global assurance labels.

To test discovery without changing the active profile, create a temporary `HERMES_HOME` containing only a `config.yaml` pointing to this checkout, run `hermes skills list`, then remove that temporary profile. This verifies parsing/discovery for that Hermes version, not adapter operation.
