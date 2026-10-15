# Testing and acceptance

Run from the repository root with Python 3.11+:

```powershell
python scripts/validate.py
python scripts/run_skill_cases.py
python -m unittest discover -s tests -q
hermes skills list
```

`validate.py` checks registry/roadmap parity, unique folder/frontmatter names, core metadata, JSON schemas and ignored local files. `run_skill_cases.py` executes shared policy/result contracts for all 101 case files and reports the §30 matrix. Current counts are 909 shared checks `PASS`, 404 routing expectations `DECLARED` and 1616 skill-runtime cases `NOT_RUN`. These counts include repeated checks of the same shared functions; they do not mean 909 independent skill implementations passed. The unit suite exercises reference policy, mock scenarios, registry, weather adapter, Control API task client and optional plugin logic. Hermes discovery must use the intended profile or an isolated temporary one. Record command, version, time, profile and exact pass/fail count. The isolated v0.20.5 profile discovered all 101 skills; three plugins passed separate registration checks without changing the active profile.

Each procedure should have a positive trigger, negative/collision cases, happy path, empty/invalid/partial input, missing/offline/stale capability, timeout/rate limit behavior, injection/secret/path/replay attempts, tier/approval checks and normalized output verification. A documented test matrix is evidence of planned cases only; executed mock tests must assert observed results. Source-dependent conclusions should carry links and retrieval times. No test may send mail, pay, book, file taxes, operate devices, delete archives or publish to the live dashboard.

The plan's ten E2E stories are mail, invoice, meeting, weather, family trip, photo archive, presentation, Loxone, Austrian tax and adapter outage. Build each with synthetic fixtures, explicit assertions on forbidden side effects and deterministic failure modes. Then test the real adapter separately behind a controlled environment and action approvals. Completing mock E2E does not certify live integration.

Acceptance evidence should use `PASS`, `FAIL`, `BLOCKED` or `NOT_RUN` per requirement. Plan §38 includes skill discovery, routing/security tests, modes, dashboard/Kanban/audit, capability failures, domain safety, docs, repeatable installer and write approval. Plan §39 additionally calls for mock adapters/plugins, registries, test report, acceptance matrix, ZIP and `v1.0.0` tag. Report what exists and what was actually exercised; do not tag a release just because documentation is complete.
