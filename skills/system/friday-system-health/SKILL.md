---
name: friday-system-health
description: Assess reported F.R.I.D.A.Y. stack and host health from fresh measurements; use for Hermes, Control API, models, voice, WSL, resources, storage, adapters or event-stream status.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, system, health, observability]
    related_skills: [friday-service-recovery, friday-storage-monitor, friday-capability-and-health-check]
    requires_tools: []
    config:
      - key: friday.system-health.mode
        description: Health inspection mode
        default: read_only
required_environment_variables: []
---

# System health

This is an evidence-led assessment procedure, not a monitoring agent. It needs real read-only probes or caller-provided measurements. No probe or adapter is implied by this skill.

**Inputs:** requested components, current UTC/local timestamp, mode, component inventory, capability results, probe outputs and thresholds from trusted configuration.

Check only in-scope components available through verified read-only capabilities: Hermes runtime, Control API, Kimi route, local Qwen, voice services, WSL, CPU/RAM/GPU/VRAM, D: storage, adapters and event stream. For each probe record source, observation time, value/status, threshold and probe error.

1. Check probe reachability and freshness before interpreting a result. Do not infer health from configuration, a prior session or a successful unrelated component.
2. Classify each component `healthy`, `degraded`, `unavailable`, `stale`, or `not_checked`; summarize only evidence-backed findings. Keep partial coverage explicit.
3. Compare measured resource values with configured thresholds. If thresholds are missing, report measurements without inventing a pass/fail boundary.
4. Separate symptoms from cause. Provide bounded next diagnostic steps; delegate repair to `friday-service-recovery` only when an actual recovery action is requested and policy allows it.

**Probe contract:** Identify each component by stable service/host or device ID and environment. Capture probe name, trusted adapter ID, observed-at time with timezone, response/error, configured freshness window and threshold source. `checked_at` from a cached configuration is not a live observation. Never merge a Kimi/Qwen route test with Hermes process health or a Control API HTTP check with event-stream delivery. CPU, RAM, GPU/VRAM and `D:` need units, denominator and measured interval; WSL needs its own host/guest scope. A missing component has `not_checked` coverage even if neighboring probes pass.

**Overall decision:** `healthy` requires every explicitly required component to have a fresh passing probe and, for resource limits, a trusted threshold. A known failed required probe makes the result `degraded` or `blocked` according to impact. Stale, conflicting or unavailable evidence makes the affected row `unknown` and prevents an overall healthy claim. Link any claimed recovery to new ordered post-checks on the same component; the E2E10 fixture verifies only synthetic mail readiness and takes no service action.

**Modes:** `mock` uses labeled fixtures; `read_only` runs or reports read-only probes; `live` has no additional authority and must not change services.

**Output:** timestamped component matrix, probe coverage, evidence/source, threshold, errors, overall status (`healthy`, `degraded`, `blocked`, `unknown`) and proposed next checks. Dashboard updates are only claims if a real event adapter confirms delivery; otherwise use local result records.

**Risk:** Tier 0 observation. This skill performs no remediation. Any restart/configuration change is a separate action requiring the recovery skill and applicable approval.

**Failure:** Missing, timed-out, stale or contradictory probe becomes `unknown`/`stale`; never report overall healthy when a required component was not checked.

**Verification:** Every health conclusion cites a fresh observation and probe; component coverage and skipped checks are visible; no write action occurred.
