# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Fault | Idempotent | Attempts/retries | Rejections | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| a2a | none | false | 15/0 | 0 | 5 | 0 | 0/0 | 116.140 | 120.579 | 120.754 |
| a2a | none | false | 5/0 | 5 | 0 | 0 | 5/0 | N/A | N/A | N/A |
| local | none | false | 50/0 | 50 | 0 | 0 | 50/0 | N/A | N/A | N/A |
| http | none | false | 28/0 | 16 | 4 | 0 | 16/0 | 135.760 | 169.392 | 170.339 |
| local | none | false | 97/0 | 73 | 8 | 0 | 42/0 | 128.589 | 142.207 | 145.305 |
| http | none | false | 15/0 | 0 | 5 | 0 | 0/0 | 109.001 | 110.486 | 110.742 |
| a2a | none | false | 50/0 | 50 | 0 | 0 | 50/0 | N/A | N/A | N/A |
| http | none | false | 5/0 | 5 | 0 | 0 | 5/0 | N/A | N/A | N/A |
| http | none | false | 50/0 | 50 | 0 | 0 | 50/0 | N/A | N/A | N/A |
| a2a | none | false | 26/0 | 17 | 3 | 0 | 17/0 | 112.098 | 157.944 | 162.019 |
| local | none | false | 15/0 | 0 | 5 | 0 | 0/0 | 104.146 | 105.433 | 105.627 |
| http | none | false | 56/0 | 50 | 2 | 0 | 48/0 | 138.313 | 138.415 | 138.425 |
| local | none | false | 20/0 | 20 | 0 | 0 | 20/0 | N/A | N/A | N/A |
| a2a | none | false | 21/0 | 21 | 0 | 0 | 20/0 | N/A | N/A | N/A |
| a2a | none | false | 57/0 | 48 | 3 | 0 | 47/0 | 138.321 | 149.668 | 150.676 |
| http | none | false | 20/0 | 20 | 0 | 0 | 20/0 | N/A | N/A | N/A |
| local | none | false | 5/0 | 5 | 0 | 0 | 5/0 | N/A | N/A | N/A |
| local | none | false | 30/0 | 18 | 4 | 0 | 16/0 | 128.590 | 154.917 | 155.148 |
| http | after-commit | true | 18/9 | 0 | 3 | 0 | 0/0 | 43.391 | 45.313 | 45.484 |
| local | delay-first | true | 18/9 | 0 | 3 | 0 | 0/0 | 790.524 | 792.209 | 792.358 |
| a2a | fail-first | false | 18/9 | 0 | 3 | 0 | 0/0 | 64.190 | 68.091 | 68.437 |
| a2a | after-commit | true | 18/9 | 0 | 3 | 0 | 0/0 | 57.968 | 63.379 | 63.860 |
| http | delay-first | true | 18/9 | 0 | 3 | 0 | 0/0 | 816.071 | 821.309 | 821.775 |
| http | fail-first | false | 18/9 | 0 | 3 | 0 | 0/0 | 43.783 | 54.055 | 54.969 |
| a2a | none | true | 9/0 | 0 | 3 | 0 | 0/0 | 15.141 | 21.429 | 21.988 |
| http | fail-first | true | 18/9 | 0 | 3 | 0 | 0/0 | 53.617 | 73.016 | 74.740 |
| http | after-commit | false | 18/9 | 0 | 3 | 0 | 0/0 | 56.067 | 59.723 | 60.048 |
| a2a | none | false | 9/0 | 0 | 3 | 0 | 0/0 | 19.205 | 21.155 | 21.328 |
| local | none | true | 9/0 | 0 | 3 | 0 | 0/0 | 2.735 | 3.368 | 3.424 |
| http | delay-first | false | 18/9 | 0 | 3 | 0 | 0/0 | 815.135 | 815.710 | 815.761 |
| a2a | delay-first | true | 18/9 | 0 | 3 | 0 | 0/0 | 825.295 | 832.697 | 833.355 |
| local | after-commit | false | 18/9 | 0 | 3 | 0 | 0/0 | 35.682 | 37.419 | 37.574 |
| http | none | true | 9/0 | 0 | 3 | 0 | 0/0 | 10.854 | 78.322 | 84.319 |
| local | fail-first | false | 18/9 | 0 | 3 | 0 | 0/0 | 35.622 | 36.528 | 36.608 |
| a2a | after-commit | false | 18/9 | 0 | 3 | 0 | 0/0 | 65.142 | 65.806 | 65.865 |
| local | delay-first | false | 18/9 | 0 | 3 | 0 | 0/0 | 792.049 | 794.608 | 794.836 |
| a2a | fail-first | true | 18/9 | 0 | 3 | 0 | 0/0 | 64.043 | 69.175 | 69.631 |
| http | none | false | 9/0 | 0 | 3 | 0 | 0/0 | 9.966 | 12.753 | 13.001 |
| local | after-commit | true | 18/9 | 0 | 3 | 0 | 0/0 | 37.841 | 38.107 | 38.130 |
| local | fail-first | true | 18/9 | 0 | 3 | 0 | 0/0 | 34.698 | 36.392 | 36.542 |
| local | none | false | 9/0 | 0 | 3 | 0 | 0/0 | 1.690 | 2.559 | 2.636 |
| a2a | delay-first | false | 18/9 | 0 | 3 | 0 | 0/0 | 815.728 | 819.374 | 819.698 |
| http | delay-first | false | 6/3 | 0 | 1 | 0 | 0/0 | 7529.384 | 7529.384 | 7529.384 |
| local | delay-first | false | 6/3 | 0 | 1 | 0 | 0/0 | 7510.844 | 7510.844 | 7510.844 |
| a2a | delay-first | false | 6/3 | 0 | 1 | 0 | 0/0 | 7543.661 | 7543.661 | 7543.661 |

## Architectural Decision Insights

Compare repetitions within identical workload, topology, rate and telemetry settings.
A boundary's observed cost includes SDK work, codecs, kernel execution, scheduling and transport.
A difference between means does not identify a causal transport component.
Use isolation, independent deployment and interoperability requirements alongside measured latency budgets.
A2A immediate replies do not measure durable delegation, failure recovery or remote trust boundaries.
MCP rows measure tool/resource access and must not be interpreted as an A2A replacement or agent-delegation ranking.
Retry, idempotency and backpressure rows are controlled application-layer treatments; they do not model every host or network failure.
Local deployment has fewer processes; the experiment does not prove a universal topology winner.

## Provenance and limits

See each manifest for exact commit, hardware, constraints, versions, seed and limitations.
CPU deltas and sampled peak RSS are in summary.csv. Harness CPU includes generator and supervisor.
Native runs use no container image; an absent image digest is null, never an invented hash.
Spans include warmup; correlate measured requests through samples.jsonl trace_id.
