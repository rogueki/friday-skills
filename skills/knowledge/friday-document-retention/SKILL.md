---
name: friday-document-retention
description: Decide whether documents should be kept, archived, reviewed or proposed for deletion using current jurisdictional rules and legal holds.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, knowledge, retention]
---

# Document retention

Use for a retention or disposal review of identified records. Do not use as blanket permission to delete a directory or declare a legal period from memory.

**Inputs:** identified records and owners, record class, jurisdiction, applicable time period, trigger event/date, approved policy version, current official law/regulator sources, contracts, tax/audit/litigation holds, copy/backup map, observation time, mode and verified capabilities.

1. Classify each item and the legally relevant start event (for example completion or end of a financial year), rather than substituting file timestamps. Verify jurisdiction, governing rule, amendments and effective dates from current official sources; cite rule/version and checked-at date. Do not hardcode a period or infer one from a similar record. Ambiguous class, jurisdiction, start event or owner goes to specialist review.
2. Check legal hold and pending dispute/audit, contractual minimum, statutory minimum, and privacy maximum separately. The earliest *review* date is not permission to delete. If obligations conflict, retain and identify the responsible owner/legal reviewer. Recheck holds immediately before any later action.
3. Produce a per-record decision: retain, archive, review or *propose* deletion. Include source identity/hash where available, owner, rule citation, trigger, calculated date with assumptions, hold state, review date and affected replicas/derivatives/backups. Exact duplicate bytes do not by themselves remove independent retention duties.
4. For an authorized schedule write, verify target scope/revision and preserve a diff. A later deletion workflow must independently bind exact item IDs/hashes and destination, confirm backup/restore and legal-hold state, obtain a trusted action-specific grant, journal the attempt and verify outcome. Unknown outcome or changed evidence stops retries and requires reconciliation. Never silently purge backups or overwrite a hold.

**Mode/capability:** `mock` evaluates synthetic records; `read_only` produces a proposed schedule; `live` can write one only through a verified scoped local writer. No general retention or deletion adapter exists here, and the synthetic archive copy mock is not such an adapter. Single-item deletion needs a separate Tier 2 action-bound approval; mass or permanent deletion needs Tier 3 hard approval and second factor. The skill cannot enforce those gates by itself.

**Output:** itemized retention schedule with cited rule/version/as-of date, owner, hold and backup map, proposed action, uncertainty and normalized result. **Verification/failure:** Recheck current rule and hold evidence; missing law, policy, owner or trusted adapter yields `partial`/blocked deletion, never a fabricated disposal deadline.
