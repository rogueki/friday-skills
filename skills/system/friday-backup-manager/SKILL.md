---
name: friday-backup-manager
description: Plan and verify policy-compliant backups and restore drills for F.R.I.D.A.Y. configuration and data; use when backup coverage, integrity, encryption or restore evidence is needed.
version: 0.1.0
author: RogueKI
license: MIT
metadata:
  hermes:
    tags: [friday, system, backup, restore]
    related_skills: [friday-storage-monitor, friday-service-recovery, friday-privacy-and-data-governance]
    requires_tools: []
    config:
      - key: friday.backup.mode
        description: Backup and restore mode
        default: read_only
required_environment_variables: []
---

# Backup manager

Use this procedure to define backup scope, inspect evidence and plan a restore test. A skill does not provide a backup client or guarantee that configured jobs ran.

**Inputs:** asset inventory and data classification, retention policy, approved destinations, encryption/key custody status (never key material), mode, backup logs/manifests/checksums, and restore-test environment.

1. Define in-scope assets explicitly: skills, Hermes configuration, task data if supported, dashboard configuration, encrypted voice profiles, adapter configuration with secrets excluded, and documents only where policy permits. Record excluded and unknown assets.
2. Check the backup capability and destination before any operation. `mock` uses fixtures; `read_only` reviews existing manifests/logs; `live` requires an approved backup adapter, destination policy and explicit approval for the concrete scope.
3. Ensure secrets are excluded or handled by the approved secret store; never copy plaintext credentials into an archive or report. Sensitive voice profiles require encryption and access-policy evidence; do not claim their protection from a filename or setting alone.
4. For each backup record source scope, completion time, destination, encryption/integrity evidence, retention and errors. A successful process exit alone is not proof of recoverability.
5. Before calling a backup successful, require a restore drill to an isolated non-production target: restore selected representative items, verify checksums/schema/readability and document cleanup/rollback. A backup with no restore evidence is `backup_created_restore_unverified`.
6. Never overwrite production during a restore drill. A production restore is a distinct high-impact operation requiring Tier 3 approval, verified target, recovery plan and second factor.

**Coverage evidence:** Build one row per asset class: source and owner, policy/RPO/RTO if defined, latest completed backup ID and UTC time, destination and failure domain, encryption-at-rest and in-transit evidence, retention, integrity manifest, and latest restore-drill ID. Include Skills, Hermes config, Kanban/task data, Dashboard config, encrypted voice profile, sanitized adapter config and policy-included documents. A configured schedule, encrypted filename or successful job exit alone never proves an asset recoverable. Record key custody reference and access test outcome, never key material.

**Restore drill:** Use an isolated target with capacity and access controls; pin a backup ID and expected manifest, restore representative files/configuration and test readability/schema and checksum or another strong integrity check. Record restore start/end, operator, missing objects, errors and cleanup. If the drill cannot be performed, label coverage `backup_created_restore_unverified`; if it fails, label it `failed` and preserve the prior backup. Do not replace the only good copy or assert RPO/RTO compliance from a single sample.

**Output:** asset coverage matrix, backup evidence, restore-test evidence, missing controls, retention issues and status (`verified`, `restore_unverified`, `partial`, `blocked`, `failed`).

**Risk and approval:** Inspection Tier 0. Backup creation Tier 1/2 by policy. Restore that can overwrite or expose data is Tier 3 with hard approval and second factor.

**Failure:** Missing manifest, integrity check, encryption proof or restore test prevents “backup successful.” Keep failures visible; do not silently retry into a new destination.

**Verification:** Independently inspect restore output and compare representative content/integrity evidence. Separate backup-job completion from demonstrated restore success.
