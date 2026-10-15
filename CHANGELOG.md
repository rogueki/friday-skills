# Changelog

Changes are recorded for the independent F.R.I.D.A.Y. Skills package by RogueKI. Entries describe repository content; Hermes discovery and live service readiness require separate verification.

## Unreleased (registry 0.3.0)

- Added procedures and local cases for all 100 plan skills, plus the extra web research skill; authenticated live integrations remain unverified.
- Add architecture, configuration, routing, capability, approval, security, testing, dashboard, operations, troubleshooting and authoring documentation.
- Keep the companion `rogue-friday` repository read only while this package evolves.
- Add an opt-in Hermes v0.20.5 plugin with four local mock tools; verified in an isolated profile. It is not a live adapter or a global policy gate.
- Map 101 skills to 63 logical capabilities, with every live/mock adapter marked unavailable until installed and verified.
- Add four routing examples and three executable shared contracts per skill; the report separates shared checks from unrun model routing and adapter behavior.
- Add deterministic negative mock scenarios, a synthetic Austrian grants fixture, Python 3.11 metadata and Windows/Linux CI.
- Add a bounded public GeoSphere forecast reader and optional Hermes weather tool; one live read-only forecast was verified, with no write path.
- Add an opt-in Hermes Kanban observer that journals sanitized task metadata locally and a transport-injected Control API task client tested against the pinned parent contract.
- Add bounded GMX IMAP reads and a Tier-2-gated SMTP Python adapter with durable send journal. The optional Hermes plugin exposes reading only and defaults to synthetic data.
- Add bounded CalDAV reads and a Tier-2-gated create/update Python adapter with ETag preconditions and durable replay journal. The optional Hermes plugin remains mock-only until trusted transport wiring exists.
- Document the read-only parent integration handoff and the remaining service auth, activity and task lifecycle contracts.
- Add an opt-in, bounded routing evaluation runner that separates synthetic callback checks from claimed model inference; its default reports all 404 decisions as not run.
- Add a read-only, provider-neutral Loxone status snapshot adapter and synthetic Hermes tool with allowlisted IDs, freshness and unit validation. Native Miniserver interoperability remains unverified.
- Replace model-supplied approval mappings for GMX and CalDAV mutations with host-owned, durable one-time grants. Add replay, mismatch, concurrent-consume and failure tests; operator authentication remains a host responsibility.
- Document the installed Hermes v0.20.5 routing path and the initially inactive `skills.write_approval` setting without making paid model calls.
- Connect the active Windows Hermes profile to this repository's 101 skills and enable `skills.write_approval` plus `skills.guard_agent_created`; preserve all other profile values and keep optional plugins disabled.
- Add offline structured invoice review with exact arithmetic, limited IBAN validation, duplicate and independent supplier checks, plus a masked non-executable payment preview. Original-document extraction and host evidence remain open.

## 0.1.0 — 2026-10-15

- Created private `rogueki/friday-skills` repository with 10 core procedures and the additional `friday-web-research` procedure.
- Added 100-entry plan roadmap, packaged-skill registry, schemas, deterministic policy checks, validator and local tests.
- Verified initial 11 skills were discoverable by Hermes v0.20.5 in an isolated temporary profile; this did not configure the operator's active profile.
- Documented that local `friday.skill.*` records are separate from the companion application's `jarvis.task.*` and `jarvis.activity.appended` contract.
