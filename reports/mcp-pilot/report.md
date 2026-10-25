# Measured round results

These are real observations, not illustrative numbers. One row per independent round.
Latency percentiles use successful scheduled-arrival-to-completion observations, including generator delay.
Errors and drops are separate; success latency is not an availability measure.
P99 with small n is exploratory. No saturation or cross-hardware conclusion follows from smoke runs.

| Scenario | Payload | Wait | Mode | OTel | Target RPS | n | Drops | Errors/timeouts | P50 ms | P95 ms | P99 ms |
|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 9.469 | 10.548 | 10.720 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 4.430 | 4.965 | 5.091 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.594 | 4.723 | 4.911 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 5.545 | 5.929 | 6.029 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.315 | 6.701 | 6.798 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 12.018 | 15.132 | 15.208 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 7.315 | 9.768 | 10.662 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.215 | 8.403 | 8.434 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.758 | 9.296 | 9.335 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 5.086 | 5.712 | 5.850 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.110 | 4.004 | 4.274 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 20.468 | 29.469 | 30.241 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.052 | 18.091 | 18.260 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 15.817 | 21.064 | 21.675 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.005 | 8.717 | 8.881 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.061 | 28.252 | 34.394 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.651 | 18.437 | 18.613 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.822 | 12.692 | 15.610 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 12.169 | 16.223 | 17.390 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 14.113 | 14.961 | 15.039 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 8.252 | 42.755 | 65.123 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 10.045 | 12.837 | 13.291 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.454 | 7.812 | 8.023 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.804 | 15.680 | 16.865 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.272 | 9.878 | 9.995 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 7.954 | 8.714 | 8.715 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 12.169 | 12.598 | 12.688 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.877 | 8.269 | 8.622 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.065 | 7.569 | 7.597 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 5.598 | 6.500 | 6.553 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.141 | 3.789 | 3.974 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.799 | 8.898 | 9.126 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.364 | 16.742 | 16.985 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 5.136 | 5.996 | 6.165 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.119 | 19.257 | 19.982 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.102 | 3.652 | 3.842 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 12.816 | 15.982 | 16.534 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 17.170 | 20.013 | 21.261 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 10.307 | 13.837 | 15.249 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.519 | 9.366 | 9.407 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 5.911 | 8.195 | 8.517 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.481 | 9.433 | 9.627 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 10.582 | 13.431 | 14.299 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 16.211 | 19.757 | 21.296 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.064 | 7.630 | 7.736 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 14.807 | 16.349 | 16.403 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 4.623 | 5.113 | 5.168 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.889 | 16.328 | 16.492 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 9.304 | 10.803 | 11.504 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.209 | 19.674 | 20.033 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 16.624 | 19.279 | 19.527 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.569 | 4.135 | 4.189 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.385 | 8.102 | 8.446 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 7.121 | 19.510 | 24.944 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.146 | 15.412 | 15.600 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.930 | 9.299 | 9.373 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.912 | 10.422 | 10.619 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.403 | 8.398 | 8.567 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.883 | 4.243 | 4.297 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.113 | 6.677 | 6.681 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 6.072 | 8.756 | 9.636 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.191 | 22.150 | 22.638 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.374 | 9.332 | 9.583 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 11.866 | 18.145 | 21.278 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 10.534 | 13.436 | 14.337 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 9.723 | 46.543 | 70.199 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 7.099 | 8.180 | 8.239 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 16.552 | 25.033 | 25.483 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 4.873 | 7.678 | 8.027 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.998 | 12.953 | 12.962 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 16.732 | 26.287 | 30.044 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.159 | 14.183 | 14.289 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 5.332 | 11.104 | 13.749 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.568 | 13.824 | 15.305 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 11.051 | 11.745 | 11.783 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 5.842 | 6.752 | 6.978 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.885 | 39.138 | 51.802 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 2.992 | 4.065 | 4.476 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 7.872 | 8.730 | 8.816 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 18.053 | 26.096 | 28.392 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.059 | 16.686 | 17.095 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.890 | 16.129 | 16.441 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.787 | 7.142 | 7.147 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 14.167 | 17.337 | 18.618 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.826 | 10.935 | 11.296 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 18.900 | 22.464 | 22.613 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 10.211 | 13.050 | 13.057 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.635 | 18.269 | 18.664 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.311 | 9.890 | 10.427 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 8.011 | 10.992 | 11.114 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 4.931 | 5.656 | 5.680 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.058 | 8.294 | 8.543 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.944 | 4.695 | 4.772 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.381 | 10.998 | 11.303 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 11.250 | 14.188 | 15.199 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 15.322 | 20.617 | 22.960 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 8.178 | 9.349 | 9.369 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.159 | 16.179 | 17.148 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 7.697 | 8.290 | 8.342 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 7.589 | 9.433 | 10.015 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 4.805 | 6.153 | 6.708 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.493 | 4.307 | 4.323 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 16.131 | 35.517 | 41.333 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.841 | 9.043 | 9.629 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 16.132 | 19.853 | 20.599 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 15.871 | 20.774 | 22.130 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 14.616 | 25.273 | 31.434 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 5.626 | 7.037 | 7.288 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.395 | 7.329 | 7.476 |
| mcp-streamable-http | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 6.067 | 30.581 | 46.154 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 5.506 | 6.668 | 6.675 |
| mcp-stdio | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 13.773 | 14.959 | 15.118 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 10.858 | 16.158 | 19.331 |
| mcp-inprocess | 16384 | 0 | parallel | false | 10 | 10 | 0 | 0/0 | 3.490 | 9.981 | 13.284 |
| mcp-inprocess | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 11.294 | 14.499 | 14.706 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 17.629 | 24.481 | 24.635 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.636 | 13.030 | 13.474 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 16.327 | 21.751 | 22.321 |
| mcp-stdio | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 8.085 | 13.842 | 16.067 |
| mcp-streamable-http | 16384 | 0 | parallel | true | 10 | 10 | 0 | 0/0 | 11.456 | 17.560 | 18.284 |

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
