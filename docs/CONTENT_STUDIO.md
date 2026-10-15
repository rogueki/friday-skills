# Content Studio skills

RogueKI's F.R.I.D.A.Y. Content Studio skills live in this separate `friday-skills` repository under `skills/media/`:

| Skill | Purpose | Runtime readiness |
| --- | --- | --- |
| `friday-content-planning` | Ideas, posting drafts and version 1 `plan.json` | Procedure and offline cases |
| `friday-kie-media` | Reviewed kie.ai image/video task request and result checks | Procedure; dashboard endpoint exists in local companion branch, Hermes bridge absent |
| `friday-elevenlabs-voice` | Reviewed script and MP3 speech generation | Procedure; dashboard endpoint exists in local companion branch, Hermes bridge absent |
| `friday-video-editing` | Edit decision list and manual CapCut handoff | Procedure only; no verified CapCut automation API |

The companion implementation is on local `rogue-friday` branch `codex/content-studio-oct15`. Its `docs/CONTENT_STUDIO.md` describes server routes, key handling and tests. Neither branch is published yet. A Hermes runtime can discover these SKILL.md files through `skills.external_dirs` pointing to this repository's `skills` directory. Discovery does not install or authenticate a Control API client. Do not pass provider keys through skills, prompts or `plan.json`; the companion Control API keeps them server-side.

All four cases files define routing expectations and synthetic shared-policy contracts. They do not demonstrate live model routing, provider generation or file export. No paid live API calls were run.
