# Experimental methodology

## Unit and controlled variables

At the default topology, one offered execution performs exactly three specialist operations on one immutable case. `specialist_repetitions` expands that fan-out in complete three-role blocks. Domain rules, expected results, seed, timeout, active-execution limit and instrumentation mode are identical across matched runs within a treatment family. HTTP/A2A each use one native Python process and one Uvicorn worker. MCP uses the official v2 client/server through direct dispatch, stdio or one Streamable HTTP worker. A2A card resolution and MCP discovery/listing occur once before warmup. Cold start and discovery are not steady-state measurements.

Delegation and tool access are separate research questions. A0/A1/A2 compare direct specialist delegation boundaries. T0/T1/T2 compare MCP tool/resource access boundaries. Cross-family rows may be useful for architecture budgeting, but are not protocol substitutability tests and must not be ranked without responsibility/topology context.

Remote services contain all three roles; specialist-per-container deployment is outside this experiment. A0 deliberately removes the remote process. Consequently process count is a treatment dimension between local and remote; we do not falsely match it away. The generator shares the supervisor process for native campaigns and competes with it for CPU. Record that confound rather than attribute every difference to the wire.

All payload targets refer to sorted compact ASCII domain case JSON, not complete task/envelope bytes. Fixtures store exact bodies and expected business responses; the manifest hashes the case. Seed 42 is the versioned baseline. Runtime timing fields never enter business equality comparisons.

## Workload and order

The minimum workload performs integer rules and hashes the case. 50/250 ms variants perform the same rules then await `asyncio.sleep`. Scheduler pressure can make actual elapsed waits longer. These are controlled requested waits, not calibrated CPU budgets. Larger cases require additional real hashing/serialization work, which is part of the observed payload-size effect.

Sequential and concurrent orchestration use the same ordered task list. v0.2 supports 1–32 repetitions of all three roles and a 1–128 bounded parallel fan-out limit. Concurrent orchestration uses TaskGroup cancellation on error and a semaphore around adapter invocations. A single supervisor deadline covers fan-out and fan-in. There are no retries or idempotency guarantees beyond pure deterministic computation; those remain v0.3 work.

MCP context amplification sends 0/1/4/16 exact copies of task JSON as unused synthetic context, validating equality at the tool boundary. It is not a claim about LLM attention or tokenization. `tool_repetitions` repeats deterministic tool access and requires equal results. `resource_reads` bypasses the client response cache and validates every returned fixture. Factor these independently; a fully crossed matrix changes several causal variables at once.

Each round creates a fresh session, performs the configured warmup executions (excluded from samples), then measures. A seeded shuffle randomizes scenarios and configurations within each repetition. Complete campaigns require at least five repeats; the full matrix uses five. Campaign plans are persisted before work starts, with a completed-round list updated after each success. Do not select only favorable repeats after inspecting results.

## Arrivals and coordinated omission

The native generator schedules arrival i at `epoch + i/rate` using a monotonic clock. It never waits for a response to schedule the next arrival. If the active execution limit is exhausted, it records a dropped offered arrival. If the event loop is late, it records scheduling lag and measures latency from the original deadline, not the delayed start. Therefore slow responses cannot silently suppress the offered workload or hide the delayed portion. A heavily delayed generator still invalidates a capacity claim: inspect lag and drops, not just success P95.

k6 supplies an independent `constant-arrival-rate` path through a common supervisor HTTP ingress. Fixed preallocated VUs avoid changing allocation during the window; insufficient VUs produce explicit `dropped_iterations`. Its HTTP timers and ingress topology differ from native scheduled-arrival timers, so these datasets must stay separate. The k6 setup phase warms three executions; custom measured metrics exclude that phase.

## Measurement definitions

- Arrival latency: scheduled deadline to completion, including generator lag and export work at the execution boundary.
- Service duration: actual task start to completion. It includes all supervisor/adapter work and final business validation.
- Specialist time: immediately around the shared kernel, excluding transport translation. It includes real rule/hash work and requested synthetic wait.
- Serialization: explicit task JSON encoding and reply decoding in the remote adapter. SDK ProtoJSON, envelopes and JSON-RPC work also occur inside the transport scope; they are not separately isolated.
- Transport scope: entire remote adapter operation, including SDK work, remote wait and response. It is NOT network-only latency.
- Bytes: HTTP/A2A use actual request/response body lengths observed through public HTTPX hooks. MCP uses explicit serialized tool arguments/text results plus resource URI/content lengths. MCP JSON-RPC/HTTP framing is excluded because stdio/direct public clients do not expose equivalent byte hooks. Failed partial counts are null. Compare bytes only under the recorded scope.
- Boundary calls: `remote_calls` is retained for schema compatibility and counts adapter boundary operations. MCP additionally reports `tool_calls`, `resource_reads` and duplicated `context_bytes`; `mcp-inprocess` has protocol operations but no network.
- Throughput: successful executions divided by the elapsed measurement window including drain. Effective admitted arrival rate is non-dropped starts / configured arrival duration. Planned rate, offered count and dropped count remain separately available.
- Errors/timeouts: failures among admitted executions; drops belong to the generator, not service error rate. Failure durations remain in raw samples; success percentiles must not obscure availability.
- CPU: process user+system seconds sampled at approximately 100 ms. Separate harness and worker deltas; divide by elapsed seconds to obtain average consumed cores if needed. Not normalized to host CPU count.
- Memory: sampled process RSS, not allocator usage or exact instantaneous peak. Monitoring itself has overhead and runs in both baseline modes.

The official high-level stdio client owns its subprocess without exposing its PID through the public API. v0.2 therefore records harness resources but leaves stdio specialist CPU/RSS unavailable instead of discovering it through SDK internals or process-name heuristics.

Report per-round n, percentiles by linear interpolation, mean/median and all failure counters. Do not infer P99 stability from a handful of smoke observations. Preserve repetitions individually; no unqualified pooling across machines/configurations. Paired telemetry effects are observational differences under matched settings, not a universal OTel price. No difference of averages establishes causal transport decomposition.

## Instrumentation treatment

Off uses NullProbe and performs no explicit OTel calls at benchmark boundaries. On owns an independent TracerProvider with explicit always-on sampling and synchronous JSONL export. HTTP uses W3C headers; MCP uses the public request `meta` field and a public server middleware. SDK automatic spans remain on the global default no-op provider; the experiment does not monkey patch SDK internals. Instrumentation/export and resource sampling settings must accompany every claim. Spans include warmup; use measured sample trace IDs to filter them.

## Validity and acceptance

Reject missing/tampered raw files, bad schemas, non-contiguous sample indices and manifest count mismatches. An aborted round lacks a completed manifest. Keep its logs for diagnosis; do not manufacture a result. Success requires real adapter contract equality, official A2A and MCP protocol tests, error/timeout tests, strict typing, lint and architecture checks. CI is a functional test environment; its timings are never promoted as comparable measurements.

Same-host synthetic waits do not establish cross-region cost, CPU parallelism, fault isolation, tenant/security isolation, availability, model behavior or independent scaling. Record OS, architecture, hardware/cgroup constraints, dependency lock, commit and dirty state. Native rounds use no application image and record its digest as null. Container campaigns must capture their actual built images and topology; the provided Compose smoke alone is not a performance campaign.

References consulted 2026-10-25: [k6 open arrivals](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/), [Azure chatty I/O](https://learn.microsoft.com/en-us/azure/architecture/antipatterns/chatty-io/), [Azure design principles](https://learn.microsoft.com/en-us/azure/architecture/guide/design-principles/).
