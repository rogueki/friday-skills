---
name: friday-tax-deadline-monitor-at
description: Track Austrian tax filing, response and appeal deadlines from dated official rules and case-specific notices.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, austria, tax]
---

# friday-tax-deadline-monitor-at

## Routing

Use for tax due dates and notice windows. Do not use for invoice due dates or final return quality review.

## Inputs and capability

Inputs: Tax type/year, filing channel, notice or Bescheid delivery dates, advisor status, jurisdiction and scheduler capability. Required capabilities: official-web.read for current BMF rules and document.read for case-specific notices; scheduler.run and notification.deliver are separate requirements for an ongoing watch. mock uses synthetic notices, read_only returns a one-time timeline, and live may schedule only through verified hooks. No filing adapter is presumed.

## Procedure

1. Classify each item separately: annual filing, authority request for information/evidence, payment, Bescheid, appeal or an already granted extension. Capture tax type/year, responsible person, channel and official notice ID. Never treat a generic filing date as the date for a specific notice.
2. Read the applicable official BMF procedure page, for example [Bescheidbeschwerde und Verfahren](https://www.bmf.gv.at/themen/steuern/fristen-verfahren/beschwerde-zahlungserleichterung-nachsicht.html), plus the actual notice and its Rechtsmittelbelehrung. Record URL, applicable rule year/version, retrieval UTC time, notice issue date, delivery/receipt evidence and any verified extension decision. An envelope date, message timestamp and legally effective delivery may differ; preserve each separately.
3. Identify the exact trigger specified by the notice or current official rule. Compute a candidate date only when trigger, period, applicable calendar/weekend/holiday convention and extension are all verified. Store local timezone and an unambiguous ISO date; show the calculation and source. If service date or rule conflicts, output `date: unknown`, high-priority verification task and no fabricated countdown.
4. De-duplicate by notice ID, tax year, deadline type and source revision. On changed notice or confirmed extension, supersede the old reminder with an audit reference rather than running two conflicting alerts. Recompute after relevant official rule or notice changes.
5. Return one-time timeline by default. Claim ongoing monitoring only after a real scheduler has acknowledged the job, a protected delivery target is confirmed, and a test delivery/health check is verified. A local list or dashboard mapping is not a scheduled reminder; do not include sensitive tax details in notifications.

## Approval and failures

No automated submission or appeal. A reminder is not legal proof of timely receipt.
Unknown service date or conflicting extensions means an unknown deadline and urgent verification, not a fabricated date. No automated response, appeal or filing follows a reminder. If a deadline may already be near or past, escalate to human review with source evidence rather than assuring timeliness.

## Output and verification

Return shared/schemas/result.schema.json fields: status, skill, mode, summary, artifacts, actions_taken, actions_proposed, approvals_required, warnings, errors, sources (URL and retrieval time for external claims), verification; optional task_id. Use partial for incomplete usable work and blocked for missing required capability. Never put a proposal in actions_taken. Positive check: date independently recomputed from the verified receipt trigger and notice/rule; scheduler acknowledgement exists if monitoring is claimed. Negative check: issue date substituted for unknown receipt, unverified extension, stale rule, duplicate notice or missing scheduler never yields a firm deadline or active-monitoring claim.

Only with a real Kanban task and trusted publisher, emit local friday.skill.* progress without sensitive data; do not claim dashboard delivery or post these events to the current Control API. Design basis: local implementation plan section 15.5 and docs/CONTRACTS.md.

## Manual routing cases

See tests/cases.json; examples are for manual review, not automated behavior proof.
