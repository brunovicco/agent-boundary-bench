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

## Implications for design decisions

A modular monolith can avoid boundary work for frequent small calls; this experiment offers
no measurement of its organizational or failure-isolation costs. Exposing selected specialists
through services or A2A may satisfy deployment/interoperability requirements, but those benefits
must be tested separately. The local-versus-remote medians here can inform a workload-specific
latency budget, not determine a topology alone. Hybrid designs deserve a measured evaluation
at the intended call granularity and with a realistic useful workload.

Before an article makes a capacity, recovery or isolation claim, execute longer isolated
arrival sweeps, repeat the calibrated conditions, and add the v0.3 fault/resource treatments.
The 1,620-round full matrices and 1,440-round MCP amplification matrix were not executed.
