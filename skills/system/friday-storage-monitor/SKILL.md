---
name: friday-storage-monitor
description: Review fresh storage measurements, WSL virtual disk growth, logs, model caches, backups and temporary files; use to identify capacity risk and prepare a cleanup plan.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, system, storage, capacity]
    related_skills: [friday-system-health, friday-service-recovery, friday-backup-manager]
    requires_tools: []
    config:
      - key: friday.storage.mode
        description: Storage inspection mode
        default: read_only
required_environment_variables: []
---

# Storage monitor

Inspect capacity from verified measurements and report safe options. This skill does not delete, compact or move files.

**Inputs:** filesystem/mount scope, free/total bytes and observation time, configured warning thresholds, WSL VHD measurements if available, categorized usage (logs, model cache, backups, temp), mode and retention policy.

**Capability and precondition:** require a verified read-only storage inventory capability (for example, a filesystem usage probe) that can report scoped paths, sizes and observation time. WSL VHD growth additionally requires a dedicated VHD measurement capability. If either capability is absent, mark that coverage `not_checked`; do not substitute estimates or directory names.

1. Confirm the path/mount and measurement freshness. Keep Windows and WSL paths distinct; do not assume `D:` and a mounted path refer to the same capacity.
2. Report measured usage and threshold status. If no threshold or VHD metric exists, state that instead of estimating a pass.
3. Identify large categories only from a scoped read-only inventory. Avoid reading file contents or traversing protected/user directories unnecessarily.
4. Propose cleanup candidates with exact paths, size evidence, owner/purpose, retention rule, reversibility and risk. Prioritize cache regeneration or aged logs only when policy documents retention.
5. For backup locations, check that proposed cleanup does not remove the only verified copy. Keep a dry-run list and require separate approval/tooling for deletion or relocation.

**Trend and candidate record:** Compare like-for-like measurements of the same volume or VHD with UTC timestamps, units and source; compute growth rate only when both readings are valid and say when the interval is too short to project exhaustion. Distinguish host free space from WSL guest free space and VHD physical size. For logs, model caches, backups and temporary data, record exact scoped path, measured bytes, owner, last access/modification evidence where available, policy retention and regeneration or restore path. An apparently old, duplicated or temporary file is not automatically safe to remove.

**Escalation:** Report current free bytes, percent, configured warning/critical boundary and estimated time to threshold only with sufficient samples. Flag unknown mount, stale sample, access denial and absent threshold as coverage gaps. Cleanup proposals remain read-only artifacts; no delete, VHD compaction, cache purge or backup pruning is provided by this skill.

**Modes:** `mock` uses fixture inventories; `read_only` measures and proposes; `live` may still only inspect. Any mutation is a separate approved operation outside this skill.

**Output:** timestamped capacity table, scope/coverage, warning threshold source, candidate cleanup plan and items excluded due to unknown retention. No cleanup action is claimed.

**Risk:** Observation Tier 0. Moving/deleting files can be irreversible; obtain the appropriate explicit approval and backup/recovery proof through a dedicated operation.

**Failure:** Missing permissions or stale measurements yields partial/unknown results. Never infer that temporary-looking files are disposable.

**Verification:** Ensure each size and path is from a current scoped measurement; cleanup remains a proposal; backup retention and rollback considerations are recorded.
