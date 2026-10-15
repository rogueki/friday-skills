# Changelog

Changes are recorded for the independent F.R.I.D.A.Y. Skills package by RogueKI. Entries describe repository content; Hermes discovery and live service readiness require separate verification.

## Unreleased (registry 0.2.0)

- Added procedures and local cases for all 100 plan skills, plus the extra web research skill; live adapters are still unavailable.
- Add architecture, configuration, routing, capability, approval, security, testing, dashboard, operations, troubleshooting and authoring documentation.
- Keep the companion `rogue-friday` repository read only while this package evolves.

## 0.1.0 — 2026-10-15

- Created private `rogueki/friday-skills` repository with 10 core procedures and the additional `friday-web-research` procedure.
- Added 100-entry plan roadmap, packaged-skill registry, schemas, deterministic policy checks, validator and local tests.
- Verified initial 11 skills were discoverable by Hermes v0.20.5 in an isolated temporary profile; this did not configure the operator's active profile.
- Documented that local `friday.skill.*` records are separate from the companion application's `jarvis.task.*` and `jarvis.activity.appended` contract.
