# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Payload | Wait | Mode | OTel | Target RPS | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| a2a | 1024 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 65.461 | 72.536 | 73.777 |
| http | 1024 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 56.769 | 67.147 | 68.576 |
| a2a | 16384 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 192.190 | 267.026 | 280.818 |
| http | 131072 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 10.844 | 11.765 | 11.873 |
| http | 1024 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 7.038 | 12.487 | 13.440 |
| a2a | 131072 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 30.603 | 33.690 | 33.757 |
| local | 131072 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 756.320 | 759.019 | 759.496 |
| http | 131072 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 14.377 | 16.144 | 16.419 |
| http | 16384 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 768.269 | 788.743 | 791.666 |
| local | 16384 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 52.548 | 54.764 | 55.077 |
| local | 16384 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 252.464 | 252.683 | 252.710 |
| http | 1024 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 261.604 | 271.826 | 273.665 |
| http | 16384 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 259.298 | 262.360 | 262.838 |
| a2a | 131072 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 38.790 | 60.913 | 64.049 |
| http | 131072 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 59.608 | 59.826 | 59.852 |
| local | 1024 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 52.200 | 52.954 | 53.045 |
| http | 1024 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 159.298 | 162.414 | 162.846 |
| a2a | 16384 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 65.700 | 71.942 | 72.185 |
| local | 1024 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 753.160 | 753.569 | 753.571 |
| a2a | 131072 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 282.752 | 315.714 | 321.395 |
| local | 16384 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 754.118 | 756.174 | 756.264 |
| a2a | 1024 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 16.173 | 20.723 | 21.059 |
| http | 1024 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 762.389 | 765.576 | 765.580 |
| a2a | 1024 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 264.849 | 267.465 | 267.928 |
| http | 16384 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 7.894 | 23.562 | 26.459 |
| local | 1024 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 1.818 | 7.374 | 8.479 |
| http | 16384 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 7.237 | 10.760 | 11.030 |
| a2a | 16384 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 841.104 | 964.575 | 974.904 |
| http | 1024 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 7.119 | 9.024 | 9.316 |
| http | 131072 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 263.026 | 265.923 | 266.175 |
| a2a | 131072 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 796.386 | 799.702 | 800.177 |
| http | 16384 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 161.739 | 167.656 | 168.352 |
| local | 131072 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 3.859 | 4.947 | 5.048 |
| a2a | 1024 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 172.642 | 178.801 | 179.517 |
| http | 131072 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 165.072 | 165.533 | 165.583 |
| a2a | 131072 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 201.295 | 203.498 | 203.580 |
| local | 131072 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 4.150 | 5.067 | 5.144 |
| a2a | 16384 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 19.539 | 24.265 | 25.060 |
| a2a | 131072 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 79.608 | 80.725 | 80.922 |
| local | 1024 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 152.806 | 153.366 | 153.366 |
| http | 16384 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 57.180 | 58.848 | 59.043 |
| a2a | 1024 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 11.757 | 12.136 | 12.194 |
| local | 1024 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 252.153 | 255.030 | 255.393 |
| http | 131072 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 765.530 | 773.047 | 774.059 |
| a2a | 16384 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 13.298 | 15.464 | 15.544 |
| local | 16384 | 0 | sequential | false | 5 | 5 | 0 | 0/0 | 1.185 | 1.196 | 1.197 |
| local | 16384 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 153.378 | 154.703 | 154.964 |
| local | 131072 | 50 | sequential | false | 5 | 5 | 0 | 0/0 | 155.993 | 156.443 | 156.475 |
| local | 131072 | 50 | parallel | false | 5 | 5 | 0 | 0/0 | 54.590 | 55.505 | 55.537 |
| local | 131072 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 254.127 | 254.767 | 254.782 |
| a2a | 16384 | 250 | parallel | false | 5 | 5 | 0 | 0/0 | 265.906 | 268.914 | 269.218 |
| local | 1024 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 0.931 | 2.822 | 2.970 |
| local | 16384 | 0 | parallel | false | 5 | 5 | 0 | 0/0 | 1.104 | 1.164 | 1.166 |
| a2a | 1024 | 250 | sequential | false | 5 | 5 | 0 | 0/0 | 770.542 | 773.166 | 773.172 |

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
