# Content Studio skills

RogueKI's F.R.I.D.A.Y. Content Studio skills live in this separate `friday-skills` repository under `skills/media/`:

| Skill | Purpose | Runtime readiness |
| --- | --- | --- |
| `friday-content-planning` | Ideas, posting drafts and version 1 `plan.json` with selectable Instagram, Facebook, TikTok and YouTube targets | Procedure and offline cases |
| `friday-kie-media` | Reviewed kie.ai image/video task request and result checks | Procedure plus optional Hermes Control API bridge |
| `friday-elevenlabs-voice` | Reviewed script and MP3 speech generation | Procedure plus optional Hermes Control API bridge |
| `friday-video-editing` | Edit decision list and manual CapCut handoff | Procedure only; no verified CapCut automation API |

The companion implementation is on local `rogue-friday` branch `codex/friday-main-refresh-20261016`. Its `docs/CONTENT_STUDIO.md` describes server routes, key handling and tests; `docs/CONTENT_STUDIO_PUBLISHING.md` tracks the social publishing contract. A Hermes runtime can discover these SKILL.md files through `skills.external_dirs` pointing to this repository's `skills` directory. Discovery alone does not enable a Control API connection. Do not pass provider keys through skills, prompts or `plan.json`; the companion Control API keeps them server-side.

A voice request to upload a Story can prepare a draft and ask for the exact asset and destinations. The skill must not call it published: the dashboard currently has no Meta, TikTok or YouTube account connection or publishing adapter. The optional kie.ai and ElevenLabs bridge is only for media creation, not social posting. The dashboard removed paid-action checkboxes in favor of a current request preview and explicit start button; an eventual Hermes voice action needs its own bound spoken confirmation.

## Optional Hermes bridge

`plugins/friday_content_studio` registers eight tools. `friday_studio_read_plan` reads the server-owned plan and its revision. `friday_studio_write_plan` replaces the complete version 1 plan only with an explicit `expected_revision`; the bridge sends that value as `If-Match` with CSRF. A `409` becomes `revision_conflict` and stops. The caller must read the latest plan, compare changes and ask the user how to resolve them before another write. A lost PUT response becomes `unknown_plan_outcome`; read the server state before deciding what happened. Neither plan tool publishes content or calls a paid provider.

`friday_studio_create_production` uses an idea ID and the exact current plan revision to request the dashboard's automatic media, voice and local MP4 production. Before it starts, the bridge reads the plan and presents the idea and request to the trusted host approval callback. Only a confirmed request with a stable idempotency key is sent. `friday_studio_production_status` reads the durable job state; `friday_studio_cancel_production` stops further work, though an already submitted provider call may incur charges. A lost start or cancel response is reported as `unknown_production_outcome` without an automatic retry. `provider_unknown` and `speech_unknown` require operator review. These tools do not publish to social platforms. The Control API must have Content Studio enabled, provider keys configured and FFmpeg available before production can start.

The existing `friday_studio_create_media`, `friday_studio_media_status` and `friday_studio_create_speech` tools remain for paid generation. `adapters/content_studio_control.py` validates a loopback-only Control API origin, sends a host-owned session and CSRF token, bounds requests/responses and never automatically retries writes. No provider key enters Hermes; kie.ai and ElevenLabs keys stay on the dashboard server, where Settings values are encrypted at rest with a key derived from `auth.key`. The plugin does nothing live unless explicitly enabled and bound.

For a local interactive Hermes session, copy `plugins/friday_content_studio` into an isolated Hermes profile's `plugins/` directory and make this repository's `adapters/` and `shared/` importable through a dedicated support directory, as in [the existing plugin installation pattern](../plugins/CONTRACT.md). Set `FRIDAY_SKILLS_ROOT` to that support directory. Enable `friday-content-studio` in the profile's `plugins.enabled` list. Supply the following values **locally to the Hermes process**, never in a chat or repository:

| Variable | Meaning |
| --- | --- |
| `FRIDAY_CONTROL_API_ORIGIN` | Local Control API origin, for example `http://127.0.0.1:8384` |
| `FRIDAY_CONTROL_API_SESSION` | Current owner `friday_session` cookie value |
| `FRIDAY_CONTROL_API_CSRF` | Current session's CSRF token |
| `FRIDAY_CONTENT_STUDIO_OUTPUT_DIR` | Existing trusted directory for generated MP3 files |
| `FRIDAY_CONTENT_STUDIO_INTERACTIVE_APPROVAL=1` | Enables a local terminal prompt for each exact paid request |

The operator must type `YES` for each exact paid request. Without an interactive terminal, missing binding, denied approval, or missing output directory, the tool fails closed. A custom host can instead call `register(ctx, host=StudioHostBinding(...), output_dir=...)` with its own trusted approval callback and injected transport. Model-supplied tool arguments cannot set the origin, session, CSRF or output path. The API requires its own owner role, CSRF, feature toggle and server-side key as further gates.

No live Control API login or paid provider call was performed. The fake API tests cover plan read/write, CSRF, `If-Match`, conflict without retry, approved production start/status/cancel, blocked stale or unapproved starts, Hermes handler to fake authenticated Control API transport, and response/MP3 file. The plan and production APIs are owner-only; only the Control API enforces those server-side gates. A live plan round trip and live provider result remain unverified.

All four cases files define routing expectations and synthetic shared-policy contracts. They do not demonstrate live model routing or provider generation. No paid live API calls were run.
