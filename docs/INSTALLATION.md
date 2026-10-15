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

Run `hermes skills list` and verify all 11 `friday-*` names. Run `hermes skills audit` and `hermes doctor` if available in the installed version. On 2026-10-15, Hermes v0.20.5 discovered all 11 as enabled through an isolated temporary profile with `external_dirs` pointing here. This does not configure or verify the user's active Hermes profile. The local validator and unit tests require Python 3.10+ and no third-party packages.

The current package has no authenticated dashboard, mail, calendar, payment or memory adapter. Before live use, an integration must supply explicit capability records, mode, approval evidence, idempotency, durable audit/event delivery and a tested failure path. See [contracts](CONTRACTS.md). Never put tokens into a skill or this repository.

Hermes references: [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills).
