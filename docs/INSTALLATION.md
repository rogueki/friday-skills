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

Run `hermes skills list` and compare the discovered `friday-*` names with the current `registry/skills.json` and [catalog](SKILL_CATALOG.md). On 2026-10-15, Hermes v0.20.5 discovered **all 101** as enabled through an isolated temporary profile with `external_dirs` pointing here. This does not configure or verify the user's active Hermes profile. `hermes skills audit` reported `No hub-installed skills to audit` for that external-directory profile; it did not audit these 101 skills. The local validator and unit tests require Python 3.10+ and no third-party packages.

The optional [native Hermes mock plugin](../plugins/CONTRACT.md) has a separate, explicit opt-in setup. An isolated Hermes v0.20.5 profile loaded its four local tools; the active profile was not changed. The plugin has no external write path and does not enforce approvals for unrelated Hermes tools.

The current package has no authenticated dashboard, mail, calendar, payment or memory adapter. Before live use, an integration must supply explicit capability records, mode, approval evidence, idempotency, durable audit/event delivery and a tested failure path. See [contracts](CONTRACTS.md). Never put tokens into a skill or this repository.

Hermes references: [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills).
