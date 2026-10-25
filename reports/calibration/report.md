# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Payload | Wait | Mode | OTel | Target RPS | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| a2a | 16384 | 250 | sequential | false | 20 | 60 | 0 | 0/0 | 770.938 | 790.654 | 800.562 |
| a2a | 16384 | 250 | sequential | false | 5 | 15 | 0 | 0/0 | 775.324 | 782.238 | 783.185 |
| local | 16384 | 250 | parallel | false | 20 | 60 | 0 | 0/0 | 252.247 | 254.569 | 255.862 |
| http | 16384 | 250 | parallel | false | 5 | 15 | 0 | 0/0 | 258.293 | 262.529 | 266.235 |
| local | 16384 | 250 | parallel | false | 50 | 150 | 0 | 0/0 | 252.291 | 253.410 | 253.817 |
| http | 16384 | 250 | sequential | false | 20 | 60 | 0 | 0/0 | 758.928 | 763.050 | 764.322 |
| a2a | 16384 | 250 | parallel | false | 20 | 60 | 0 | 0/0 | 266.718 | 316.794 | 345.896 |
| http | 16384 | 250 | sequential | false | 5 | 15 | 0 | 0/0 | 766.784 | 852.330 | 902.318 |
| http | 16384 | 250 | parallel | false | 20 | 60 | 0 | 0/0 | 260.532 | 283.023 | 291.466 |
| a2a | 16384 | 250 | parallel | false | 5 | 15 | 0 | 0/0 | 271.142 | 298.668 | 333.744 |
| local | 16384 | 250 | sequential | false | 20 | 60 | 0 | 0/0 | 753.596 | 757.143 | 758.513 |
| http | 16384 | 250 | parallel | false | 50 | 150 | 0 | 0/0 | 257.291 | 275.388 | 314.479 |
| local | 16384 | 250 | sequential | false | 50 | 150 | 0 | 0/0 | 753.662 | 755.671 | 759.787 |
| a2a | 16384 | 250 | sequential | false | 50 | 150 | 0 | 0/0 | 783.668 | 820.793 | 851.403 |
| a2a | 16384 | 250 | parallel | false | 50 | 150 | 0 | 0/0 | 306.384 | 975.921 | 1034.414 |
| http | 16384 | 250 | sequential | false | 50 | 150 | 0 | 0/0 | 760.109 | 764.913 | 768.423 |
| local | 16384 | 250 | sequential | false | 5 | 15 | 0 | 0/0 | 754.184 | 756.224 | 757.167 |
| local | 16384 | 250 | parallel | false | 5 | 15 | 0 | 0/0 | 252.232 | 252.967 | 253.181 |

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
