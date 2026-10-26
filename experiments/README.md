# Recorded experiments

All data under `experiments/results/` are real measurements collected on 2026-10-25 UTC.
The v0.1 native measurements use commit `5eefbd76`; the MCP v0.2 native measurements use
`cbf803b5`. Supplemental k6 measurements use `c3f573a` (delegation) or `4fd93ebc` (MCP).
Full SHAs and lock hashes are retained in the manifests. Every published measurement reports
`git_dirty=false`; aborted or dirty development attempts are not included.

The first v0.3 development milestone has committed macOS smoke evidence under
`v030-macos-final`; its validation scope is recorded separately. The resource-isolation
definitions are executable plans only. No v0.2 result is relabeled as fault, recovery,
idempotency, isolation or saturation evidence.

| Dataset | Rounds | Successful executions | Purpose |
|---|---:|---:|---|
| pilot | 30 | 1200 | 5 repeats, minimal workload, 1 KiB, 20 RPS, sequential, OTel off/on |
| coverage | 54 | 270 | All payload/wait/mode combinations at 5 RPS, one repeat, telemetry off |
| calibration | 18 | 1350 | 16 KiB, 250 ms wait, sequential/parallel, 5/20/50 RPS, one repeat |
| mcp-smoke | 24 | 72 | Three MCP boundaries, sequential/parallel, context/resource smoke |
| mcp-pilot | 120 | 1200 | Five repeats of context/resource/telemetry factors at 10 RPS |
| v030 resilience/timeout/backpressure smoke | 45 | 114 successful, 411 expected treatment errors | First v0.3 controlled-treatment validation |
| k6 delegation | 3 | 33 | Supplemental constant-arrival-rate checks for local/HTTP/A2A |
| k6 MCP | 3 | 31 | Supplemental constant-arrival-rate checks for direct/stdio/Streamable HTTP |

Native offered=completed=succeeded for all 4,092 executions; error/timeout/drop counts are zero.
Each k6 scenario additionally has three warmup executions. k6's boundary scheduling can yield
10 or 11 measured iterations in a two-second window at a configured 5/s; actual counts are
retained rather than replaced with `rate * duration`. k6 built-in HTTP summaries include warmup;
custom `abb_measured_*` metrics do not. No k6/native latency pooling is performed.

Rebuild the native reports:

```bash
uv run abb report --input experiments/results/pilot --output reports/pilot
uv run abb report --input experiments/results/coverage --output reports/coverage
uv run abb report --input experiments/results/calibration --output reports/calibration
uv run abb report --input experiments/results/mcp-smoke --output reports/mcp-smoke
uv run abb report --input experiments/results/mcp-pilot --output reports/mcp-pilot
```

Do not infer sustained saturation from these short measurements. Neither 1,620-round full
matrix nor the 1,440-round MCP amplification matrix was executed. Native raw schemas/manifests
include process CPU/RSS where public process ownership permits it; the official MCP stdio client
does not expose its child PID. Supplemental k6 smoke has no process resource collection, as
stated in its manifests. This host is shared, not an isolated performance rig. Independent
per-round results/outliers are deliberately preserved.

For v0.3 development, start with:

```bash
uv run abb campaign --config experiments/resilience-smoke.json \
  --output results/resilience-smoke
uv run abb campaign --config experiments/timeout-smoke.json \
  --output results/timeout-smoke
uv run abb campaign --config experiments/backpressure-smoke.json \
  --output results/backpressure-smoke
```

`resilience-full.json` defines 1,920 rounds, `timeout-full.json` defines 120 rounds and
`backpressure-full.json` defines 270 rounds,
all with five repetitions. Do not run them concurrently or publish shared-runner timings as
capacity evidence. See [the resilience methodology](../docs/RESILIENCE.md).

The resource-isolation smoke has 12 rounds and the full matrix has 180 rounds per Compose
profile. Run the same matrix once with generous and once with constrained limits; do not add
the profile label to the matrix itself because the container runtime owns that treatment.
See [the resource-isolation methodology](../docs/RESOURCE_ISOLATION.md) for exact commands and
acceptance rules.
