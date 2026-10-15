# Test report — 2026-10-15

Repository: `friday-skills` at the 0.2.0 procedure-suite stage. Environment: Windows PowerShell, Python 3.11.0, Hermes Agent v0.20.5 (2026.8.19; upstream `2d4de4e7`, local `68518c1f`). All fixture and scenario tests used synthetic data. No live adapter was exercised.

| Check | Result | Evidence |
|---|---|---|
| `python scripts/validate.py` | PASS | 101 skills; registry, 100-item roadmap, schemas and ignored local files valid. |
| `python scripts/build_registry.py` | PASS | Generated routing/capability/automation/dashboard registries current. |
| `python scripts/run_skill_cases.py` | PASS shared contract | 101 case files; 909 repeated shared policy/result checks passed, 404 manual routing expectations declared, 1616 skill-runtime cases not run. |
| `python -m unittest discover -s tests -q` | PASS | 45 tests, including policy, negative mock scenarios, grants fixture, capability registry, packaging and optional plugin contract. |
| `ruff check scripts shared plugins tools tests` | PASS | Python lint passed locally. |
| `python -m compileall -q scripts shared plugins tools tests` | PASS | Python files compiled locally. |
| `python scripts/smoke_test.py` | PASS | 101 registered `SKILL.md` files exist. |
| Isolated `HERMES_HOME` + `hermes skills list` | PASS | 101 `friday-*` rows reported `enabled`. The temporary profile only referenced this checkout via `skills.external_dirs`. |
| Isolated Hermes v0.20.5 plugin discovery | PASS | Optional `friday-local` loaded with four tools and no load error in a separate test profile; active profile untouched. |
| 101 per-skill `tests/cases.json` | PASS structural | Every skill has positive, negative, ambiguity and collision examples plus three §31 shared contracts. Routing outcomes are authored expectations, not executed model decisions. |
| `pyproject.toml` and GitHub Actions | PASS remote | Python 3.11 project metadata and [CI run 38747133211](https://github.com/rogueki/friday-skills/actions/runs/38747133211) on commit `6110222`: Windows and Ubuntu jobs both passed. |
| PowerShell and Bash install / repeat install | PASS local | Worker ran dry run, first copy and second copy into temporary targets; 203 files copied first, 0 changed on repeat. No active Hermes profile was modified. |
| ZIP export / CRC | PASS local | The 0.2.0 testkit ZIP has 286 entries and passed CRC verification; local `MEMORY.md`, `SCOPE.md`, ignored plan and secrets are excluded. The final artifact hash is recorded in local `MEMORY.md`. |
| `hermes skills audit` | NOT APPLICABLE | Local Hermes command reported `No hub-installed skills to audit`; it did not audit these `external_dirs` skills. |
| Real GMX/CalDAV/Loxone/banking/Office/Control API actions | NOT RUN | No live adapters or credentials are shipped or invoked. |

The ten plan workflows are **synthetic local scenarios**, with fixture-dependent negative variants for injection mail, suspicious invoice, timezone conflict, stale weather and travel, archive hash mismatch, Loxone readback failure, unknown tax rule and offline adapter. They are not end-to-end tests of the separate `rogue-friday` application. Policy helpers and hooks are callable local contracts; the optional plugin does not create a Hermes-wide enforcement gate merely because it is installed.

The isolated discovery profile remained in the Windows temporary directory after its cleanup command was rejected by automatic approval review: `C:\Users\BYTENI~1\AppData\Local\Temp\friday-skills-hermes-b100b0188edc4981aada7525bac2ee07`. We supplied only `config.yaml` with `skills.external_dirs`; Hermes generated additional profile directories and `SOUL.md` during the command. We did not supply credentials, but did not audit every generated artifact.
