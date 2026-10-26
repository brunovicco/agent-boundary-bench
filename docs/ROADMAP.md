# Roadmap

## v0.1.0 acceptance

Implemented native local/HTTP/A2A paths, deterministic fixtures and oracle, sequential/concurrent three-role orchestration, open-arrival harness, traces, process metrics, raw schemas, reports and tests. Container configuration and CI are included; execution status is in VALIDATION.md. Full capacity/repetition campaigns must not be claimed unless their complete raw data exist.

## v0.2.0 — complete: tool access and context topology

Implemented with official MCP Python 2.3.0 and negotiated protocol 2026-07-28:

- Separate SDK direct-dispatch, stdio and Streamable HTTP tool-access arms.
- One deterministic `analyze_credit` tool and one versioned synthetic fixture resource template.
- Generalized three-role fan-out repetitions with explicit bounded concurrency and ordered fan-in.
- Independent context-copy, tool-call and uncached resource-read amplification controls.
- v2 raw schema/manifest fields, reports, factorized campaign definitions and real transport tests.
- Public MCP request metadata/server middleware for W3C correlation without SDK monkey patching.
- Explicit A2A-delegation versus MCP-tool-access interpretation boundary.

Recorded validation includes a 24-round smoke and 120-round five-repeat pilot, with 1,272
successful executions and zero errors, timeouts or drops. The full 1,620-round boundary matrix
and 1,440-round amplification matrix remain intentionally unexecuted until an isolated benchmark
host is available; campaign definitions are versioned and ready.

The public release includes bilingual documentation, cross-platform native validation,
functional Docker Compose verification and dedicated [release notes](RELEASE_0.2.0.md).

The optional `a2a-otel-kit` treatment is not silently enabled: doing so would change the existing A2A baseline. It remains suitable for a separately declared instrumentation campaign rather than a v0.2 kernel dependency.

## v0.3.0 — in development: failures, pressure and isolation

- Implemented in the first development milestone: deterministic application-layer fault
  injection, bounded retries, recovery, stable idempotent delegation IDs, bounded worker-local
  cache, per-worker admission/queue controls, schema v3 counters and campaign definitions.
- Next: sustained capacity sweeps and backpressure with an external isolated generator.
- Next: process/container resource interference, failure containment and remote network topologies.
- Next: advanced distributed telemetry, collector/exporter treatment matrices and lost-span accounting.

The implemented first milestone is documented in [RESILIENCE.md](RESILIENCE.md). Its native and
real-protocol tests validate behavior, not sustained capacity or infrastructure-failure
containment. v0.3.0 has not been released.
