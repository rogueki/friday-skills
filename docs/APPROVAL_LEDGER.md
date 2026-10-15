# One-time approval boundary

RogueKI F.R.I.D.A.Y. keeps Tier-2 GMX sends and CalDAV creates/updates behind a host-owned `ApprovalLedger`. The Hermes GMX and CalDAV plugins expose read tools only.

## Host contract

1. The trusted host authenticates the operator, displays the exact action, target and content, records the operator's decision in its own audit system, and checks account permission. This package does **not** authenticate the operator or prove that `decision_id` is genuine.
2. The host creates one grant with `ApprovalLedger.issue(action=..., target=..., payload=..., idempotency_key=..., expires_at=..., decision_id=...)`. Keep the ledger object, grant ID, provider credentials and write transport outside model-facing tool arguments and untrusted process input. Do not expose `issue` as an agent tool.
3. The host calls `send_message` or `write_event` with the same ledger object and grant ID. The adapter checks a fresh authenticated write capability, then consumes the exact grant atomically before its own durable operation reservation and the single external mutation attempt.
4. A missing, expired, mismatched or used grant fails closed. After consumption, a journal failure also fails closed; the host must reconcile the approval and operation journals before issuing a new grant. A timeout or uncertain provider outcome is never blindly retried.

The grant binds action, target, canonical payload fingerprint, idempotency key, Tier 2 and expiry. One `decision_id` can issue only one grant in this ledger. The SQLite file stores only hashes, the action/tier and timestamps. It does not store payload text, target, key, credentials or the raw grant ID. The file path must be absolute and use an existing non-symlink directory; preexisting files must be regular, single-linked and private on POSIX. Protect the directory and file with OS permissions or ACLs. The host must prevent untrusted code from replacing the ledger path; this Python class is not a security boundary against another process with filesystem access. Keep backups and the host audit trail because lost ledger state cannot safely authorize a replay.

The grant consumption and provider mutation cannot share a transaction. A crash after consumption may leave no provider attempt, and a crash during a provider attempt may leave an unknown outcome. Both states require reconciliation rather than automatic resend. Grant issuance is deliberately a trusted-host API, not evidence of an operator decision by itself.

## Offline verification

`python -m unittest discover -s tests -p 'test_approval_ledger.py' -v` checks exact binding, expiration, replay after restart, concurrent consumption, invalid storage and unavailable database behavior. Adapter tests use injected transports and never contact GMX or a calendar provider.
