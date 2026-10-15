# Hermes runtime verification boundary

RogueKI checked the locally installed Hermes Agent v0.20.5 (`68518c1f`) on
2026-10-15 without running a model. The operator's active Windows profile was
subsequently connected to this repository's skill directory. This is not
evidence of routing success.

## Current local evidence

- The active profile resolves `skills.external_dirs` to this repository's `skills`
  directory, `skills.write_approval` to `true`, and `skills.guard_agent_created`
  to `true`. `hermes skills list --enabled-only` shows 101 `friday-*` rows.
  A local backup preceded the configuration change and all other parsed config
  values stayed equal. Write approval governs Hermes skill-management edits,
  not Tier 2/3 external actions. No staged-write flow was exercised.
- Hermes places an `<available_skills>` index into its model prompt and the model
  may call `skill_view(name)` to load a skill. `--skills` preloads a named skill
  and therefore cannot prove automatic routing. Local source:
  `agent/prompt_builder.py` and `tools/skills_tool.py` in the installed Hermes
  v0.20.5 checkout.
- A one-shot `hermes -z` can write a usage file after inference. Hermes offers
  no verified hard USD cap in this CLI. Turn and wall-clock limits reduce
  loops but cannot bound cost of one provider request. The operator's existing
  login is not a dedicated evaluation budget.
- The model names available to Codex Sol/Luna workers are not established as
  Hermes provider/model identifiers. Worker evaluations would not prove Hermes
  routing.

## Controlled future sample

1. Create a fresh isolated `HERMES_HOME` with only the intended
   `skills.external_dirs` path and an explicitly chosen provider/model. Do not
   use `--ignore-user-config`, which would bypass that isolated configuration.
2. Enforce a small provider-side quota or a hard request/token budget through
   an external proxy. `--usage-file` is retrospective and is not this gate.
3. Set `agent.max_turns: 2` and `agent.run_budget_seconds: 30` in that isolated
   profile. Run one authored positive case with `hermes -z --usage-file
   <usage.json> '<request>'`; do not preload the expected skill.
4. Export the new session as JSONL and inspect the actual `skill_view` tool
   call, selected name and model response. Redact any user text or secrets
   before retaining evidence. Record Hermes commit, provider/model revision,
   case-set SHA, usage and profile path.
5. Score the observation with [the routing evaluator](HERMES_ROUTING_EVAL.md)
   only when the callback is backed by that trace. A synthetic callback stays
   `NOT_RUN` for model-routing acceptance.

The full suite's 404 routing expectations and 1,616 skill-runtime cases remain
unexecuted. A green registration, local mock, or inferred provider identity
does not close those acceptance items.
