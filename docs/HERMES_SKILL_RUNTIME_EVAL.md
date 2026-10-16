# Isolated Hermes skill runtime evaluation

RogueKI / F.R.I.D.A.Y. One optional `friday-weather` case checks the actual
Hermes path: skill index → assistant `skill_view(friday-weather)` → assistant
`friday_weather_forecast` call in `mock` mode → correlated tool result →
assistant answer explicitly labelled synthetic. This differs from directly
calling the Python plugin handler or running the offline E2E4 fixture.

The runner defaults to a dry run and reports `NOT_RUN` without calling Hermes
or Ollama:

```powershell
python scripts/evaluate_hermes_skill_runtime.py
```

Only an explicit `--run` starts one inference, after an exact model match in
`http://127.0.0.1:<port>/api/tags`. Both model and port are allowlisted. For
example, once the local model is installed and the host has sufficient memory:

```powershell
python scripts/evaluate_hermes_skill_runtime.py --run --model qwen3.5:0.8b --ollama-port 11435 --trace-output artifacts/hermes-weather-runtime.jsonl
```

The runner creates a disposable `HERMES_HOME`, copies all 101 skills, and
stages only the Weather plugin, adapter, and synthetic fixture into separate
temporary support paths. The staged plugin and adapter reject every mode
except `mock`; source files remain unchanged. The environment has no ambient
API keys, proxies, or active profile paths. Hermes v0.20.5 is invoked with
`skills,friday_weather`, bounded turns/time, local Ollama only, and no skill
preload. Its redacted session export is retained under ignored `artifacts/`,
with a SHA-256 digest in the result. That export can still contain the prompt
and response, so keep it local. Process stdout/stderr and raw tool content
are not printed by the runner. The report also pins model, loopback port, query
hash and hashes of the relevant source skill, plugin, adapter and fixture.

`PASS` requires one native session, exactly the target structured skill view,
its correlated tool response containing the `friday-weather` skill frontmatter
before the Weather call, one explicit mock Weather call, a correlated completed synthetic read result
with `weather.read` and `write_effect=false`, and a final assistant response
that identifies the data as synthetic or mock. Wrong skill, live mode, missing
tool call/result, blocked result, or unlabelled answer is `FAIL`. Missing model,
Hermes failure, invalid/missing export, or timeouts remain `NOT_RUN`.

`tests/test_hermes_skill_runtime.py` checks parser behavior with fabricated
session structures and checks dry-run isolation. A parser `PASS` in that unit
test is **not** a Hermes runtime pass. No `--run` has been executed as part of
this implementation. The suite's 1,616 individual skill-runtime cases remain
`NOT_RUN` until observed Hermes sessions exist for each case; this one
optional positive Weather run would cover at most one case. It does not prove
voice playback, default-location resolution, live provider behavior, or the
full E2E4 contract.
