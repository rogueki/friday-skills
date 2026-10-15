# F.R.I.D.A.Y. Skills

**RogueKI** maintains this independent Hermes Agent skill suite for [rogueki/rogue-friday](https://github.com/rogueki/rogue-friday). F.R.I.D.A.Y. is the successor assistant in this project's own story: a coordinating core calls focused specialists for executive work, communication, finance, home, family, media, research and operations. This project is not affiliated with Marvel.

The [roadmap](registry/roadmap.json) names **100 skills from the implementation plan**. `friday-web-research` and four Content Studio procedures extend that plan. The current [registry/skills.json](registry/skills.json) lists 105 packaged procedures, cross-checked against `skills/**/SKILL.md`; [the catalog](docs/SKILL_CATALOG.md) explains categories, triggers and readiness. A procedure marked installable or mock-ready does not imply a live connector.

## What this repository provides

- Hermes `SKILL.md` decision procedures, examples and local tests.
- Local schemas and Python policy/mock helpers that an integration must **explicitly call**. Installing skills alone does not enforce approvals, prevent tool calls or emit dashboard events.
- An optional [native Hermes plugin](plugins/CONTRACT.md) with four local mock tools. It was loaded in an isolated test profile and is not enabled in the active profile. Its policy tool returns a decision but cannot enforce other Hermes tools or perform external actions.
- An optional [GeoSphere weather tool](docs/WEATHER_PLUGIN.md) backed by a bounded public read adapter, and a separate [Kanban observer](docs/KANBAN_OBSERVER.md). All three plugins passed isolated Hermes v0.20.5 registration checks; none is enabled in the active profile.
- A [Control API task client](docs/CONTROL_API_TASKS.md) with injected transport and mock tests. The companion `rogue-friday` repository stays read only; this package does not ship its dashboard or credentials.
- Optional [GMX mail](docs/GMX_MAIL_ADAPTER.md) and [CalDAV calendar](docs/CALDAV_ADAPTER.md) adapters with bounded synthetic and explicit read paths. Their Hermes plugins expose read tools only; CalDAV can use a host-bound authenticated transport. Python write functions require a trusted approval gateway and durable replay journal; no real account was connected.
- A bounded [Loxone status snapshot](docs/LOXONE_STATUS_ADAPTER.md) contract with a synthetic Hermes default and an optional host-bound authenticated read tool. It has no native Miniserver client or control command.
- An offline [invoice PDF intake, review and payment preview](docs/INVOICE_ADAPTER.md). The bounded PDF path hashes original digital PDF bytes and records page evidence; a local mock flow composes it with skonto and a masked payment draft. Document authenticity remains unresolved and no payment is made.
- A bounded [single-page web extractor](docs/WEB_EXTRACTION_ADAPTER.md) for supplied HTML, with optional static and browser Scrapling transports behind a trusted host egress gate. Its [Hermes tool](docs/WEB_RESEARCH_PLUGIN.md) is disabled by default and requires a host-injected transport and allowlist; no live browser fetch, broad crawl or paid fallback was verified.
- An opt-in [local archive reader](docs/LOCAL_ARCHIVE_READER.md) that inventories an explicitly approved directory and identifies exact byte duplicates without modifying files. A separate [local E2E6 mock](docs/ARCHIVE_LOCAL_E2E.md) connects real source and backup scans to an in-memory copy simulation; neither is a Hermes tool or a real migration adapter.
- An opt-in [routing evaluator](docs/HERMES_ROUTING_EVAL.md) for all 404 authored cases. It defaults to `NOT_RUN` and needs an explicit, externally budgeted model callback for actual decision evidence.
- An [offline adapter evaluator](docs/SKILL_ADAPTER_EVAL.md) that executes 107 cases across ten local synthetic workflows and fails on variant coverage gaps. The PowerPoint case stays `PARTIAL` without a renderer; Ubuntu CI requires its PDF and PNG evidence. It reports adapter evidence separately from Hermes routing and individual skill runtime.
- An optional [isolated Hermes routing sample](docs/HERMES_RUNTIME_VERIFICATION.md) that copies the skill tree into a temporary profile and requires a retained structured session trace before scoring one authored case. The dry run makes no model call.
- A [bounded local routing batch](docs/HERMES_ROUTING_EVAL.md) that inventories all 404 authored cases and can resume capped local Ollama/Hermes runs only from a matching revision and retained per-case traces. Its dry run reports all cases `NOT_RUN`.
- A [synthetic research composition](docs/RESEARCH_E2E_MOCK.md) that extracts pinned local pages, checks conflicting evidence and produces a decision brief without a live source or external action.
- A host-owned [one-time approval ledger](docs/APPROVAL_LEDGER.md) for the GMX and CalDAV Python write paths. Grant issuance still requires a real operator decision and trusted host integration.
- A host-side [input trust helper](docs/INPUT_TRUST_BOUNDARY.md) that binds source provenance to an exact local mock proposal. It requires an authenticating host and does not gate arbitrary Hermes tools.
- A [parent integration handoff](docs/PARENT_INTEGRATION_HANDOFF.md) pinned to the read-only `rogue-friday` snapshot, covering service authentication, tasks, activity, audit and event replay.
- Four [Content Studio skills](docs/CONTENT_STUDIO.md) for planning, kie.ai media, ElevenLabs narration and manual video editing. An optional host-bound Hermes plugin connects them to the companion dashboard's server-side provider endpoints, gated by exact paid-action approval.

`mock` means synthetic fixtures only. `read_only` permits verified observations through an adapter; the public weather reader needs no account. `live` requires a verified adapter, fresh capability and action-specific approval for higher-risk actions. Mail and calendar writes are implemented as gated Python adapter functions, but no trusted approval gateway or provider account has been connected. The full suite cannot presently perform those writes, operate banking or Loxone, file taxes or publish to the dashboard.

## Local use

On Windows, the source folder is `C:\Users\ByteNinja\Downloads\JARVIS_Installer\Skills`. Point Hermes `skills.external_dirs` at its `skills` child and enable `skills.write_approval: true`; see [installation](docs/INSTALLATION.md) and [configuration](docs/CONFIGURATION.md). A WSL Hermes process needs its Linux view of the same path.

On the operator's Windows Hermes v0.20.5 profile, this path is now configured and all 101 `friday-*` skills appear enabled. Skill write approval and the agent-created content scanner are enabled. This does not enable any optional plugin or verify model routing.

```powershell
python scripts/validate.py
python scripts/run_skill_cases.py
python scripts/evaluate_skill_adapters.py
python -m unittest discover -s tests -q
hermes skills list
```

These checks cover different things: structural validity, shared per-skill contracts, local adapter behavior, unit/mock behavior and discovery in the selected Hermes profile. Run them against the same revision. The per-skill report explicitly marks unexecuted Hermes routing and individual skill runtime; these checks do not prove production behavior.

## Documentation

| Need | Read |
|---|---|
| Choose a skill and understand coverage | [Catalog](docs/SKILL_CATALOG.md), [routing](docs/ROUTING.md) |
| Connect safely | [Architecture](docs/ARCHITECTURE.md), [capabilities](docs/CAPABILITIES.md), [approvals](docs/APPROVALS.md), [one-time grants](docs/APPROVAL_LEDGER.md), [contracts](docs/CONTRACTS.md), [Control API tasks](docs/CONTROL_API_TASKS.md), [weather adapter](docs/WEATHER_ADAPTER.md), [GMX mail](docs/GMX_MAIL_ADAPTER.md), [CalDAV](docs/CALDAV_ADAPTER.md), [invoice review](docs/INVOICE_ADAPTER.md), [web extraction](docs/WEB_EXTRACTION_ADAPTER.md), [local archive reader](docs/LOCAL_ARCHIVE_READER.md) |
| Operate and troubleshoot | [Operations](docs/OPERATIONS.md), [testing](docs/TESTING.md), [Hermes runtime verification](docs/HERMES_RUNTIME_VERIFICATION.md), [troubleshooting](docs/TROUBLESHOOTING.md) |
| Integrate dashboard | [Dashboard events](docs/DASHBOARD_EVENTS.md), [parent handoff](docs/PARENT_INTEGRATION_HANDOFF.md) |
| Contribute | [Skill authoring](docs/SKILL_AUTHORING.md), [security](docs/SECURITY.md), [reuse research](docs/REUSE_RESEARCH.md) |

Official upstream references: [Hermes Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills) and [Creating Skills](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills). Check the documentation for the installed Hermes version before relying on a feature.

Licensed under [MIT](LICENSE). Changes and maturity are tracked in [CHANGELOG.md](CHANGELOG.md).
