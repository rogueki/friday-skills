# Skill catalog

The source of truth for installed skills is `registry/skills.json`. All entries listed there are `implemented_procedure`, locally testable and installable as Hermes skill text. None has a live dashboard or external adapter. The original plan's `jarvis-*` names are mapped in the registry. The [machine-readable roadmap](../registry/roadmap.json) lists **all 100 plan skills** by original section and name: ten core entries implemented, 90 planned. `friday-web-research` is one extra implemented skill outside the plan's 100; it does not imply that the planned research suite is complete. No placeholder `SKILL.md` files are published for planned entries.

| Category | Implemented skill | Function | Runtime integration |
|---|---|---|---|
| core | friday-executive-orchestrator | Decompose and coordinate tasks | None |
| core | friday-intent-and-skill-router | Route by intent, risk, capability | None |
| core | friday-task-kanban-manager | Plan and verify task lifecycle | None |
| core | friday-approval-policy | Structure and recheck approvals | None |
| core | friday-input-trust-and-injection-defense | Separate untrusted content | None |
| core | friday-dashboard-activity-publisher | Define truthful event publication | None |
| core | friday-audit-and-lineage | Build redacted lineage | None |
| core | friday-memory-governance | Review durable memory candidates | None |
| core | friday-capability-and-health-check | Diagnose available capabilities | None |
| core | friday-error-recovery | Classify and recover bounded failures | None |
| research | friday-web-research | Source-grounded public web research | Optional local tools only |

Roadmap by plan section:

| Section | Domain | Implemented | Planned |
|---|---|---:|---:|
| 9 | Core safety and orchestration | 10 | 0 |
| 10 | Executive assistant | 0 | 6 |
| 11 | Communication | 0 | 7 |
| 12 | Calendar and meetings | 0 | 5 |
| 13 | Weather | 0 | 3 |
| 14 | Finance | 0 | 6 |
| 15 | Austria tax | 0 | 6 |
| 16 | Funding and tariffs | 0 | 4 |
| 17 | Home and energy | 0 | 5 |
| 18 | Media | 0 | 7 |
| 19 | Archive | 0 | 6 |
| 20 | Travel | 0 | 7 |
| 21 | Office and documents | 0 | 9 |
| 22 | Research and business | 0 | 6 |
| 23 | Files and knowledge | 0 | 4 |
| 24 | Voice and identity | 0 | 3 |
| 25 | System operations | 0 | 6 |

Next milestones: trusted Hermes hook/policy enforcement; dashboard Control API adapter with delivery acknowledgments and actual task/activity event mapping; mock Kanban and approval lifecycle; domain skills only when their data sources and adapters are ready. These milestones are unimplemented.
