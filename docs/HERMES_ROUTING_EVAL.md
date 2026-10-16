# Hermes routing evaluation

`scripts/evaluate_hermes_routing.py` reads the four authored routing cases in every `skills/**/tests/cases.json` file. Its default run makes **no model call** and reports all 404 cases as `NOT_RUN`:

```powershell
python scripts/evaluate_hermes_routing.py --output artifacts/routing-eval.json
```

For an actual routing run, provide a Python callback and an explicit case cap:

```powershell
python scripts/evaluate_hermes_routing.py --provider my_router:route_decision --max-cases 4 --output artifacts/routing-eval.json
```

The named module must already be importable. Importing it and invoking its callback may make paid provider calls; the runner does not configure credentials, a model, or a cost limit. Use an external provider quota/budget and start with a small cap. Run in an isolated Hermes profile if using Hermes; do not point experimental callbacks at the active F.R.I.D.A.Y. profile. The runner does not mutate a profile or call Hermes by itself.

The callback receives one object with `request`, `candidate_skill`, and `catalog` (canonical skill names and trigger descriptions). It does **not** receive `expected`, `case_id`, or the case file path. Return an object such as:

```python
{
    "decision": "select",  # select | reject | defer, relative to candidate_skill
    "selected_skills": ["friday-weather"],
    "evidence": {
        "kind": "model_inference_claimed",
        "provider": "provider-id",
        "model": "model-id",
        "response_id": "provider-trace-id",
    },
}
```

`select` requires the candidate in `selected_skills`; `reject` and `defer` exclude it. `defer` means a clarification, policy gate, or explicit handoff to another specialist; a handoff target may appear in `selected_skills`. The runner accepts a legacy `jarvis-*` name only when `registry/skills.json` maps it unambiguously to a canonical `friday-*` name. It does not guess fuzzy aliases. Provider callbacks must distinguish a genuine handoff from simple rejection and should return only observed decisions.

Omit `evidence` or use `{"kind": "synthetic"}` for scripted/offline callbacks. Their `synthetic_match` is useful for testing the harness, but **never increments routing `PASS` or `FAIL`**; those cases stay `NOT_RUN`. `PASS` and `FAIL` require `model_inference_claimed` plus bounded provider, model and response identifiers. These identifiers are callback claims, not independently authenticated proof. Before publishing model routing results, verify corresponding provider traces, model revision, prompt/tool configuration, case-set commit, costs, and repeat runs outside this report. Do not label a scripted callback as model inference.

The JSON report includes a SHA-256 digest of the case set and catalog. Each case record includes candidate, source case file, case ID, expectation, observed decision, selected canonical skills, evidence class, elapsed time, and `PASS`/`FAIL`/`NOT_RUN`. It omits raw requests, responses, provider errors, credentials and trace content. A callback exception records only its exception type and leaves that case `NOT_RUN`. Remaining cases stay `NOT_RUN` after the cap. The CLI exits nonzero if any scored case fails. A green synthetic harness test is **not** evidence that Hermes selected the right skill.

Hermes v0.20.5 `hermes skills` exposes installation/discovery commands, not a deterministic automatic routing oracle. A real callback must invoke a deliberately configured Hermes/model session, observe the actual skill selection or `skill_view` tool call, and return only that observed result. A mocked tool call can test Hermes plumbing but must use `synthetic`. Until such a callback and verified provider traces exist, the established 404 routing expectations remain `DECLARED` in `run_skill_cases.py` and `NOT_RUN` for model inference here.

## Optional local Hermes sample

Run a single authored case without a model call first:

```powershell
python scripts/local_hermes_smoke.py --skill friday-archive-inventory --case-id positive --dry-run
```

Once local Ollama actually lists `qwen3:4b`, opt into one bounded model run:

```powershell
python scripts/local_hermes_smoke.py --skill friday-archive-inventory --case-id positive --run --output artifacts/local-routing-result.json --trace-output artifacts/local-routing-trace.jsonl
```

