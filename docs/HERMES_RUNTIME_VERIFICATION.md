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
- `-z`/`--yolo` bypasses dangerous-command approval and must not be used for
  routing evaluation. Hermes v0.20.5 instead exposes `hermes chat -q` or
  `--query-file`, `--provider`, `--model`, `--toolsets`, `--max-turns` and
  `--run-budget`. These limits do not prove a hard USD cap for a cloud model.
- The model names available to Codex Sol/Luna workers are not established as
  Hermes provider/model identifiers. Worker evaluations would not prove Hermes
  routing.

## Isolated local sample

The opt-in [local smoke harness](../scripts/local_hermes_smoke.py) selects one
authored case by skill name and case ID. Its `--dry-run` mode copies the full
skill tree into a new temporary `HERMES_HOME`, builds a minimal local-only config
and previews bounded CLI flags. It never calls Ollama or Hermes in this mode.
The `--run` mode first requires an exact `qwen3:4b` entry from local Ollama's
`127.0.0.1:11434/api/tags`; it has no cloud fallback. It starts Hermes from a
new temporary working directory with a scrubbed subprocess environment,
`--provider custom --model qwen3:4b --toolsets skills --max-turns 2
--run-budget 420 --ignore-rules -Q`. The query is passed through a file without
the expected decision or target skill name. Python applies a 480-second chat
subprocess timeout by default, with separate 30-second limits for version
probe and session export. The isolated config requests both
`model.context_length` and `model.ollama_num_ctx` at 65,536; this does not
verify that Ollama allocated the requested context. The local memory estimate
and the decision to defer another model attempt are recorded in
[routing evaluation](HERMES_ROUTING_EVAL.md).

`--toolsets skills` exposes `skill_manage` as well as `skill_view` in this Hermes
version. The copied tree is the only external skill directory in that run, so
a skill-management edit targets disposable files. `--ignore-rules` omits ambient
AGENTS/SOUL/memory injection. No `--skills` preload, `-z` or
`--ignore-user-config` is used. The active profile and source skill tree are
never passed to the model subprocess.

With `--trace-output artifacts/local-routing-trace.jsonl`, a Hermes-redacted
session export is retained for review; this file may still contain case text
and stays local under ignored `artifacts/`. Hermes v0.20.5 JSONL export contains
one full session per line. The harness exports by `--source` from the new
temporary home and requires exactly one row with a native
`YYYYMMDD_HHMMSS_<6 hex>` session ID. It never infers an ID from chat stdout,
which `-Q` may suppress. Zero, multiple, malformed or conflicting session IDs
cannot be scored. The harness records Hermes version,
case-set SHA, the ID from that row, trace hash, observed `skill_view`
names, elapsed time and exit status. It does not print raw model output. A
missing model, process failure, invalid session export or missing structured assistant tool call remains
`NOT_RUN`. An unretained or ambiguous trace is `PARTIAL`. A retained single
`skill_view` can score select/reject for that one case; defer remains `PARTIAL`
because tool selection alone cannot establish why the model deferred. Inspect
the retained trace and Ollama logs before treating even a scored sample as
independent routing evidence. It says nothing about other cases or runtime
skill correctness.

The full suite's 404 routing expectations and 1,616 skill-runtime cases remain
unexecuted. A green registration, local mock, or inferred provider identity
does not close those acceptance items.
