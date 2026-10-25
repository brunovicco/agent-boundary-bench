# Architectural Decision Insights from recorded evidence

These are observations on a shared host, not portable performance guarantees.
Native measurements use commit 5eefbd76 and the configurations under experiments/.

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

## Implications for design decisions

A modular monolith can avoid boundary work for frequent small calls; this experiment offers
no measurement of its organizational or failure-isolation costs. Exposing selected specialists
through services or A2A may satisfy deployment/interoperability requirements, but those benefits
must be tested separately. The local-versus-remote medians here can inform a workload-specific
latency budget, not determine a topology alone. Hybrid designs deserve a measured evaluation
at the intended call granularity and with a realistic useful workload.

Before an article makes a capacity, recovery or isolation claim, execute longer isolated
arrival sweeps, repeat the calibrated conditions, and add the v0.3 fault/resource treatments.
MCP v0.2 must remain a separate tool/resource-access question.
