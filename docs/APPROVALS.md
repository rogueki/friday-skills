# Approval and action policy

Risk tiers follow the local `shared/policy.py` contract:

| Tier | Representative action | Gate |
|---:|---|---|
| 0 | Observe, analyze, search | Fresh read capability and source/verification evidence. |
| 1 | Draft, reversible write in an authorized local workspace | Workspace and mode check; preserve originals. |
| 2 | External message, calendar edit, single physical/home action | Exact action-specific approval, live write capability and idempotency key. |
| 3 | Payment, purchase/booking, contract, tax submission, credential or mass/security-critical action | Tier 2 checks plus hard approval and verified second factor. |

Unknown action names default to Tier 3 in `risk_tier`. Tier 1 is not permission to mutate arbitrary paths. `mock` works with synthetic data; a `read_only` run cannot claim an external write. The Python helper is a **reference gate only**; a trusted gateway must call it before the real tool and must separately enforce identity, scope, replay protection and audit persistence.

For an approved action, bind `action`, exact `target` and payload hash (`action_fingerprint`) to one approval with `status: approved`, tier and UTC expiry. Re-evaluate it immediately before execution. A changed recipient, amount, bank detail, document or target invalidates the approval. Require an idempotency key for Tier 2/3 retries; distinguish transport timeout from completed side effect before retrying. A denied or missing approval returns `waiting_approval` or `blocked`, with the proposed action separate from `actions_taken`.

The plan treats mail send and phone calls as Tier 2; payment execution, tax filing and booking as Tier 3. Home controls require Tier 2 or higher according to impact. These are integration requirements, not a promise that those live operations are available. `skills.write_approval` in Hermes governs edits to skill text and does not replace action approval. See [contracts](CONTRACTS.md) and [security](SECURITY.md).

The GMX and CalDAV Python write functions now require a host-owned [one-time approval ledger](APPROVAL_LEDGER.md). They do not accept a caller-supplied approval mapping. Grant issuance, operator authentication, capability provenance and OS protection of the ledger remain host integration responsibilities; no Hermes write tool is registered for these actions.
