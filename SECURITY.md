# Security policy

This is a synthetic benchmark, not a production credit decision service. Do not submit customer data, account data, credentials or proprietary payloads. Fixtures are entirely generated from explicit seeds. Spans contain identifiers and timings only.

Services bind to loopback by default; Compose publishes loopback ports. Authentication, TLS, tenant isolation, rate limiting and production ingress hardening are outside v0.1. Do not expose these endpoints to an untrusted network. A2A discovery is directed only at the worker started by the harness, not arbitrary user-provided URLs. Logs should still be reviewed before sharing artifacts.

The harness starts only its own fixed Python subprocess command with validated options and no shell; Git metadata reads use fixed internal arguments. Seeded PRNGs are for reproducible fixtures/order, never tokens. Narrow Bandit annotations on these operations document intentional behavior; checks remain enabled elsewhere. No live MCP server or commercial model is configured.

For a vulnerability, use private security reporting on the repository when available. Avoid posting exploit details or sensitive logs in public issues. If no private channel is available, open a minimal issue requesting a private reporting channel without the sensitive details. v0.1 is the supported release line; dependency updates must rerun protocol conformance and regenerate lockfiles.