The harness uses a temporary profile and a **copy** of all packaged skills.
Hermes v0.20.5 requires at least 64,000 context tokens for agent initialization.
That profile requests exactly `model.context_length: 65536` and
`model.ollama_num_ctx: 65536` for local Ollama. Smaller values fail argument
validation before any model or Hermes process call. The default Hermes run budget
is 420 seconds, with a 480-second subprocess limit; startup and redacted
session export each have a separate 30-second limit. The result records these
requested settings and `effective_context_verified: false`. A configuration
request does not prove the context actually allocated by Ollama; inspect the
local runtime separately before interpreting a model result. The optional
`--context-tokens` (currently only 65536), `--run-budget-seconds` (180–600) and
`--timeout-seconds` flags apply only to this isolated run. The timeout must
exceed the run budget by 30–180 seconds and cannot exceed 780 seconds.
The large requested window may exceed available host/GPU memory; it is not
evidence that Ollama allocated that window or that the model can answer.
On 2026-10-15, the local `qwen3:4b` metadata reported 36 layers, eight
key/value heads, and 128 dimensions for both keys and values. At 65,536
tokens, an unquantized 16-bit KV cache alone would require 9.0 GiB
(`36 * 65536 * 8 * (128 + 128) * 2` bytes). The model file is 2.5 GB.
At that check, `nvidia-smi` showed only 3,531 MiB free on the 12,282 MiB
GPU, Windows reported 8,775,116 KiB free physical RAM, and `ollama ps`
showed no loaded model. The combined free GPU/RAM is barely above the
estimated cache plus model weights, before runtime, graph and host overhead;
the memory pools are not interchangeable. KV quantization or flash attention
could change the actual requirement, but neither was verified as active.
For that reason no new 65,536-token Hermes inference was attempted on this
host. The revised archive-positive routing result remains unobserved; the
earlier archive-to-storage misroute remains the only scored sample. Recheck
resources and effective Ollama context on a host with sufficient headroom
before running the command above.
This matters because Hermes' `skills` toolset includes `skill_manage` alongside
`skill_view`. It never uses `-z`/YOLO or preloads `--skills`. It returns
`NOT_RUN`/`PARTIAL` unless the structured `skill_view` call is found and a
redacted trace is retained. It requires exactly one full session in the isolated
Hermes JSONL export and takes the native session ID from that record, even if
quiet chat mode prints none. A single PASS/FAIL applies only to that case and
does not update this evaluator's 404-case aggregate. See [runtime verification](HERMES_RUNTIME_VERIFICATION.md)
for isolation, trace and scoring limits.

With `--trace-output`, a valid one-session redacted export is retained even
when no structured assistant `skill_view` call occurs. The result then stays
`NOT_RUN`: `trace_verified` and its SHA-256 attest to the retained session,
not to a scored routing decision. Review the local trace to diagnose the
model's tool behavior; the JSON result does not include session contents.
If Hermes exits nonzero before export, the result remains `NOT_RUN` and adds a
fixed `reason_code` for recognizable local model memory, context, Ollama
connection/model, CLI, config, or runtime dependency errors. Unknown failures
use `hermes_nonzero_exit`. Timeout codes identify version probe, chat, or
session export. Neither the smoke nor batch report copies Hermes stdout,
stderr, exception text, or request content into the diagnostic field. The
classification is a hint, not proof of the underlying failure; inspect the
isolated runtime separately when a code is ambiguous.
`hermes_context_minimum` identifies the explicit Hermes 64,000-token
initialization rejection if it is ever returned despite preflight validation.
On Windows, the isolated child process and capture decoder use UTF-8 so
Unicode skill-index output cannot fail at the local console code page. An
unclassified exit remains `hermes_nonzero_exit`; it must not be interpreted as
a model routing decision.

## Bounded local batch for all authored cases

`scripts/local_hermes_routing_batch.py` enumerates the full authored case set
in registry order. It uses the isolated `local_hermes_smoke.py` session once per
attempt. A dry run inventories the cases and writes no Ollama or Hermes call:

```powershell
python scripts/local_hermes_routing_batch.py --dry-run --output artifacts/routing-batch-preview.json
```

After the exact local `qwen3:4b` model is installed and the one-case harness has
been inspected, start with an explicit small cap. `--max-cases` limits **new
attempts in this invocation**, not the total report size:

```powershell
python scripts/local_hermes_routing_batch.py --run --max-cases 4 --output artifacts/routing-batch.json
python scripts/local_hermes_routing_batch.py --run --max-cases 4 --output artifacts/routing-batch.json --resume
```

Reports and redacted per-case JSONL traces are confined to ignored
`artifacts/`. Each report path gets its own trace directory. The report has no
raw request, model response or credential text.
It records the ordered case-set hash, Git HEAD, skill-tree and harness source
hashes, model, requested context and time budgets, case
identities, statuses, session IDs and trace hashes. Every attempted case first
gets an atomic `STARTED` reservation. Resume accepts only matching case set,
model, revision, skill tree and harness sources, then reopens and hashes each retained trace and
recomputes its status from structured assistant `skill_view` calls. Verified
zero-view traces are hash- and session-checked on resume, remain `NOT_RUN` with
`reason_code: no_skill_view`, and are not automatically retried. Use a new
report path for an intentional fresh attempt while keeping the first report
and trace for comparison. Verified cases are never attempted twice by resume.
A changed requested context or time budget also fails resume provenance checks;
start a new report path for a fresh configuration. Existing reports made with
the earlier report schema cannot be resumed by this version.
A previously started or finished case without verified trace blocks automatic
resume; `--retry-unverified`
explicitly permits a new attempt. Inspect its report and any trace before
using that option. `attempted_total` counts distinct cases and
`attempt_reservations_total` also counts explicit retries. An existing case
trace cannot be silently overwritten.

The report's `.lock` file prevents concurrent use of the same output path. A
crashed process may leave it behind; verify the prior process has ended and
inspect the report before removing that lock manually. Keep reports and traces
local: Hermes redaction is applied to exported sessions, but traces can still
contain case text. A `PASS` or `FAIL` reflects only one case's structured
`skill_view` observation. `PARTIAL` includes defer cases and ambiguous multiple
views; `NOT_RUN` includes cases without retained evidence and verified sessions
with zero structured views. This batch does not turn the separate 1,616
individual SKILL.md runtime checks into passing tests.
