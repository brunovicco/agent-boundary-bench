# Roadmap

## v0.1.0 acceptance

Implemented native local/HTTP/A2A paths, deterministic fixtures and oracle, sequential/concurrent three-role orchestration, open-arrival harness, traces, process metrics, raw schemas, reports and tests. Container configuration and CI are included; execution status is in VALIDATION.md. Full capacity/repetition campaigns must not be claimed unless their complete raw data exist. Remote repository creation remains an environment capability, not a simulated success.

## v0.2.0 — tool access and context topology

- Recheck stable MCP v2 and its transport/client dependencies against the recorded compatibility study.
- Implement MCP in-process SDK client/server, stdio and Streamable HTTP as separate tool-access arms.
- Generalize fan-out/fan-in beyond the initial fixed three roles, with bounded concurrency.
- Measure context/payload amplification and repeated tools/resources access.
- Preserve distinct A2A delegation versus MCP tool-access questions; do not rank them as substitutes.
- Add optional a2a-otel-kit integration behind an adapter, after measuring its instrumentation impact.

## v0.3.0 — failures, pressure and isolation

- Controlled fault injection, bounded retries, recovery and idempotent delegation IDs.
- Sustained capacity sweeps and backpressure with an external isolated generator.
- Process/container resource interference, failure containment and remote network topologies.
- Advanced distributed telemetry, collector/exporter treatment matrices and lost-span accounting.

No v0.2/v0.3 MCP/fault infrastructure is included speculatively in v0.1. Existing deadline tests validate current behavior; they do not constitute the future fault-injection campaign.
