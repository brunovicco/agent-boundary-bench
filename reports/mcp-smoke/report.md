# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Payload | Wait | Mode | OTel | Target RPS | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| mcp-stdio | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 8.643 | 8.691 | 8.695 |
| mcp-inprocess | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 6.045 | 7.778 | 7.932 |
| mcp-streamable-http | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 6.657 | 7.402 | 7.468 |
| mcp-streamable-http | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 15.867 | 15.942 | 15.949 |
| mcp-stdio | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 7.674 | 8.186 | 8.231 |
| mcp-stdio | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 6.924 | 7.279 | 7.311 |
| mcp-streamable-http | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 12.586 | 13.244 | 13.303 |
| mcp-stdio | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 9.850 | 10.704 | 10.780 |
| mcp-stdio | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 4.062 | 4.475 | 4.512 |
| mcp-streamable-http | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 8.379 | 8.819 | 8.859 |
| mcp-stdio | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 5.416 | 6.126 | 6.189 |
| mcp-inprocess | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 4.663 | 4.742 | 4.749 |
| mcp-streamable-http | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 8.358 | 10.065 | 10.217 |
| mcp-inprocess | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 2.487 | 2.854 | 2.887 |
| mcp-stdio | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 10.641 | 11.478 | 11.553 |
| mcp-inprocess | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 2.617 | 2.678 | 2.683 |
| mcp-streamable-http | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 5.748 | 6.321 | 6.372 |
| mcp-inprocess | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 2.561 | 2.619 | 2.624 |
| mcp-streamable-http | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 13.233 | 13.822 | 13.874 |
| mcp-stdio | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 6.759 | 8.845 | 9.031 |
| mcp-inprocess | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 4.941 | 5.129 | 5.146 |
| mcp-inprocess | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 3.547 | 4.023 | 4.066 |
| mcp-inprocess | 1024 | 0 | sequential | false | 5 | 3 | 0 | 0/0 | 6.412 | 7.202 | 7.272 |
| mcp-streamable-http | 1024 | 0 | parallel | false | 5 | 3 | 0 | 0/0 | 5.443 | 5.716 | 5.740 |

## Architectural Decision Insights

Compare repetitions within identical workload, topology, rate and telemetry settings.
A boundary's observed cost includes SDK work, codecs, kernel execution, scheduling and transport.
A difference between means does not identify a causal transport component.
Use isolation, independent deployment and interoperability requirements alongside measured latency budgets.
A2A immediate replies do not measure durable delegation, failure recovery or remote trust boundaries.
MCP rows measure tool/resource access and must not be interpreted as an A2A replacement or agent-delegation ranking.
Local deployment has fewer processes; the experiment does not prove a universal topology winner.

## Provenance and limits

See each manifest for exact commit, hardware, constraints, versions, seed and limitations.
CPU deltas and sampled peak RSS are in summary.csv. Harness CPU includes generator and supervisor.
Native runs use no container image; an absent image digest is null, never an invented hash.
Spans include warmup; correlate measured requests through samples.jsonl trace_id.
