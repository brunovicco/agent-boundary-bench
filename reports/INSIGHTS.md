# Architectural Decision Insights from recorded evidence

These are observations on a shared host, not portable performance guarantees.
Delegation measurements use commit `5eefbd76`; MCP measurements use `cbf803b5`.
Configurations and complete per-round evidence are under `experiments/`.

## Repeated minimal-work pilot

1 KiB canonical payload, 0 ms synthetic wait, sequential delegation, 20 offered RPS,
telemetry off, five rounds, 40 successes per round. Values below are the median of
five per-round percentiles, NOT a pooled request percentile.

| Scenario | Median round P50 (ms) | Median round P95 (ms) | Total n |
|---|---:|---:|---:|
| Local | 1.150 | 2.747 | 200 |
| HTTP | 12.125 | 18.012 | 200 |
| A2A | 20.218 | 26.680 | 200 |

The observed boundary cost matters for this minimal synthetic operation. One A2A off
round had P50=214.546 ms and P95=376.450 ms; it remains in the raw table and chart.
This variation prevents presenting the small sample as a stable universal protocol cost.
On/off telemetry deltas also vary in sign for remote paths. They do not prove negative
instrumentation cost or isolate a causal exporter effect. Inspect all 15 matched pairs.

## Single 50 RPS calibration condition

16 KiB, 250 ms requested async wait per specialist, telemetry off, three-second arrival
window. Each row contains 150 offered and successful executions, no errors or drops,
and only one repetition. These are success scheduled-arrival percentiles.

| Scenario | Mode | P50 ms | P95 ms |
|---|---|---:|---:|
| Local | Sequential | 753.662 | 755.671 |
| Local | Parallel | 252.291 | 253.410 |
| HTTP | Sequential | 760.109 | 764.913 |
| HTTP | Parallel | 257.291 | 275.388 |
| A2A | Sequential | 783.668 | 820.793 |
| A2A | Parallel | 306.384 | 975.921 |

Parallel execution reduced observed median elapsed wait in these conditions, while A2A's
parallel P95 was higher in this single run. That calls for repeated profiling, not a claim
that concurrency always improves or degrades tails. The 250 ms operation is an async wait,
not CPU work. A throughput denominator including drain explains why successful executions
per elapsed second can be below the offered 50/s despite every request completing; that
alone is not saturation evidence.

## Repeated MCP tool-access pilot

16 KiB canonical payload, 0 ms synthetic wait, parallel three-role orchestration, zero context
copies and 10 offered RPS. Each cell below is the median of five telemetry-off round percentiles
with 10 successes per round. MCP discovery/listing occurred before warmup and is not included.

| MCP boundary | Resource reads per specialist | Median round P50 (ms) | Median round P95 (ms) | Total n |
|---|---:|---:|---:|---:|
| Direct in-process | 0 | 3.110 | 4.065 | 50 |
| stdio | 0 | 5.842 | 6.752 | 50 |
| Streamable HTTP | 0 | 6.315 | 8.102 | 50 |
| Direct in-process | 2 | 7.374 | 9.433 | 50 |
| stdio | 2 | 12.169 | 16.179 | 50 |
| Streamable HTTP | 2 | 13.889 | 16.328 | 50 |

These matched conditions show the expected cost of two extra uncached resource reads, but do
not isolate a universal per-read cost. Four copied context payloads changed both bytes and
validation work; their effect was smaller and variable in this short pilot. Across 20 matched
on/off pairs per boundary, synchronous metadata-only OTel export had median mean-latency deltas
of 1.997 ms (direct), 2.818 ms (stdio) and 1.727 ms (Streamable HTTP). Individual deltas retain
shared-host variation, including negative observations, so these are treatment observations,
not causal SDK constants.

All 1,200 pilot requests and 72 MCP smoke requests completed successfully with no errors,
timeouts or drops. That validates the harness and functional paths at the tested rate; it does
not establish sustained capacity. MCP measures tool/resource access. It is not an A2A replacement
or an agent-delegation ranking.

## Container resource-isolation smoke

The macOS Docker smoke used clean commit `d910a570`, one one-CPU/512-MiB harness, and separate
remote specialists at either one CPU/512 MiB (generous) or 0.25 CPU/256 MiB (constrained).
Each cell below is one round with five successful measured requests; therefore ratios are
descriptive observations, not repeated effect estimates.

| Scenario | CPU iterations | Memory | Generous P50 ms | Constrained P50 ms | Constrained/generous |
|---|---:|---:|---:|---:|---:|
| Local | 0 | 0 | 56.533 | 54.366 | 0.962× |
| Local | 0 | 8 MiB | 67.395 | 74.210 | 1.101× |
| Local | 25,000 | 0 | 92.858 | 87.996 | 0.948× |
| Local | 25,000 | 8 MiB | 104.953 | 101.180 | 0.964× |
| HTTP | 0 | 0 | 56.672 | 59.455 | 1.049× |
| HTTP | 0 | 8 MiB | 70.520 | 255.853 | 3.628× |
| HTTP | 25,000 | 0 | 89.443 | 138.088 | 1.544× |
| HTTP | 25,000 | 8 MiB | 121.462 | 204.750 | 1.686× |
| A2A | 0 | 0 | 66.167 | 61.970 | 0.937× |
| A2A | 0 | 8 MiB | 73.649 | 76.197 | 1.035× |
| A2A | 25,000 | 0 | 96.213 | 112.156 | 1.166× |
| A2A | 25,000 | 8 MiB | 104.917 | 1,053.340 | 10.040× |

Both profiles completed 60/60 offered executions and 12/12 warmups with no errors, timeouts,
drops or sampling failures. The constrained A2A CPU-plus-memory round recorded 2.787763 seconds
of specialist cgroup throttling versus zero in its generous match. Across all eight remote rounds,
sampled specialist throttled-time deltas summed to 5.360728 seconds constrained versus 0.065566
seconds generous. No memory pressure or OOM event was observed.

The local arms retained the same harness cgroup in both profiles and provide a useful same-host
control, but the remote architectures have a larger aggregate CPU budget than local. The smoke
therefore demonstrates observable quota enforcement and motivates repeated treatment analysis;
it does not establish a portable slowdown, a protocol ranking or a fixed-total-budget comparison.
See the [raw data](../experiments/results/v030-resource-isolation-macos/),
[derived report](v030-resource-isolation-macos/report.md) and
[validation record](../docs/validation/v0.3-resource-isolation.md).

## Implications for design decisions

A modular monolith can avoid boundary work for frequent small calls; this experiment offers
no measurement of its organizational or failure-isolation costs. Exposing selected specialists
through services or A2A may satisfy deployment/interoperability requirements, but those benefits
must be tested separately. The local-versus-remote medians here can inform a workload-specific
latency budget, not determine a topology alone. Hybrid designs deserve a measured evaluation
at the intended call granularity and with a realistic useful workload.

Before an article makes a capacity, recovery or general isolation claim, execute longer isolated
arrival sweeps and repeat the calibrated conditions. The v0.3 treatments and bounded smoke paths
now exist, but the two 180-round resource-isolation profiles, 1,620-round base matrices and
1,440-round MCP amplification matrix were not executed.
