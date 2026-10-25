# Raw data schema v1

Authoritative machine-readable JSON Schemas are under `schemas/`, generated from `benchmark.models`. JSONL has one complete object per line. Floating point durations use monotonic elapsed milliseconds, not wall-clock timestamps. No generated example numbers are mixed with measured evidence.

| File | Unit | Required interpretation |
|---|---|---|
| `manifest.json` | Completed round | Config, UTC start/end, commit/dirty status, lock hash, runtime/SDK versions, environment, topology, image digest or null, case hash, counts, elapsed time, file hashes and limitations |
| `samples.jsonl` | Offered arrival | Index, scheduled/start offsets, scheduler lag, arrival/service duration, outcome, error type, specialist timings, bytes/calls/codec/transport totals, trace ID |
| `resources.jsonl` | Process/time point | Process role, procfs-visible PID, elapsed offset, cumulative CPU seconds and instantaneous RSS bytes |
| `*-spans.jsonl` | Exported span | Service/name, trace/span/parent IDs, start ns, duration ms, status; no payload content |
| `campaign.json` | Planned campaign | Exact configuration source, seeded round order, completed run IDs |

Success requires three validated business results. `remote_calls`, body byte totals and adapter timings are null for failures because partial accounting is not recovered in v0.1. Local success has zero remote calls/body bytes. Empty specialist timings on failure mean missing data, not zero specialist work. A dropped arrival has no service execution, zero service duration and an explicit generator limit reason.

Completed means an admitted execution ended, including errors/timeouts. Offered = completed + generator drops; succeeded <= completed. Report error rate uses completed as denominator; successful throughput uses the full window plus drain. Effective arrival rate uses admitted arrivals / configured arrival window. Expected offered arrivals = ceil(rate * duration); all their indices must appear exactly once. A round without a manifest is incomplete and excluded rather than repaired.

`image_hashes.application=null` means native execution without a measured application image. `network` distinguishes no transport from loopback HTTP/1.1 and records workers/pools/discovery. Cgroup controls may be null when unavailable; host-reported memory/CPU are not silently substituted for enforced limits. On this Work environment the mounted procfs uses a parent PID namespace; process IDs are explicitly resolved via `/proc/self/status` and advertised by the local health endpoint for sampling.

Schemas fix `extra=forbid` for raw records/config/manifest. Model validation occurs before reporting; raw sample/resource SHA-256 checks detect edits. The hashes establish file integrity relative to the manifest, not signed provenance or resistance to malicious rewriting of both files. Manifest hashes must be independently published if stronger evidence is required.

Matplotlib and CSV/Markdown reports consume only completed native manifests and existing raw files. Percentiles use linear interpolation; n=0 produces N/A, never fabricated observations. Per-round success latency excludes failed requests; inspect error/drop/timeout columns alongside it. k6 raw records use k6's own Metric/Point schema and are deliberately not parsed as native Sample objects.
