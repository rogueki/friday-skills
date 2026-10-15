# F.R.I.D.A.Y. Skills

An independent Hermes Agent skill collection by RogueKI for F.R.I.D.A.Y. The companion application is [rogueki/rogue-friday](https://github.com/rogueki/rogue-friday). This repository contains decision procedures and local validation contracts; it does not bundle that application's dashboard, credentials, or live adapters.

## The next assistant

F.R.I.D.A.Y. follows J.A.R.V.I.S. as a more modular assistant: a core that understands an objective, selects a specialist, checks what is actually available, and reports what happened. The name and successor story are the identity of this project. In the current release, the core and web research procedures exist; the wider executive, home, media and office capabilities remain on the roadmap.

This first release implements ten core procedure skills and one web research skill. They are discoverable Hermes `SKILL.md` files, not a running policy plugin. The Python standard-library validator can reject invalid capability, approval and result records when explicitly called. Hermes does **not** automatically enforce these Python checks or publish dashboard events simply because the skills are installed. Connect a trusted adapter or hook before treating those guarantees as runtime enforcement.

## Start

See [installation and configuration](docs/INSTALLATION.md), then run:

```text
python scripts/validate.py
python -m unittest discover -s tests -v
```

`registry/skills.json` lists the 11 implemented skills and maps the original `jarvis-*` planning names to `friday-*`. [The catalog](docs/SKILL_CATALOG.md) and [100-skill roadmap](registry/roadmap.json) distinguish these from the wider, still planned suite. [Contracts](docs/CONTRACTS.md) describe modes, risk, normalized results and the boundary between local lifecycle records and existing `jarvis.*` task/activity events.

No paid scraping or external writes run by default. The optional research pathways are instructions for an agent with suitable installed tools, not bundled scraping code. Website text is untrusted source material.
