# v0.3 resilience experiments

v0.3 adds controlled failure and pressure factors to the A0/A1/A2 delegation family. The
business kernel, fixtures and expected results are unchanged. MCP remains the tool/resource
access family introduced in v0.2 and is intentionally excluded from these delegation retry and
idempotency claims.

This document describes development version `0.3.0.dev0`. It is not a published v0.3 release
or a claim that the complete v0.3 roadmap has been validated.

## Treatments

| Control | Meaning |
|---|---|
| `fault_mode=none` | Retry machinery is enabled when `max_attempts > 1`, but no fault is injected |
| `fail-first` | The selected first attempt fails before the kernel executes |
| `delay-first` | The selected first attempt waits for `fault_delay_ms` and returns a transient failure without running the kernel; use a shorter `attempt_timeout` to produce a controlled client timeout |
| `after-commit` | The kernel executes, then the first response reports a transient failure |
| `fault_every=N` | SHA-256 of the stable delegation ID deterministically selects one in N delegations |
| `max_attempts` | Total bounded attempts, including the initial call |
| `retry_backoff_ms` | Fixed client-side wait between transient failures |
| `idempotency` | Enables a bounded worker-local result cache keyed by delegation ID |
| `service_concurrency` | Maximum active specialist operations; zero disables service admission control |
| `queue_capacity` | Maximum waiting operations before explicit overload rejection |
| `queue_timeout_ms` | Maximum wait for service admission |

The supervisor creates one delegation ID per specialist operation and reuses it for every retry.
The ID is application metadata, not part of `AnalysisTask` or the business hash. HTTP carries it
in `X-ABB-Delegation-ID`/`X-ABB-Attempt`; A2A carries it in the public `Message.metadata` field;
the local adapter passes the same typed metadata directly.

`after-commit` distinguishes retry from idempotency. Without idempotency, a retry executes the
kernel twice. With idempotency, the first result is stored before the injected response failure
and the retry is served from cache. Raw counters expose both outcomes. The cache has explicit
capacity and TTL, is process-local and is lost on restart. It is not a durable distributed
idempotency guarantee.

Each cache entry also binds the delegation ID to a canonical task hash. Reusing an ID for a
different task returns the permanent `idempotency_conflict` error instead of a cached result.
The hash, not the task payload, is retained for this check.

## Commands

Run one deterministic recovery treatment:

```bash
uv run abb run --scenario a2a --profile smoke \
  --fault-mode after-commit --max-attempts 2 --attempt-timeout 1 \
  --idempotency --output results/v030-a2a-after-commit
```

Run a controlled first-attempt timeout:

```bash
uv run abb run --scenario http --profile smoke \
  --fault-mode delay-first --fault-delay-ms 2000 \
  --attempt-timeout 1 --max-attempts 2 --retry-backoff-ms 1500 \
  --output results/v030-http-timeout
```

Run the short matrices:

```bash
uv run abb campaign --config experiments/resilience-smoke.json \
  --output results/resilience-smoke
uv run abb campaign --config experiments/timeout-smoke.json \
  --output results/timeout-smoke
uv run abb campaign --config experiments/backpressure-smoke.json \
  --output results/backpressure-smoke
```

The full definitions require five repetitions:

- `experiments/resilience-full.json`: 1,920 rounds.
- `experiments/timeout-full.json`: 120 rounds.
- `experiments/backpressure-full.json`: 270 rounds.

They are definitions, not recorded results. Run them only on a documented, isolated host and
preserve every completed round rather than selecting favorable repetitions.

Warmup uses the configured treatment. Expected typed fault/retry/admission failures are counted
as `warmup_failed` rather than aborting the round; any unclassified warmup exception still aborts.
`warmup_succeeded + warmup_failed` must equal the configured warmup count.

The HTTP client's transport timeout uses the round-level `timeout`; the supervisor owns the
shorter per-attempt deadline. This avoids a race between an SDK transport timeout and the declared
application treatment. A late remote `delay-first` handler never executes the business kernel.
The general resilience campaign keeps a one-second attempt deadline so ordinary loopback jitter
is not mislabeled as a fault. The separate timeout campaign uses a one-second attempt deadline, a
2,000 ms injected delay and a declared 1,500 ms retry backoff. This avoids retrying before a
canceled A2A request lifecycle can finish. These are controlled campaign parameters, not inferred
universal retry recommendations.

## Raw observations

Schema v3 adds `attempts`, `retries`, `kernel_executions`, `idempotency_hits`,
`injected_failures`, `rejections` and `backpressure_wait_ms`. Failed retry sequences retain
measurements already observed on completed attempts. A null value still means unavailable; it
must not be converted to zero. `remote_calls` includes failed HTTP/A2A attempts when their public
client hooks observed the request.

Telemetry names retry attempts, backoff, admission waits, injected faults and idempotency hits.
The exporter remains metadata-only. Enabling telemetry remains a separate experimental factor.

## Interpretation limits

- Faults are deterministic application-layer treatments. They do not reproduce every packet,
  proxy, process, machine or regional failure.
- The synthetic kernel is side-effect free. `kernel_executions` demonstrates duplicate work;
  it is not evidence that a real financial write can be made idempotent by caching a response.
- Immediate A2A Message replies still exclude durable task recovery and polling.
- Admission control is per worker. Multi-worker/global quotas require a separate design.
- Generator concurrency drops and service rejections are different events and remain separate.
- Resource isolation, cross-host network treatments, sustained external-generator sweeps and
  collector/exporter loss accounting remain later v0.3 milestones.

See [ADR 0007](adr/0007-controlled-resilience-treatments.md), the
[methodology](METHODOLOGY.md), the [raw schema](RESULTS_SCHEMA.md) and the
[development validation record](validation/v0.3-development.md).
