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

**Inputs:** record class, jurisdiction, creation/closure dates, owner, applicable policy, current official legal sources, contractual obligations, litigation/audit holds, copies/backups, mode and file capabilities.

1. Identify each record type and the event that starts its retention clock. Research current official rules for the relevant jurisdiction and date; cite statute/regulator or approved policy version. If classification or jurisdiction is uncertain, request specialist review.
2. Check legal hold, tax/audit, contractual and privacy obligations before calculating earliest review/disposal date. Separate minimum legal retention from operational value and maximum privacy retention.
3. Produce a decision per item: retain, archive, review, or propose deletion, with evidence, owner and next review date. Check exact duplicate claims against hashes and metadata. Explain backup and derived-copy implications.
4. For an approved action, verify target list and scope immediately before execution, preserve an audit trail and confirm outcome from a trusted adapter. Prefer reversible archive where suitable; never silently purge backups or override a hold.

**Mode/capability:** `mock` evaluates synthetic records; `read_only` calculates proposed handling; `live` may write a local schedule, while a single deletion requires Tier 2 action-bound approval and mass/permanent deletion Tier 3 with hard approval and second factor. A skill alone cannot enforce these gates: require the actual capability and trusted approval record. Do not disclose sensitive contents beyond necessary metadata.

**Output:** itemized retention schedule, citations/as-of dates, holds, proposed actions and normalized result. **Verification/failure:** Recheck current sources and hold status; missing policy, law or owner blocks deletion and yields `partial` review status.
