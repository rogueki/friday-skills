---
name: friday-cost-and-model-router
description: Recommend a model route from task complexity, risk, context, latency, cost and tool needs; use when selecting among configured local Qwen and Kimi quality tiers.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, system, models, cost]
    related_skills: [friday-intent-and-skill-router, friday-capability-and-health-check]
    requires_tools: []
    config:
      - key: friday.model-router.mode
        description: Model route recommendation mode
        default: read_only
required_environment_variables: []
---

# Cost and model router

Recommend a route only from current configured-model capability data. Names such as local Qwen, Kimi Low, Kimi High and Kimi Max are plan labels, not proof that those endpoints or tiers are available.

**Inputs:** task requirements and risk, context size/sensitivity, quality needs, latency/cost constraints, tool requirements, current model inventory/capabilities, route prices or budgets if supplied, mode and approval state.

1. Identify minimum quality, tool and context requirements; identify whether content can be sent to a remote model under the applicable privacy policy.
2. Check freshness and source for model availability, context capacity, tool support, latency and price. Unknown data stays unknown; do not invent cost, speed or performance rankings.
3. Exclude models that fail privacy, capability, quality or budget constraints. For high-impact, legal, financial or safety-sensitive reasoning, require the configured higher-assurance route or human review; do not route around a specialist approval gate.
4. Recommend the least costly eligible route only when prices/budget and eligibility evidence are available. Otherwise recommend by stated capability, with cost marked unknown. Explain tradeoffs and fallback route.
5. In `mock`, use labeled fixture data; in `read_only`, return recommendation only; `live` may select a route only if a real router capability confirms the exact model and accepted request. A recommendation alone is not a model call.
6. Record actual route/result only from runtime telemetry. Never claim a worker, model, or provider was used based on the recommendation.

**Decision record:** For Local Qwen and each configured Kimi Low/High/Max route, record provider/model identifier, configuration revision, health observation time, usable context budget, required tool support, data residency, latency evidence and marginal price with currency/unit and effective date. Estimate tokens and total cost as a range when inputs justify it; reserve budget for tools and retries. Missing pricing or telemetry remains `unknown`, not zero. Apply privacy, context, tool, quality and hard budget gates before ranking eligible routes. If none qualifies, stop or ask for a policy-compliant human choice; do not silently send local data to a remote tier.

**Observed execution:** Return `recommended_route` separately from `accepted_route` and `observed_route`. Only a trusted router acknowledgement and runtime trace for the same request ID can establish the latter; record actual tokens/cost only if metered. A fallback is a new explicit routing decision after fresh eligibility checks. The 404 declared routing examples in this package are not model-decision evidence, and no current live route adapter is implied here.

**Output:** recommended route, eligible/excluded candidates and reasons, evidence timestamps, known/unknown cost and latency, privacy classification, fallback, and status (`recommended`, `no_eligible_route`, `unknown`).

**Risk and approval:** Route recommendation is Tier 0. Sending sensitive data to an external model must comply with data policy and any required approval. Tier 3 decisions retain separate hard approval and second factor.

**Failure:** If inventory is missing/stale or no candidate meets constraints, return `unknown`/`no_eligible_route` and request updated capability data or human routing. Never silently downgrade quality or privacy.

**Verification:** Confirm recommendation satisfies every hard constraint, uses dated evidence, respects budget/privacy and separates suggested route from observed execution.
