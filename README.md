# F.R.I.D.A.Y. Skills

**Give F.R.I.D.A.Y. the skills for your work.** This is the official companion repository for the [F.R.I.D.A.Y. framework](https://github.com/rogueki/rogue-friday): 106 focused Hermes procedures for office work, research, communication, home, media and operations. The framework supplies the installer, voice assistant, dashboard and service integrations; this repository extends what Friday can guide and automate. Both repositories are MIT licensed, so you can adapt skills and build a connector for a provider your setup needs.

**Get started:** [Install the framework](https://github.com/rogueki/rogue-friday#schnellstart) · [Browse the 106 skills](docs/SKILL_CATALOG.md) · [Connect accounts and tools](docs/SETUP_CATALOG.md) · [Create a custom skill](docs/SKILL_AUTHORING.md). Optional provider integrations are configured per installation; the catalog explains what is ready and what needs a connector or account.

**RogueKI** maintains this independent Hermes Agent skill suite. F.R.I.D.A.Y. is the successor assistant in this project's own story: a coordinating core calls focused specialists for executive work, communication, finance, home, family, media, research and operations. This project is not affiliated with Marvel.

The [roadmap](registry/roadmap.json) names **100 skills from the implementation plan**. `friday-web-research`, four Content Studio procedures and one Discord communication procedure extend that plan. The current [registry/skills.json](registry/skills.json) lists 106 packaged procedures, cross-checked against `skills/**/SKILL.md`; [the catalog](docs/SKILL_CATALOG.md) explains categories, triggers and readiness. A procedure marked installable or mock-ready does not imply a live connector.

## Start here for the public beta

The [rogue-friday framework](https://github.com/rogueki/rogue-friday) runs the assistant, dashboard and services. This repository adds 106 focused Hermes decision procedures and offline checks. They cover executive planning and mail, calendar and weather, finance and Austrian tax, Loxone and energy, family media and travel, Office documents and PowerPoint, research, local knowledge, voice and system operations. For example, `friday-executive-mail-manager` proposes inbox priorities, `friday-calendar-manager` structures calendar work, `friday-loxone-status` describes bounded device reads, and `friday-kie-media` prepares a reviewed media request.

To make the procedures discoverable, clone this repository and point Hermes `skills.external_dirs` at its `skills` subdirectory; then run `hermes skills list` and compare IDs with `registry/skills.json`. See [installation](docs/INSTALLATION.md) and [configuration](docs/CONFIGURATION.md). Optional plugins and provider accounts have their own setup. The [integration catalog](docs/SETUP_CATALOG.md) explains which skill paths need an account, where settings belong and what is still unimplemented. GMX, CalDAV, Kie.ai and ElevenLabs require separate host/server setup for their live paths; Obsidian and local Computer Use do not require external accounts.

Beta readiness is per capability and per host. In the integrated Friday dashboard, the Skills view explains catalogued account prerequisites, required permissions and cost notes, then links to Settings > Skill Accounts for setup. Missing permission, pricing or connection evidence stays unknown; a visible requirement or configured account does not prove a provider is reachable or a skill can execute. The package contains procedures and local mock tests, while many live provider transports, approval gateways and full Hermes runtime checks remain open. The static setup catalog still reports `live_status: unknown` for every skill; check the actual Hermes profile and provider connection before relying on an action.

## What this repository provides

- Hermes `SKILL.md` decision procedures, examples and local tests.
- Local schemas and Python policy/mock helpers that an integration must **explicitly call**. Installing skills alone does not enforce approvals, prevent tool calls or emit dashboard events.
- An optional [native Hermes plugin](plugins/CONTRACT.md) with four local mock tools. It was loaded in an isolated test profile and is not enabled in the active profile. Its policy tool returns a decision but cannot enforce other Hermes tools or perform external actions.
- An optional [GeoSphere weather tool](docs/WEATHER_PLUGIN.md) backed by a bounded public read adapter, and a separate [Kanban observer](docs/KANBAN_OBSERVER.md). All three plugins passed isolated Hermes v0.20.5 registration checks; none is enabled in the active profile.
- A [Control API task client](docs/CONTROL_API_TASKS.md) with injected transport and mock tests. The companion `rogue-friday` repository supplies the dashboard and Control API; this package does not ship their credentials.
- Optional [GMX mail](docs/GMX_MAIL_ADAPTER.md) and [CalDAV calendar](docs/CALDAV_ADAPTER.md) adapters with bounded synthetic and explicit read paths. Their Hermes plugins expose read tools only; CalDAV can use a host-bound authenticated transport. Python write functions require a trusted approval gateway and durable replay journal; no real account was connected.
- The companion [Friday dashboard](https://github.com/rogueki/rogue-friday) includes a local calendar: the owner can create, view, edit and delete events without a provider account. Friday also supports speaker-verified local event changes by voice, with a spoken preview and a second confirmation. It can read a configured ICS/CalDAV calendar and create a CalDAV event after an owner preview and confirmation. Its installer provisions the separate `friday-dashboard-calendar` Hermes read tool with a private calendar-only loopback key. That tool can read local and configured external events; no provider credential is copied into Hermes and no write tool is exposed. The older `friday-caldav` plugin retains its independent synthetic/host-injected contract. ICS feeds remain read only, and provider-specific OAuth connectors can be added to the framework for individual installations.
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

The companion [rogue-friday dashboard](https://github.com/rogueki/rogue-friday) also has a direct **Skills → Coding mit Hermes** route that can launch the selected native Codex, OpenCode or Claude Code CLI in a chosen Git repository, with run status, output and stop controls. It is a framework feature separate from this package's `friday-project-context-builder` and Hermes `terminal`/`process` skill handoff. The chosen CLI must be installed and authenticated in Friday-Ubuntu; process start alone does not prove a successful model request. The framework's optional CLI setup supports interactive Codex sign-in with a supported ChatGPT plan and Claude Code sign-in with a Claude Pro/Max plan. Those subscriptions authorize the respective coding CLI, not Friday's general model routing. See [the workflow guide](docs/HERMES_WORKFLOWS.md).

On Windows, choose an installation folder for this repository. Point Hermes `skills.external_dirs` at its `skills` child and enable `skills.write_approval: true`; see [installation](docs/INSTALLATION.md) and [configuration](docs/CONFIGURATION.md). A WSL Hermes process needs its Linux view of the same path. The `rogue-friday` installer places this repository under `<InstallRoot>\skills\friday-skills` and configures discovery automatically.

On the development installation, Hermes v0.22.2 discovered the previous 105 Friday-Skills alongside 53 bundled skills. Your installation may differ; run `hermes skills list` in the same profile that runs Friday. See the [setup catalog](docs/SETUP_CATALOG.md) for account requirements. Discovery and activation do not establish live provider readiness. The framework installer also applies the reviewed [Himalaya v2 compatibility overlay](compat/hermes/himalaya-v2/SKILL.md) when its optional Himalaya 2.2.1 CLI and the known Hermes v1 mail skill are present. It backs up the original and refuses unknown upstream changes; no mailbox is contacted during installation.

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
