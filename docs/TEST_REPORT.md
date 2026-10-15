# Test report — 2026-10-15

Repository: `friday-skills` at the 0.2.0 procedure-suite stage. Environment: Windows PowerShell, Python 3.11.0, Hermes Agent v0.20.5 (2026.8.19; upstream `2d4de4e7`, local `68518c1f`). All fixture and scenario tests used synthetic data. No live adapter was exercised.

| Check | Result | Evidence |
|---|---|---|
| `python scripts/validate.py` | PASS | 101 skills; registry, 100-item roadmap, schemas and ignored local files valid. |
| `python scripts/build_registry.py` | PASS | Generated routing/capability/automation/dashboard registries current. |
| `python -m unittest discover -s tests -q` | PASS | 24 tests, including policy, mock scenarios, routing, fixtures and packaging. |
| `python scripts/smoke_test.py` | PASS | 101 registered `SKILL.md` files exist. |
| Isolated `HERMES_HOME` + `hermes skills list` | PASS | 101 `friday-*` rows reported `enabled`. The temporary profile only referenced this checkout via `skills.external_dirs`. |
| 101 per-skill `tests/cases.json` | PASS structural | Every skill has positive, negative and collision examples. These are authored review cases, not executed model routing results. |
| PowerShell and Bash install / repeat install | PASS local | Worker ran dry run, first copy and second copy into temporary targets; 203 files copied first, 0 changed on repeat. No active Hermes profile was modified. |
| ZIP export / CRC | PASS local | Deterministic ZIP verified, with local `MEMORY.md`, `SCOPE.md`, ignored plan and secrets excluded. |
| `hermes skills audit` | NOT APPLICABLE | Local Hermes command reported `No hub-installed skills to audit`; it did not audit these `external_dirs` skills. |
| Real GMX/CalDAV/Loxone/banking/Office/Control API actions | NOT RUN | No live adapters or credentials are shipped or invoked. |

The ten plan workflows are **synthetic local scenario traces**, with assertions for key mock outcomes and forbidden external effects. They are not end-to-end tests of the separate `rogue-friday` application. Policy helpers and hooks are callable local contracts; Hermes does not register them as a live plugin merely because the repository is installed.

The isolated discovery profile remained in the Windows temporary directory after its cleanup command was rejected by automatic approval review. It contains a `config.yaml` referencing this checkout and no credentials: `C:\Users\BYTENI~1\AppData\Local\Temp\friday-skills-hermes-b100b0188edc4981aada7525bac2ee07`.
