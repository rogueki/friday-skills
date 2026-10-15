# Hermes web research plugin

`plugins/friday_web_research` exposes one read-only Hermes tool,
`friday_web_extract`, backed by `adapters.web_extraction.extract_one`.

## Fail-closed registration

The standalone Hermes entry point `register(ctx)` registers the tool with no
network capability. Calls return `host_capability_unavailable`. Environment
variables and tool parameters cannot configure transport or hosts.

An embedding host that already owns an authorized egress boundary can instead
call `register_with_host(ctx, transport=..., allowed_hosts=...,
authorize_egress=...)`. These values are captured by that handler instance and
are not exposed in the model schema. The authorizer receives the exact URL and
the adapter's fixed time and byte limits immediately before the transport is
called. A denial or exception blocks the request.

The host transport and egress layer remain the security boundary. They must
enforce public DNS/IP pinning, the approved host and redirect policy, request
and ingress-byte limits. The adapter also checks HTTPS, exact allowed hosts,
redirects, login paths, response size, content type and challenge pages. Do not
pass browser stealth or CAPTCHA-solving transports to this tool. The provided
Scrapling transports need their own trusted host authorization and network
boundary; this plugin does not create one.

Successful output preserves the adapter result, including UTC retrieval time,
source/final URL, method provenance and `untrusted-page-data` marking. Page
content is evidence data and must never be followed as instructions. Failures
return bounded generic errors without transport exception details. All results
declare `write_effect: false`.

The plugin tests use fake transports only. They do not establish DNS pinning,
real egress authorization, or compatibility with a particular host integration.
