# Raw data schema v4

Authoritative machine-readable JSON Schemas are under `schemas/`, generated from `benchmark.models`. JSONL has one complete object per line. Floating point durations use monotonic elapsed milliseconds, not wall-clock timestamps. No generated example numbers are mixed with measured evidence.

| File | Unit | Required interpretation |
|---|---|---|
| `manifest.json` | Completed round | Config, UTC start/end, commit/dirty status, lock hash, runtime/SDK versions, environment, topology, image digest or null, case hash, counts, elapsed time, file hashes and limitations |
| `samples.jsonl` | Offered arrival | Index, scheduled/start offsets, scheduler lag, arrival/service duration, outcome, error type, specialist timings, bytes/calls/codec/transport totals, trace ID and resilience counters |
| `resources.jsonl` | Process/time point | Process role, procfs-visible PID, elapsed offset, process CPU/RSS and nullable cgroup v2 CPU/memory observations |
| `*-spans.jsonl` | Exported span | Service/name, trace/span/parent IDs, start ns, duration ms, status; no payload content |
| `campaign.json` | Planned campaign | Exact configuration source, seeded round order, completed run IDs |

Success requires `3 * specialist_repetitions` validated business results. Local success has zero boundary calls/body bytes. MCP success adds `tool_calls`, `resource_reads` and `context_bytes`; zero means the operation was configured but absent, while null means unavailable. A dropped arrival has no service execution, zero service duration and an explicit generator limit reason.

Schema v3 adds `attempts`, `retries`, `kernel_executions`, `idempotency_hits`,
`injected_failures`, `rejections` and `backpressure_wait_ms`. Completed attempts retain public
adapter observations even if the retry sequence ultimately fails. A timeout can still leave
fields null when the relevant boundary did not expose a completed observation. Empty specialist
timings mean unavailable work measurements, not zero work. `kernel_executions` counts this
synthetic kernel and is not an exactly-once guarantee for external side effects.

Completed means an admitted execution ended, including errors/timeouts. Offered = completed + generator drops; succeeded <= completed. Report error rate uses completed as denominator; successful throughput uses the full window plus drain. Effective arrival rate uses admitted arrivals / configured arrival window. Expected offered arrivals = ceil(rate * duration); all their indices must appear exactly once. A round without a manifest is incomplete and excluded rather than repaired.

`image_hashes.application=null` means native execution without a measured application image. `network` distinguishes in-process, stdio and loopback HTTP topologies and records workers/pools/discovery. The official MCP stdio client does not expose its child PID; its specialist resource series is absent and the manifest states that limitation. Cgroup controls may be null when unavailable; host-reported memory/CPU are not silently substituted for enforced limits.

Schema v4 adds `cpu_iterations`, `memory_bytes`, `resource_sampling` and resource-sample schema v2. Cgroup fields
include cumulative CPU usage/user/system/throttling counters, observed CPU quota in cores,
memory current/peak/limit and `memory.events` counters. `max` limits remain null instead of being
invented as machine totals. Cgroup counters describe the process' cgroup, not the process alone.
The isolation label in `environment.resource_isolation` is requested-treatment metadata; it is
not evidence of an enforced limit. Remote sampling failures remain explicit in the manifest.
`scripts/validate_isolation_results.py` verifies raw hashes/counts and rejects incomplete
campaigns, sampling loss above the declared bound, fewer than two valid observations per role,
absent cgroup v2 evidence, absent image provenance or limits that differ from the declared
treatment. Loss within the explicit bound remains recorded and reported rather than imputed.

Schemas fix `extra=forbid` for raw records/config/manifest. Model validation occurs before reporting; raw sample/resource SHA-256 checks detect edits. The hashes establish file integrity relative to the manifest, not signed provenance or resistance to malicious rewriting of both files. Manifest hashes must be independently published if stronger evidence is required.

Matplotlib and CSV/Markdown reports consume only completed native manifests and existing raw files. Percentiles use linear interpolation; n=0 produces N/A, never fabricated observations. Per-round success latency excludes failed requests; inspect error/drop/timeout columns alongside it. k6 raw records use k6's own Metric/Point schema and are deliberately not parsed as native Sample objects.

`telemetry-deltas.csv` pairs only unique on/off rounds with identical config, environment,
commit and lock. Missing or ambiguous pairs produce no delta. These are observational deltas,
not causal estimates. `span-summary.csv` uses measured trace IDs and excludes warmup spans.

Adapter codec/transport fields are sums across every fan-out operation. Under concurrent execution,
those sums can exceed elapsed supervisor latency; they are not a serial wall-time breakdown.

v2 added MCP scenarios and amplification controls. v3 adds delegation resilience and admission
controls with defaults for fields absent from v1/v2 records. v4 adds CPU/memory work and cgroup resource
observations with nullable defaults for earlier records. Reports can read committed earlier
evidence but must not relabel it as a newer-schema execution. HTTP/A2A byte totals represent observed
bodies; MCP totals represent explicit application tool/resource content and exclude protocol
framing. The per-run manifest is authoritative for measurement scope. The quality gate verifies
that every committed JSON Schema is regenerated from its Pydantic model without drift.
