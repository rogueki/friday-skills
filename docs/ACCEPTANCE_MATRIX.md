# Acceptance matrix — plan §§38–39

Status means `PASS` (observed), `PARTIAL` (bounded local evidence), `BLOCKED` (depends on the separate application or adapter), or `NOT RUN`. This is a 0.2.0 procedure-suite milestone, not a v1.0.0 acceptance claim.

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| All 100 plan skills plus extra web research | PASS | 101 valid `SKILL.md`; 100 roadmap entries implemented. |
| Hermes discovery and no name conflict | PASS | Isolated Hermes v0.20.5 profile showed 101 enabled rows; registry and path uniqueness validated. |
| Positive, negative and collision cases per skill | PARTIAL | All 101 case files exist and parse; model routing outcomes have not been executed across all cases. |
| Mock mode and no real test side effects | PARTIAL | 29 local tests, mock adapters and optional Hermes plugin have no execute path, ten synthetic scenarios; individual skill procedures are text, not executable domain adapters. |
| Approval tiers, input trust, capability failure | PARTIAL | Local policy/mock tests pass. A trusted live adapter must call preflight synchronously before every external action; no Hermes-wide hard gate is registered. |
| Dashboard events, Kanban and audit | BLOCKED | Local lifecycle records and non-publishable mapping exist; no Control API publisher, server acknowledgement, or live Kanban integration. |
| Mail injection, weather route, invoice no payment | PARTIAL | Representative synthetic regression tests pass; no live mail/weather/finance adapters tested. |
| Tax never auto-submits, booking never auto-executes, archive not auto-deleted, Loxone write gated | PARTIAL | Procedures and mock traces enforce these boundaries; provider-side behavior remains untested. |
| PowerPoint worker flow | PARTIAL | Synthetic brief/render fixture and QA trace; no Windows Office Worker connection or rendered production deck. |
| Documentation and 15 automation definitions | PASS | Required operating/installation/security docs and catalog present; automations intentionally disabled. |
| Repeatable install and ZIP export | PASS | PowerShell/Bash repeat install and deterministic ZIP/CRC checked locally. |
| Skill write approval active in operator profile | NOT RUN | Configuration example sets `skills.write_approval: true`; the active Hermes profile was not changed. |
| Optional Hermes local plugin | PASS | Isolated Hermes v0.20.5 profile loaded `friday-local` with four mock tools; it remains disabled in the active profile and provides no global policy gate. |
| Live adapters and production tests | BLOCKED | Need explicit integration into the separate `rogue-friday` stack, which was read-only during this work. |
| `v1.0.0` tag | NOT RUN | Deferred until live contract integration and acceptance criteria above are met. |

See [test report](TEST_REPORT.md), [contracts](CONTRACTS.md), and [integration boundaries](ARCHITECTURE.md). The companion [`rogue-friday`](https://github.com/rogueki/rogue-friday) repository was not edited.
