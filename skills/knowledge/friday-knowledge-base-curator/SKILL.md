---
name: friday-knowledge-base-curator
description: Curate an authorized knowledge base by linking sources, flagging duplicates and stale entries, and scheduling review.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, knowledge, curation]
---

# Knowledge base curation

Use when a collection of notes or articles needs structure, provenance and maintenance. Do not treat retrieval rank as truth or merge entries solely because titles resemble one another.

**Inputs:** authorized knowledge corpus and scope, taxonomy, canonical owners, source links, last-review timestamps, retention/sensitivity rules, mode and index/write capabilities.

1. Inventory entries and their source, owner, version and last review date. Group by topic and audience; identify broken links, unreferenced assertions and genuinely duplicate content with hash and semantic comparison.
2. Propose a canonical structure and cross-links. For each merge or rewrite, show what information would be kept, changed or lost. Preserve dissenting historical decisions as dated records rather than erasing them.
3. Flag stale entries using source recency and domain-specific volatility, then route material claims to `friday-source-verification` where needed. Set review dates and ownership for high-change topics.
4. Apply only authorized reversible local changes through a confirmed capability, keeping original versions or a diff. Rebuild/search the index if available and test a few representative queries for discoverability.

**Mode/capability:** `mock` curates synthetic notes; `read_only` returns an audit and edit proposal; `live` can write new linked entries in an authorized workspace. Review is Tier 0, reversible writes Tier 1, destructive merges/removals require a specific Tier 2/3 gate. Do not ingest unrelated private documents or leak source text to external search services.

**Output:** taxonomy, duplicate/staleness report, source-linked edits, review dates and normalized result. **Verification/failure:** Check links, revision history and sample search results; if index capability is absent, mark retrieval QA NOT_RUN and status `partial`.
