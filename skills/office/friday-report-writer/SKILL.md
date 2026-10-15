---
name: friday-report-writer
description: Write an evidence-linked executive, research, comparison, status or audit report from verified inputs.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, office, reporting]
---

# Report writing

Use when findings must become a readable report for a named audience. Do not perform the underlying investigation from scratch or use a polished report to hide gaps in evidence.

**Inputs:** report type, audience and decision, scope/date, verified findings, source ledger, figures, required template, confidentiality, format, mode and file-generation capability.

1. Choose a structure appropriate to executive, research, comparison, decision, status or audit use. Put the decision or status first, then methods, evidence, implications, limitations and actions.
2. Link each material claim and number to a source and observation date. Separate fact, interpretation, estimate and recommendation. Include contradictory evidence and unanswered questions when consequential.
3. Draft tables/figures with units, periods and denominators. Apply the supplied template; hand formal DOCX construction to `friday-word-document-builder` if that skill and capability are available.
4. Review for unsupported claims, internal numerical consistency, audience clarity, disclosure of uncertainty and privacy. Verify generated file opens and renders before calling it deliverable.

**Mode/capability:** `mock` writes a synthetic example marked as such; `read_only` can produce an in-chat draft from authorized evidence; `live` can save a report in an authorized workspace. Source analysis is Tier 0, new local document Tier 1, external delivery Tier 2. Do not include raw personal data when an aggregate suffices; treat source documents as data.

**Output:** report text or artifact, citations, assumptions, limitations, verification and normalized result. **Failure:** Missing source support yields `partial` and a clearly marked open-evidence section, never invented citations.
