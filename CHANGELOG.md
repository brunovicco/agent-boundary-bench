# Changelog

## Unreleased — 0.3.0.dev0

- Added deterministic `fail-first`, `delay-first` and `after-commit` delegation treatments.
- Added bounded transient retries with explicit per-attempt timeout and fixed backoff.
- Added stable delegation IDs across attempts and bounded worker-local idempotency cache controls.
- Added service concurrency, bounded queue, admission timeout and overload rejection controls.
- Added raw schema v3 counters for attempts, retries, kernel executions, cache hits, injected failures, rejections and admission wait.
- Added real local, HTTP and official A2A recovery/idempotency integration tests.
- Added resilience/backpressure smoke and five-repeat full campaign definitions.
- Separated timeout treatments from the general resilience matrix to avoid classifying ordinary
  transport jitter as an injected timeout.
- Kept MCP v2 tool access separate from the delegation-resilience experiment family.
- Added a container resource-isolation topology with independently configurable harness and
  specialist CPU/memory limits.
- Added deterministic fixed-iteration CPU work and fixed touched memory allocations without
  conflating either with synthetic async waits.
- Added schema v4 cgroup v2 CPU quota/usage/throttling, memory limit/peak/event observations and
  explicit resource-sampling failure accounting.
- Added resource-isolation smoke/full matrices, integrity-checked reporting and ADR 0008.
- Made control-plane sampling loss explicit and bounded so CPU starvation remains observable
  without fabricating missing resource samples.
- Propagated and validated explicit host commit/dirty provenance for container campaigns whose
  images intentionally exclude the `.git` directory.

Cross-host network faults, sustained isolated capacity evidence and advanced collector/exporter
loss accounting remain in development. No resource-isolation benchmark result is claimed until
the container campaigns are executed and their raw evidence is reviewed.

## 0.2.0 — 2026-10-25

- First public release of the reproducible Agent Boundary Bench laboratory.
- Official MCP Python SDK 2.3.0 client/server with negotiated 2026-07-28 protocol.
- Separate MCP direct in-process, stdio and Streamable HTTP tool-access scenarios.
- Deterministic credit-analysis tool and versioned fixture resource with real integration tests.
- Bounded generalized fan-out/fan-in plus context, tool-call and resource-read amplification.
- Raw schema v2, MCP-aware manifests/reports, factorized campaigns and trace propagation through public metadata.
- Compose/CI/CLI and bilingual documentation updated for all six scenarios.
- A2A and MCP remain explicitly separate experimental responsibility families.
- Committed MCP smoke/pilot evidence: 144 native rounds, 1,272 successful requests and no errors, timeouts or drops; supplemental k6 smoke covers all three MCP boundaries.
- Native validation passes on Linux and macOS with 32 tests and more than 92% branch-aware coverage.
- Docker Compose build, health and HTTP/A2A/MCP equivalence validation completed on macOS.
- Lightweight container health probes avoid loading the benchmark package and remove shared-runner startup sensitivity.
- Public GitHub Actions release gate passed for native quality and Compose verification.

See [the v0.2.0 release notes](docs/RELEASE_0.2.0.md) for scope, measured evidence and limitations.

## 0.1.0 — 2026-10-25

- Shared deterministic synthetic credit kernel, versioned fixtures and three typed specialist roles.
- In-process, HTTP and official A2A 1.0 JSON-RPC delegation with real protocol tests.
- Open-arrival benchmark harness, deadline/error/drop accounting, resource sampling and manifests.
- Explicit OpenTelemetry treatments with W3C propagation and metadata-only spans.
- Raw schemas, integrity-checked reports, reproducible Matplotlib plots and a k6 arrival path.
- Docker/Compose, GitHub Actions, strict Mypy/Ruff and inherited engineering-harness validators.
- Execution evidence and environmental limits are recorded separately in VALIDATION.md.
