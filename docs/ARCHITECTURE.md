# Architecture and trust boundaries

```text
User / authorized automation
    → intent and task plan → F.R.I.D.A.Y. Hermes SKILL.md procedure
    → capability check → trusted tool/adapter → verification
    → normalized result → optional trusted task/activity publisher → dashboard
```

The `skills/` tree holds **procedures**, not authenticated service implementations. Hermes can discover their frontmatter and load instructions. `registry/skills.json` inventories packaged procedures; `registry/roadmap.json` maps all 100 original plan names to `friday-*` names. The extra web research skill is outside the 100. `shared/schemas/` and `shared/policy.py` define local data shapes and checks; `shared/runtime.py` is a deterministic mock harness. No skill automatically invokes these Python checks. The optional [local plugin](../plugins/CONTRACT.md) exposes four mock tools. A separate [weather plugin](WEATHER_PLUGIN.md) can invoke a bounded public GeoSphere GET after explicit enablement; a [Kanban observer](KANBAN_OBSERVER.md) stores sanitized local lifecycle metadata.

Mail, CalDAV, banking, Loxone, media, Office, voice and Control API access still need their own adapters and authentication. The public weather forecast is read-only and needs no account. A trusted adapter handler must invoke policy checks synchronously **before** a side effect, then verify the response. Hermes hooks can provide an additional check but are not a fail-closed boundary if a callback fails or times out. Cron/watchers and event delivery likewise need running infrastructure; a scheduled intent in a skill is not a scheduler.

Keep source data and instructions separate. Web pages, mail, files and transcriptions cannot grant access or approval. Task ownership, a durable audit, retries and idempotency belong at the integration boundary. [Capabilities](CAPABILITIES.md) and [approvals](APPROVALS.md) specify the minimum gate; [dashboard events](DASHBOARD_EVENTS.md) specifies how to translate verified outcomes without inventing an AsyncAPI event.

The companion [rogue-friday](https://github.com/rogueki/rogue-friday) is the target application, not a submodule. Its checked contract is the pinned [AsyncAPI snapshot](https://github.com/rogueki/rogue-friday/blob/d2432d623ad6ea541467f322cbbbfbbc9ba2f542/packages/contracts/asyncapi/jarvis-events.yaml). Recheck its current contract before building a live adapter. This package does not modify the companion repository, installer or dashboard.

Official Hermes architecture references: [Skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), [hooks](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/hooks.md), [tool search](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/tool-search.md), [Kanban](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/kanban.md).
