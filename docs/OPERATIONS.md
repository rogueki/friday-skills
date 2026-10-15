# Operations

## Routine local checks

1. Confirm the checkout, branch and staged files: `git status --short --branch` and `git diff --check`. Preserve other agents' work.
2. Run `python scripts/validate.py` and `python -m unittest discover -s tests -q` against the same revision. Inspect any errors before retrying.
3. Run `hermes skills list` in the profile that will load the suite. `hermes skills audit` and `hermes doctor` can add version-specific diagnostics; confirm availability with the installed CLI. A temporary `HERMES_HOME` is appropriate for a non-invasive discovery check.
4. Reconcile `registry/skills.json`, `registry/roadmap.json`, the catalog and physical `SKILL.md` folders. Missing or duplicate names mean the package is inconsistent.
5. Review the diff for tokens, real personal data, third-party code with unknown licenses and accidental inclusion of `MEMORY.md`/`SCOPE.md`/the local plan. Keep secrets in an external store.

## Before enabling an adapter

Identify its owner, exact target service, least permissions, supported modes, credential source, timeout/retry/idempotency behavior and tested failure path. Make it return fresh capability records. Place an action gate before every write and an independent verification after it. Test with synthetic/mock data, then a controlled service environment. Add redacted audit and only the dashboard mapping supported by the current Control API contract. A successful skill-list check alone is insufficient.

For long tasks, track state and completion evidence through a real Kanban adapter if available. If unavailable, return a local task outline or blocked result and do not claim remote task creation. For research, record source URLs/dates; for tax, finance and travel, recheck current official rules/prices before decisions.

## Changes and rollback

Version skill content and contract changes together. Re-run relevant local tests and Hermes discovery. Keep a prior Git revision or package export for rollback; avoid changing the live Hermes profile and repo checkout simultaneously during diagnosis. If a newly loaded skill routes incorrectly, remove its `external_dirs` reference or revert the specific change after examining the diff, then verify the old list. Report observed behavior and limits in the changelog/test report.

The companion `rogue-friday` repository, installer and dashboard are outside this package's write scope. No service deploy, active Hermes profile change or external write is implied by publishing this repo.
