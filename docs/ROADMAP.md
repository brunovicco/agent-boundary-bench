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

## v0.3.0 — failures, pressure and isolation

- Controlled fault injection, bounded retries, recovery and idempotent delegation IDs.
- Sustained capacity sweeps and backpressure with an external isolated generator.
- Process/container resource interference, failure containment and remote network topologies.
- Advanced distributed telemetry, collector/exporter treatment matrices and lost-span accounting.

v0.3 fault/pressure/isolation infrastructure is not included speculatively. Existing deadline and post-timeout recovery tests validate current behavior; they do not constitute a controlled fault-injection campaign.
