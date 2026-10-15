---
name: friday-decision-brief
description: Turn verified options into a concise decision brief with criteria, cost, risk, uncertainty and a recommended next step.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, research, decisions]
---

# Decision brief

Use when a decision maker needs a short comparison and recommendation from existing evidence. Do not use as a substitute for missing research or to execute the chosen option.

**Inputs:** decision owner, deadline, options including status quo, criteria and weights if given, cost horizon/currency, evidence ledger, constraints, operating mode and document capability.

1. State the decision and why now. List viable options on the same basis, including the cost and risk of no action. Identify hard constraints before scoring preferences.
2. For each criterion, record observed fact, source/date, assumption, uncertainty and consequence. Keep monetary ranges, one-time versus recurring cost, reversibility and dependencies explicit; do not manufacture numeric precision.
3. Compare options using the owner's stated priorities. Test whether reasonable changes in uncertain inputs reverse the ranking. Explain trade-offs and a recommendation only if evidence supports it.
4. Specify the next reversible step, approval or missing evidence required. Distinguish a recommendation from an authorized action or contract commitment.

**Mode/capability:** `mock` uses synthetic options; `read_only` writes an in-chat brief; `live` may save a local brief in an authorized workspace. Analysis is Tier 0, local draft Tier 1; purchase, booking, payment or contract remains Tier 3 with separate approval and capability. Avoid exposing confidential negotiations or private quotes.

**Output:** decision, options, criteria, facts, assumptions, risks, costs, recommendation, uncertainty, next step, sources and normalized result. **Verification/failure:** Check all material figures against the source ledger and sensitivity assumptions; if evidence is missing, mark `partial` and present contingent recommendations.
