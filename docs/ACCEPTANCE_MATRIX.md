# Acceptance matrix — plan §§38–39

Status means `PASS` (observed), `PARTIAL` (bounded evidence), `FAIL` (observed unmet condition), `BLOCKED` (depends on the separate application or adapter), or `NOT RUN`. This is a 0.3.0 integration milestone, not a v1.0.0 acceptance claim.

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| All 100 plan skills plus extra web research | PASS | 101 valid `SKILL.md`; 100 roadmap entries implemented. |
| Hermes discovery and no name conflict | PASS | Isolated Hermes v0.20.5 profile showed 101 enabled rows; registry and path uniqueness validated. |
| Positive, negative, ambiguity and collision cases per skill | PARTIAL | 404 authored routing expectations across 101 files. The opt-in evaluator reports `404 NOT_RUN` with no provider; model routing outcomes have not been executed. |
| Skill test matrix and shared mock contracts | PARTIAL | Plan §30–31 runner executes 909 repeated shared policy/result checks; 1616 skill-runtime cases remain `NOT_RUN`. These checks do not execute individual skill procedures. |
| Mock mode and no real test side effects | PARTIAL | 126 local tests and ten synthetic scenarios use no external mutations. One separate GeoSphere GET verified the weather reader; GMX, CalDAV and Loxone status tests use only fixtures/injected transports. Other skill procedures remain text or lack adapters. |
| Approval tiers, input trust, capability failure | PARTIAL | Local policy/mock tests pass. GMX and CalDAV writes now consume a host-owned one-time grant before an external attempt. Operator authentication and capability provenance still need a trusted host; no Hermes-wide hard gate is registered. |
| Dashboard events, Kanban and audit | BLOCKED | Local lifecycle records, an optional Hermes Kanban observer and a mock-tested Control API task client exist. The pinned [parent handoff](PARENT_INTEGRATION_HANDOFF.md) identifies service-auth and activity-ingest work; parent activity/audit APIs are read-only. There is no verified publisher or live task integration. |
| Mail injection, weather route, invoice no payment | PARTIAL | Synthetic negative variants pass. The public GeoSphere forecast reader returned one real Vienna forecast; bounded GMX read/send adapter paths passed offline tests only. Finance remains without an adapter. |
| Tax never auto-submits, booking never auto-executes, archive not auto-deleted, Loxone write gated | PARTIAL | Procedures and mock traces enforce these boundaries; provider-side behavior remains untested. |
| PowerPoint worker flow | PARTIAL | Synthetic brief/render fixture and QA trace; no Windows Office Worker connection or rendered production deck. |
| Capability registry, documentation, 15 automations and CI | PARTIAL | 63 logical IDs mapped to 101 skills. Static adapter availability remains false; the opt-in weather tool returns fresh per-call public read evidence. Docs/catalog and Windows/Ubuntu CI passed on `f4ab9d9`; automations remain disabled. |
| Repeatable install and ZIP export | PASS | PowerShell/Bash repeat install and deterministic ZIP/CRC checked locally. |
| Skill write approval active in operator profile | FAIL current state | Read-only Hermes v0.20.5 inspection resolved `skills.write_approval` to `false`; the active profile was not changed. See [runtime verification](HERMES_RUNTIME_VERIFICATION.md). |
| Optional Hermes plugins | PASS registration | Isolated Hermes v0.20.5 `plugins doctor --ci` registered four local mock tools, one weather tool, one GMX read tool, one CalDAV mock read tool, one Loxone synthetic read tool and three Kanban hooks. None is enabled in the active profile; no global policy gate exists. |
| Live adapters and production tests | PARTIAL | One public weather GET was verified. GMX/CalDAV adapter code has offline tests but no provider interoperability or trusted write gateway; Loxone has a read-only snapshot contract without a Miniserver transport. Banking, Office and Control API runtime integration remain unverified or absent. `rogue-friday` stayed read only. |
| `v1.0.0` tag | NOT RUN | Deferred until live contract integration and acceptance criteria above are met. |

See [test report](TEST_REPORT.md), [contracts](CONTRACTS.md), and [integration boundaries](ARCHITECTURE.md). The companion [`rogue-friday`](https://github.com/rogueki/rogue-friday) repository was not edited.
