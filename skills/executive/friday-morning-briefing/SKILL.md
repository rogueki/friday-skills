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

## Selection and presentation contract

- Snapshot each requested feed with `source_id`, record ID, event time, retrieval time and capability check time. Apply the host capability freshness rule (`shared/policy.py`, currently 300 seconds) to the capability; assess each record's own validity separately. A fresh capability cannot make an old weather forecast or stale task state current. Unavailable weather, mail, approvals, tasks, calendar, alerts, agents or private reminders are named as **unknown coverage**, never “nothing due”. Do not invent a connected feed from the plan: dashboard cards and running-agent status are output concepts until a host supplies verified sources and delivery.
- Merge duplicates by stable event/deadline ID, retaining all supporting IDs. Classify critical only for verified immediate deadline, high-impact failure or explicit owner rule; important for a dated action or meaningful preparation. Within each class sort by earliest actionable deadline, documented impact, then stable source ID. Ties use source ID so repeated runs on one snapshot are stable. Show at most 3 critical and 5 important; count and link overflow under `Weitere` without silently dropping it. Do not fill empty critical slots with unverified urgency.
- Output fields: `as_of` with timezone, three-line executive summary, `critical[]`, `important[]`, `weitere_count` and references, `coverage[]` with freshness/gaps, `detail_refs[]`, `voice_short`, and `dashboard_cards_proposed[]`. Each item has title, required action, due time or `unknown`, evidence IDs and confidence qualifier. Dashboard cards are structured draft data; no publish claim. The voice version excludes addresses, account numbers and sensitive family details when privacy mode is on.
- On-demand requests assemble once. A scheduled briefing requires an installed trigger and observed invocation; a declared but disabled automation is not a successful schedule. In quiet hours or absent delivery preference, keep the draft locally and report delivery as pending.

Example: a verified 09:00 meeting and 11:00 invoice deadline appear with their IDs and times; an offline inbox appears as `mail: unknown coverage`, not `0 important emails`.

## Output and verification

Return `shared/schemas/result.schema.json`: `artifacts` contains the briefing and source references; `actions_taken` lists only actual reads/local drafts; `actions_proposed` holds delivery; `sources` uses URL plus retrieval UTC time only for web-derived facts. Record gaps in `warnings`. Use `blocked` when no trustworthy sources remain, `partial` when material feeds are missing. Verify date range, item IDs, ranking cap and source freshness before `completed`. Long-running assembly uses a Hermes task with progress and terminal state; local skill lifecycle records are not publishable dashboard events.

Positive check: every displayed item resolves to a source record, caps hold, and an offline nonessential feed yields `partial` with an explicit gap. Negative check: reject stale capabilities, inferred deadlines presented as facts, overflow without references, and any claim of sent voice/card/push without a delivery receipt. A web weather fact uses a URL and UTC retrieval time in `sources`; internal record IDs belong in the artifact, not fake URLs.
