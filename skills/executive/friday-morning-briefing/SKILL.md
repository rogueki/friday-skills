---
name: friday-morning-briefing
description: Prepare a bounded morning executive briefing from current agenda, messages, tasks, deadlines and alerts; not a weather-only answer.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, executive, morning-briefing]
---

# Morning briefing

Do not use for a weather-only answer.

Use for an on-demand or scheduled morning overview. Do not route a single weather or calendar question here. Inputs: date and timezone, owner preferences, source capability health, trusted agenda/task/approval records, mail priority summaries, weather observation, deadline records and system alerts.

1. Resolve today's interval in the user's timezone. Require fresh read capabilities for each connected source; in `mock` use labelled synthetic records, in `read_only` or `live` read actual records only from healthy adapters. A missing source produces an explicit gap, never an empty-success claim.
2. Deduplicate related events, preserve source IDs and timestamps, then rank by urgency, impact and actionability. Show at most three critical and five important items; put the rest under “Weitere”. Distinguish known deadlines from inferred urgency.
3. Produce an executive summary, linked detail items, dashboard card data and a short voice version that omits sensitive detail in privacy mode. A schedule or hook must invoke this skill for proactive delivery; the skill itself does not run a watcher.
4. Delivering through an external channel requires its real adapter, `live` mode and an action-bound tier-2 approval. Without those, return the briefing as a draft or `waiting_approval`, with no claim of delivery.

## Output and verification

Return `shared/schemas/result.schema.json`: `artifacts` contains the briefing and source references; `actions_taken` lists only actual reads/local drafts; `actions_proposed` holds delivery; `sources` uses URL plus retrieval UTC time only for web-derived facts. Record gaps in `warnings`. Use `blocked` when no trustworthy sources remain, `partial` when material feeds are missing. Verify date range, item IDs, ranking cap and source freshness before `completed`. Long-running assembly uses a Hermes task with progress and terminal state; local skill lifecycle records are not publishable dashboard events.
