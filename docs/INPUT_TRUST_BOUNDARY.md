# Input trust boundary

Author: RogueKI. Scope: host-owned F.R.I.D.A.Y. handlers creating **local mock
proposals**. This is a narrow enforcement helper, not a Hermes-wide prompt
injection filter.

## Contract

1. A trusted reader extracts a complete source and calls `capture_source` before
   passing its text to a model. It supplies source type, canonical identifier,
   retrieval time and extraction method. The helper records a UTF-8 SHA-256
   digest. Email, web, PDF, Office, chat, attachments, tool results and imported
   skills remain `untrusted` even when their contents look like instructions.
2. The authenticating host records an operator request with
   `bind_host_request`. It binds exact action, target, JSON-compatible payload,
   source ID and source digest. The host must authenticate the operator and keep
   both Python objects out of model-controlled tool parameters. A request ID
   printed in a document or supplied in a tool argument is not authentication.
3. The host calls `create_bound_mock_proposal` with the original content and
   proposed action. It checks provenance, content digest and exact intent before
   `MockRuntime.propose` appends an in-memory record. Errors raise
   `InputTrustError` and create no proposal. A source may provide facts for a
   host-authorized draft; source instructions cannot expand the bound action.

```python
source = capture_source(
    source_id="mail:42", source_type="email",
    canonical_identifier="message-id:42@example.test",
    retrieved_at=retrieved_at, extraction_method="body.peek", content=body,
)
request = bind_host_request(
    request_id=host_request_id, operator_id=authenticated_operator_id,
    action="draft", target="local:brief", payload=draft, source=source,
)
proposal = create_bound_mock_proposal(
    runtime=runtime, request=request, source=source, content=body,
    action="draft", target="local:brief", payload=draft,
)
```

The caller supplies `retrieved_at`, `body`, `draft`, `runtime` and authenticated
host identifiers. The helper does not fetch sources, detect every injection,
authenticate a user, validate a provider receipt or enforce capabilities,
approval and idempotency for live actions. A digest detects a changed text value
within this call path; it is not a signature or proof that the reader captured
all hidden content. The existing Hermes `pre_tool_call` hook can fail open and
must not be used as the enforcement point. No arbitrary Hermes tool or other
plugin is gated by this helper.

Quoted attack language can be analyzed as data. The negative test uses a source
that asks for exfiltration and verifies that its suggested `send_message`
action cannot replace a host-bound `analyze` request. Both cases have no
external effects.
