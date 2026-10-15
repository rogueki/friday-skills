# Troubleshooting

| Symptom | Check | Action |
|---|---|---|
| `hermes skills list` omits a skill | Correct Hermes profile, OS-specific path, exact `SKILL.md` folder/frontmatter name, `platforms`, duplicate names | Fix path or metadata; rerun list in same profile. |
| The suite appears twice | `create_dir` and `external_dirs` point to same physical tree | Keep one reference. |
| Validator reports registry mismatch | Count and names in `registry/skills.json` versus `skills/**/SKILL.md`, roadmap mapping | Reconcile source inventory; do not hide an unverified skill by deleting its tests. |
| A skill asks for a tool that is absent | Fresh capability record, mode, adapter installation and authentication | Return blocked/partial or synthetic mock result; never claim live success. |
| Approval accepted for the wrong action | Fingerprint, target, payload, expiry, tier and second factor | Stop before side effect; invalidate and request a new action-bound approval. |
| Result says complete but task has no proof | `verification`, `actions_taken`, pending approvals, server response | Change to partial/blocked until actual evidence is recorded. |
| Dashboard is blank | Whether any Control API adapter exists, actual server operation and acknowledgement | Local `friday.skill.*` records are not publishable; implement and test the adapter against current AsyncAPI. |
| Research or tax claim looks stale | Source URL, retrieved date, applicable region/year | Refresh against authoritative current sources and mark uncertainty. |
| An automation fires unexpectedly | Scheduler/hook config, trigger origin, target and service logs | Disable the specific automation/adapter, inspect audit and scope; a `SKILL.md` alone cannot schedule work. |

To isolate discovery, use a temporary Hermes home as described in [configuration](CONFIGURATION.md). To isolate policy logic, run the Python unit tests. To isolate external effects, inspect the service-side logs and actual target state; do not use a local mock event as proof. When a command fails repeatedly, read its error, fix the cause and then rerun once.
