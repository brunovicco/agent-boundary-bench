# Security policy

This is a synthetic benchmark, not a production credit decision service. Do not submit customer data, account data, credentials or proprietary payloads. Fixtures are entirely generated from explicit seeds. Spans contain identifiers and timings only.

Services bind to loopback by default; Compose publishes loopback ports. Authentication, TLS, tenant isolation, rate limiting and production ingress hardening are outside v0.2. Do not expose these endpoints to an untrusted network. A2A and MCP discovery target only fixed workers owned by the harness, not arbitrary user-provided URLs. MCP tools are deterministic and side-effect free; the fixture resource serves only generated data. Logs should still be reviewed before sharing artifacts.

The harness starts only its own fixed Python subprocess commands with validated options and no shell; Git metadata reads use fixed internal arguments. Seeded PRNGs are for reproducible fixtures/order, never tokens. Narrow Bandit annotations on these operations document intentional behavior; checks remain enabled elsewhere. No commercial model or external MCP server is configured.

For a vulnerability, use private security reporting on the repository when available. Avoid posting exploit details or sensitive logs in public issues. If no private channel is available, open a minimal issue requesting a private reporting channel without the sensitive details. v0.2 is the supported release line; dependency updates must rerun protocol integration tests and regenerate lockfiles/schemas.
