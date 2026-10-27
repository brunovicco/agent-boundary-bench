# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Isolation | CPU iterations | Memory bytes | Fault | Attempts/retries | Rejections | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| http | constrained | 25000 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 204.750 | 280.034 | 294.640 |
| http | constrained | 0 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 255.853 | 338.016 | 353.809 |
| local | constrained | 25000 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 87.996 | 109.913 | 114.228 |
| a2a | constrained | 0 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 61.970 | 79.780 | 83.328 |
| a2a | constrained | 0 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 76.197 | 89.717 | 91.959 |
| http | constrained | 25000 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 138.088 | 247.087 | 256.843 |
| a2a | constrained | 25000 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 1053.340 | 1411.018 | 1442.572 |
| local | constrained | 25000 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 101.180 | 116.670 | 118.647 |
| http | constrained | 0 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 59.455 | 74.245 | 76.738 |
| local | constrained | 0 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 54.366 | 76.604 | 80.969 |
| local | constrained | 0 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 74.210 | 83.829 | 85.460 |
| a2a | constrained | 25000 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 112.156 | 343.331 | 388.727 |
| http | generous | 25000 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 121.462 | 164.937 | 169.401 |
| http | generous | 0 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 70.520 | 98.267 | 103.441 |
| local | generous | 25000 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 92.858 | 109.686 | 112.549 |
| a2a | generous | 0 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 66.167 | 82.186 | 83.678 |
| a2a | generous | 0 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 73.649 | 91.345 | 94.512 |
| http | generous | 25000 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 89.443 | 110.122 | 110.421 |
| a2a | generous | 25000 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 104.917 | 122.530 | 125.755 |
| local | generous | 25000 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 104.953 | 117.085 | 119.112 |
| http | generous | 0 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 56.672 | 74.163 | 76.587 |
| local | generous | 0 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 56.533 | 72.703 | 75.636 |
| local | generous | 0 | 8388608 | none | 15/0 | 0 | 5 | 0 | 0/0 | 67.395 | 82.400 | 84.431 |
| a2a | generous | 25000 | 0 | none | 15/0 | 0 | 5 | 0 | 0/0 | 96.213 | 115.654 | 118.898 |

## Architectural Decision Insights

Compare repetitions within identical workload, topology, rate and telemetry settings.
A boundary's observed cost includes SDK work, codecs, kernel execution, scheduling and transport.
A difference between means does not identify a causal transport component.
Use isolation, independent deployment and interoperability requirements alongside measured latency budgets.
A2A immediate replies do not measure durable delegation, failure recovery or remote trust boundaries.
MCP rows measure tool/resource access and must not be interpreted as an A2A replacement or agent-delegation ranking.
Retry, idempotency and backpressure rows are controlled application-layer treatments; they do not model every host or network failure.
Isolation labels describe requested treatments; cgroup limit/counter columns in summary.csv are the observed evidence.
CPU iterations are fixed synthetic SHA-256 work, not model inference or a duration-calibrated CPU benchmark.
Memory bytes are fixed touched allocations retained through the configured wait, not a model-memory profile.
Local deployment has fewer processes; the experiment does not prove a universal topology winner.

## Provenance and limits

See each manifest for exact commit, hardware, constraints, versions, seed and limitations.
CPU deltas and sampled peak RSS are in summary.csv. Harness CPU includes generator and supervisor.
Native runs use no container image; an absent image digest is null, never an invented hash.
Spans include warmup; correlate measured requests through samples.jsonl trace_id.
