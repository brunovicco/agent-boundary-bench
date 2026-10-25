# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Payload | Wait | Mode | OTel | Target RPS | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| http | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 8.826 | 14.417 | 17.574 |
| local | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 2.086 | 3.514 | 3.877 |
| http | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 6.951 | 10.198 | 10.720 |
| a2a | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 12.334 | 18.660 | 19.975 |
| local | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 1.052 | 1.604 | 1.629 |
| a2a | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 15.137 | 20.457 | 28.823 |
| http | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 11.487 | 18.909 | 27.188 |
| local | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 3.433 | 34.640 | 56.484 |
| http | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 22.095 | 75.890 | 131.214 |
| a2a | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 214.546 | 376.450 | 394.841 |
| a2a | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 25.215 | 71.090 | 79.833 |
| local | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 2.404 | 5.948 | 6.851 |
| http | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 10.200 | 14.984 | 15.486 |
| local | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 3.885 | 7.876 | 9.290 |
| http | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 12.757 | 31.519 | 34.728 |
| local | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 1.285 | 3.096 | 4.053 |
| a2a | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 20.424 | 26.680 | 28.395 |
| a2a | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 23.015 | 29.866 | 30.639 |
| local | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 3.872 | 57.782 | 108.099 |
| http | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 6.851 | 10.756 | 11.830 |
| http | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 9.172 | 14.305 | 14.758 |
| a2a | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 14.308 | 17.640 | 19.694 |
| a2a | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 14.905 | 19.750 | 24.931 |
| local | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 1.076 | 2.230 | 25.735 |
| local | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 1.960 | 3.305 | 8.200 |
| http | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 21.135 | 46.608 | 63.817 |
| http | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 12.125 | 18.012 | 19.993 |
| local | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 1.150 | 2.747 | 3.842 |
| a2a | 1024 | 0 | sequential | true | 20 | 40 | 0 | 0/0 | 19.644 | 34.508 | 36.541 |
| a2a | 1024 | 0 | sequential | false | 20 | 40 | 0 | 0/0 | 20.218 | 29.150 | 34.182 |

## Architectural Decision Insights

Compare repetitions within identical workload, topology, rate and telemetry settings.
A boundary's observed cost includes SDK work, codecs, kernel execution, scheduling and transport.
A difference between means does not identify a causal transport component.
Use isolation, independent deployment and interoperability requirements alongside measured latency budgets.
A2A immediate replies do not measure durable delegation, failure recovery or remote trust boundaries.
Local deployment has fewer processes; the experiment does not prove a universal topology winner.

## Provenance and limits

See each manifest for exact commit, hardware, constraints, versions, seed and limitations.
CPU deltas and sampled peak RSS are in summary.csv. Harness CPU includes generator and supervisor.
Native runs use no container image; an absent image digest is null, never an invented hash.
Spans include warmup; correlate measured requests through samples.jsonl trace_id.
