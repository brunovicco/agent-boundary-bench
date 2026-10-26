# ADR 0007: Controlled resilience treatments stay outside the domain kernel

Status: accepted for v0.3 development. Date: 2026-10-25.

Context: retry and fault experiments can easily change the business operation, hide duplicate
work or apply different semantics to local and remote paths. Random faults also make matched
rounds difficult to reproduce. MCP tool access and A2A delegation have different
responsibilities, so one generic "agent protocol resilience" result would be misleading.

Decision: retain the v1 deterministic credit kernel and place worker-local fault injection,
admission and idempotency in the application layer. Reuse one bounded delegation ID across
client attempts. Carry that ID directly for A0, in HTTP headers for A1 and in the public A2A
Message metadata field for A2. Select injected delegations with a stable SHA-256 rule, never
runtime randomness. Retry only classified transient failures, with explicit attempt count,
per-attempt timeout and backoff. Record attempts, retries, kernel executions, cache hits,
injected failures, rejections and admission wait independently. Do not apply these controls to
the MCP family in this milestone.

Consequences: matched A0/A1/A2 treatments keep the same business task and oracle while exposing
duplicate execution and recovery cost. The no-treatment path avoids additional metadata and
controller work, preserving the prior baseline. The cache is bounded, TTL-limited and
worker-local; it cannot support a durable or cross-worker idempotency claim. Application-layer
faults are repeatable but do not represent every infrastructure failure. Resource/process and
network fault treatments require separate milestones and labels.
