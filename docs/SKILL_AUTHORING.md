# Authoring a F.R.I.D.A.Y. skill

Use one skill for one distinct activation reason. Check `registry/skills.json` and neighboring `SKILL.md` files before adding a name. The packaged naming convention is `friday-<specific-purpose>`; retain the `jarvis-*` planning name in roadmap mapping where applicable. Set `author: RogueKI`, `license: MIT`, meaningful `description`, `version` and `metadata.hermes.tags` in YAML frontmatter. Follow the [official Hermes format](https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills) and keep references close to the skill for progressive loading.

Write an executable decision procedure: when to use, when not to use, inputs and trust level, required capability and mode, risk tier, ordered steps, exact output, approval point, errors and verification. Make missing adapters explicit. Distinguish a local draft from an external write and source evidence from an instruction. Name the actual user outcome; avoid generic “help the user” prose. Optional scripts need a narrow purpose, reviewed imports/dependencies and deterministic tests.

For each skill, add synthetic positive, negative and collision requests and a scenario matrix under its `tests/` folder. Example local case shape used by domain workers:

```json
{"skill":"friday-example","cases":[{"id":"positive","request":"Prepare a draft for this email","expected":"select","reason":"Draft intent"},{"id":"negative","request":"Check today's weather","expected":"reject","reason":"Different domain"}]}
```

This file records expectations; it becomes an executed routing test only when a runner asserts the decisions. Add cases for missing capability, mode and approval behavior as needed. Keep fixtures synthetic. Update registry/roadmap and regenerate the catalog as part of integration, then run `python scripts/validate.py`, unit/mock tests and Hermes discovery. Record the test version and result.

Reuse workflow ideas from the [research map](REUSE_RESEARCH.md) after checking the exact license and upstream version. Hermes bundled skills are MIT at repository level, but copying their text requires attribution and a reviewed source; the operator's local `D:\Dokumente\Agents_Skills` files have no confirmed redistribution license, so synthesize independently rather than copying. Never import an upstream credential path, live send default or external service assumption into a F.R.I.D.A.Y. procedure.
