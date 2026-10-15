# Installation and configuration

Use the **same filesystem's path** to this repository's `skills` directory. On Windows, set an absolute Windows path in `%USERPROFILE%\.hermes\config.yaml`. On WSL, translate the drive path to `/mnt/c/...` or copy the repository into WSL; a Windows path is not a Linux path. The exact mount can differ by WSL configuration.

```yaml
skills:
  external_dirs:
    - /mnt/c/Users/<user>/Downloads/JARVIS_Installer/Skills/skills
  write_approval: true
  guard_agent_created: true
```

Replace `<user>` with the local account name. The example is for Hermes running **inside WSL**. For a Windows Hermes process, use a quoted Windows path such as `C:\Users\<user>\Downloads\JARVIS_Installer\Skills\skills` instead. Configure this directory once; do not also set `create_dir` to the same physical path. Hermes can modify writable external skills through skill management, so use filesystem permissions if the source must stay read only. `write_approval: true` gates agent skill writes, not every external side effect.

Run `hermes skills list` and compare the discovered `friday-*` names with the current `registry/skills.json` and [catalog](SKILL_CATALOG.md). On 2026-10-15, Hermes v0.20.5 discovered **all 101** as enabled through an isolated temporary profile and then through the operator's active Windows profile. The latter has `skills.external_dirs` pointed at this checkout, `skills.write_approval=true` and `skills.guard_agent_created=true`. The existing config was backed up locally before the change; all other parsed config values matched the backup afterward. This does not enable plugins or verify model routing. `hermes skills audit` reported `No hub-installed skills to audit` for the external-directory profile; it did not audit these 101 skills. The local validator and unit tests require Python 3.11+ and no third-party packages.

The optional [native Hermes mock plugin](../plugins/CONTRACT.md) has a separate, explicit opt-in setup. An isolated Hermes v0.20.5 profile loaded its four local tools; plugin settings in the active profile were not changed. The plugin has no external write path and does not enforce approvals for unrelated Hermes tools.

The package has optional GMX and CalDAV adapter code, but no configured account or trusted write gateway. The dashboard, payment and memory integrations likewise remain unconnected. Before live use, an integration must supply explicit capability records, mode, trusted approval evidence, idempotency, durable audit/event delivery and a tested failure path. See [contracts](CONTRACTS.md), [GMX mail](GMX_MAIL_ADAPTER.md) and [CalDAV](CALDAV_ADAPTER.md). Never put tokens into a skill or this repository.

Hermes references: [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills).
