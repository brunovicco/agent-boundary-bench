# Agent Boundary Bench v0.2.0

Release date: 2026-10-25

v0.2.0 adds a separate MCP tool/resource-access experiment family without changing the v0.1
delegation question. It also generalizes bounded fan-out/fan-in, records amplification explicitly
and preserves reproducible raw evidence. This release does not rank MCP against A2A: the two
protocols represent different responsibilities.

## Delivered scope

### Delegation family retained from v0.1

- A0: typed Python delegation in process.
- A1: conventional JSON over persistent HTTP/1.1.
- A2: A2A 1.0 JSON-RPC using the official Python SDK.

### MCP tool-access family

- T0: official SDK direct dispatch in process.
- T1: official MCP JSON-RPC over stdio with one owned child process.
- T2: official MCP Streamable HTTP with one worker and persistent client.
- One deterministic `analyze_credit` tool.
- One versioned `credit://fixture/{size}/{seed}` resource template.
- Discovery and tool/resource listing before warmup.
- Public request metadata and server middleware for W3C trace propagation.

### Topology and amplification controls

- Repeated three-specialist fan-out with deterministic ordered fan-in.
- Explicit concurrency bound through `fanout_limit`.
- Independent context-copy, tool-call and uncached resource-read controls.
- Raw schema v2 fields for tool calls, resource reads and duplicated context bytes.
- Backward-compatible report parsing for committed v1 evidence.

### Reproducibility and operations

- Factorized smoke, pilot, full and amplification campaign definitions.
- Open-arrival native harness plus independent k6 `constant-arrival-rate` smoke.
- OpenTelemetry on/off treatments with metadata-only local span export.
- CPU/RSS collection where the public process lifecycle exposes a PID.
- Docker Compose topology for HTTP, A2A, MCP Streamable HTTP and functional verification.
- GitHub Actions quality and Compose functional jobs.
- English and Portuguese documentation, six ADRs and integrity-checked reports.

## Protocols and locked dependencies

| Component | Release used |
|---|---|
| Python | 3.12.14 Linux; 3.12.13 macOS validation |
| A2A protocol binding | JSON-RPC 1.0 |
| A2A Python SDK | 1.2.3 |
| MCP negotiated protocol | 2026-07-28 |
| MCP Python SDK | 2.3.0 |
| MCP types | 2.3.0 |
| HTTPX for A2A/HTTP | 0.28.1 |
| httpx2 for MCP | 2.16.0 |
| OpenTelemetry SDK | 1.45.1 |
| FastAPI / Uvicorn | 0.162.0 / 0.54.0 |
| Pydantic | 2.14.1 |
| k6 used for recorded smoke | 2.3.0 |

The lockfile is authoritative. See [compatibility research](COMPATIBILITY.md) for selected public
APIs, transports and explicit non-goals.

## Validation evidence

| Environment | Result |
|---|---|
| Linux native | 32 tests passed; 92.87% branch-aware coverage |
| macOS native | 32 tests passed; 92.40% branch-aware coverage |
| Static quality | Ruff, strict Mypy and architecture checks passed |
| Security/dependencies | Bandit found zero issues; pip-audit found no known dependency vulnerabilities |
| Docker Compose on macOS | Image built; HTTP/A2A/MCP healthy; equivalence verifier passed |
| GitHub Actions | Native `quality` and Docker `compose` jobs passed at commit `99a5979` |

The coverage difference is limited to platform-specific process/resource sampling paths. The
80% threshold and test selection remained unchanged. GitHub Actions is a functional release gate;
shared-runner latency is never published as benchmark evidence. See the complete
[validation record](../VALIDATION.md) and the live
[workflow](https://github.com/brunovicco/agent-boundary-bench/actions/workflows/quality.yml).
The recorded public release-gate execution is
[run 40230391324](https://github.com/brunovicco/agent-boundary-bench/actions/runs/40230391324).

## Recorded measurements

| Dataset | Rounds | Successful executions | Errors/timeouts/drops |
|---|---:|---:|---:|
| v0.1 delegation datasets | 102 | 2,820 | 0 |
| v0.2 MCP smoke | 24 | 72 | 0 |
| v0.2 MCP repeated pilot | 120 | 1,200 | 0 |
| Native total | 246 | 4,092 | 0 |

The MCP pilot used five repetitions per matched configuration. In the telemetry-off,
zero-context-copy and zero-resource-read condition, median per-round P50 was 3.110 ms for direct
dispatch, 5.842 ms for stdio and 6.315 ms for Streamable HTTP. These are short same-host pilot
observations, not pooled percentiles or portable protocol constants.

Supplemental k6 evidence contains 64 measured executions across all six scenarios plus 18 warmup
executions, with no errors or dropped iterations. Native and k6 timing samples remain separate.

## Important interpretation boundary

A2A delegates work to an independently exposed agent. MCP exposes tools and resources to a host.
HTTP remains the conventional service baseline. Cross-family rows may inform an end-to-end latency
budget, but they do not show that MCP replaces A2A or that either responsibility should always be
local or distributed.

## Known limitations

- Synthetic async waits model I/O waiting, not CPU work or LLM inference.
- No real LLM, customer data, commercial key or external MCP server is used.
- Native generators and systems under test share their recorded hosts.
- The official high-level MCP stdio client does not expose its child PID; worker CPU/RSS is null.
- Request/response byte definitions differ between HTTP/A2A and MCP and must not be pooled silently.
- The 1,620-round full matrices and 1,440-round amplification matrix were not executed.
- v0.2 does not implement controlled fault injection, retry policy, idempotency, backpressure or
  resource-isolation experiments.

## Upgrade and compatibility notes

- Existing v0.1 raw records remain reportable; absent v2 fields receive documented defaults.
- MCP scenarios require the locked v2 SDK interfaces and must not be rewritten using v1 FastMCP
  assumptions or legacy SSE while retaining the current labels.
- Regenerate reports only from validated raw data. Missing samples are not synthesized.
- Re-run the real protocol integration suite after dependency or transport changes.

## Next release

v0.3.0 will treat failures, retries, idempotency, saturation, backpressure and resource isolation
as controlled experimental factors. See the [roadmap](ROADMAP.md); none of those future treatments
is claimed as implemented in v0.2.0.
