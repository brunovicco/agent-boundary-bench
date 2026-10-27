# v0.3 resource-isolation experiments

This development milestone adds a reproducible container treatment for CPU and memory isolation
to the A0/A1/A2 delegation family. It does not turn requested Compose settings into evidence:
each round records the cgroup v2 limits and counters actually observed by the harness and remote
specialist. A missing counter remains null.

## Experimental boundary

The `local` scenario executes the supervisor, generator and specialist in the runner container's
single cgroup. HTTP and A2A execute the same specialist kernel in a separate service container and
cgroup. This difference is intentional: it is the isolation property under study, not a matched
process-count baseline.

`cpu_iterations` adds a fixed number of SHA-256 iterations per specialist call. `memory_bytes`
allocates and touches a fixed byte array. They are deterministic synthetic resource work, not a
calibrated duration, model inference or realistic credit processing. The resource-isolation
matrices use the same 50 ms asynchronous wait in every arm; this keeps allocations live long
enough to improve sampling opportunity without pretending the wait is CPU work. Business output
remains identical at every resource-work level.

One task is capped at 64 MiB, and configuration validation rejects more than 256 MiB of declared
concurrent allocation within one supervisor execution. Multiple offered executions can still
overlap, so calibration and cgroup event/error inspection remain mandatory.

The metadata-only `/resources` endpoint reports the worker's process CPU/RSS and its own cgroup
v2 counters. It does not expose fixtures or business payloads. The harness samples itself directly
and remote services through that endpoint approximately every 100 ms. Sampling failures and
attempt counts are preserved in `manifest.resource_sampling`. The metadata request has a separate
five-second timeout so a CPU-constrained worker can eventually expose its counters without
changing the business-request deadline.

## Treatments

Use the same campaign file for each resource profile. Only the declared Compose limits, output
directory and treatment label change.

| Profile | Harness | Remote specialist | Purpose |
|---|---|---|---|
| generous | 1 CPU, 512 MiB | 1 CPU, 512 MiB | containerized reference condition |
| constrained | 1 CPU, 512 MiB | 0.25 CPU, 256 MiB | remote-specialist CPU-pressure treatment |

These are starting values, not universal thresholds. The manifest and `resources.jsonl` are
authoritative. `ABB_ISOLATION_LABEL` is only a requested-treatment label. A result is not an
isolation result when the observed cgroup version/limits are absent or inconsistent with the
declared profile.

## Smoke commands

Create a host-writable output directory and build the image:

```bash
mkdir -p results
docker compose -f compose.yaml -f compose.isolation.yaml config --quiet
docker compose -f compose.yaml -f compose.isolation.yaml build
export ABB_HOST_UID="$(id -u)"
export ABB_HOST_GID="$(id -g)"
export ABB_COMMIT_SHA="$(git rev-parse HEAD)"
if test -z "$(git status --porcelain)"; then
  export ABB_GIT_DIRTY=false
else
  export ABB_GIT_DIRTY=true
fi
export ABB_IMAGE_DIGEST="$(docker image inspect agent-boundary-bench:0.3.0-dev0 --format '{{.Id}}')"
uv run python scripts/capture_container_environment.py \
  --output results/resource-isolation/environment.json
```

Run the generous 12-round smoke. Recreate the services for every profile so a previously running
container cannot silently retain the prior limits:

```bash
export ABB_ISOLATION_LABEL=generous
export ABB_ISOLATION_OUTPUT=resource-isolation/smoke-generous
export ABB_SPECIALIST_CPUS=1.0
export ABB_SPECIALIST_MEMORY=512m
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation \
  up -d --wait --force-recreate http a2a
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation \
  run --rm --no-deps isolation-runner
```

Validate hashes, completion, image provenance, sampling success and the observed cgroup limits:

```bash
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation run --rm --no-deps \
  isolation-runner python scripts/validate_isolation_results.py \
  --input /results/resource-isolation/smoke-generous \
  --label generous --harness-cpus 1 --specialist-cpus 1 \
  --harness-memory-bytes 536870912 --specialist-memory-bytes 536870912 \
  --max-sampling-failure-rate 0 \
  --expected-commit-sha "$ABB_COMMIT_SHA" \
  --require-clean-worktree \
  --require-image-digest
```

Run the constrained smoke:

```bash
export ABB_ISOLATION_LABEL=constrained
export ABB_ISOLATION_OUTPUT=resource-isolation/smoke-constrained
export ABB_SPECIALIST_CPUS=0.25
export ABB_SPECIALIST_MEMORY=256m
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation \
  up -d --wait --force-recreate http a2a
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation \
  run --rm --no-deps isolation-runner
```

Use the same validator with `--label constrained --specialist-cpus 0.25` and
`--specialist-memory-bytes 268435456`, plus the same expected-commit and clean-worktree checks.
Keep the harness expectations at one CPU and 512 MiB.
For the deliberately constrained profile, the validator defaults to a maximum 50% loss per role
and round while still requiring at least two valid cgroup v2 observations. The exact failure
counts remain in every manifest and in the validator output; they are never converted to samples.

Generate one integrity-checked report across both treatments:

```bash
uv run abb report --input results/resource-isolation \
  --output reports/resource-isolation-smoke
docker compose -f compose.yaml -f compose.isolation.yaml down --remove-orphans
```

Use a clean `results` subtree or point `abb report` at a parent containing only the campaigns
being compared. Reports recursively include every completed manifest below the input path.

## Full campaign

`experiments/resource-isolation-full.json` defines 180 rounds per profile: three boundaries,
three CPU-work levels, two memory-allocation levels, two arrival rates and five seeded
repetitions. Change the runner command temporarily with Compose `run` arguments; arguments after
the service name replace its command:

```bash
export ABB_ISOLATION_LABEL=generous
export ABB_SPECIALIST_CPUS=1.0
export ABB_SPECIALIST_MEMORY=512m
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation \
  up -d --wait --force-recreate http a2a
docker compose -f compose.yaml -f compose.isolation.yaml --profile isolation run --rm --no-deps \
  isolation-runner abb campaign \
  --config experiments/resource-isolation-full.json \
  --output /results/resource-isolation/full-generous
```

Repeat with the constrained environment and a distinct output directory. Do not run the two
profiles concurrently on the same host. Calibrate the offered rates first and inspect generator
lag, drops, errors, cgroup throttling and sampling failures before treating a run as capacity
evidence. The versioned starting rates are deliberately conservative at 2 and 5 RPS because the
constrained 0.25-CPU specialist also runs fixed CPU work. Replace them only in a separately
versioned campaign after calibration; do not edit a campaign after collecting part of it.

## Recorded evidence and interpretation

Schema v4 adds CPU/memory workload controls plus observed cgroup v2 CPU usage/throttling, CPU
quota, memory current/peak/limit and memory event counters. `summary.csv` derives deltas only when
at least two valid cumulative samples exist. Cgroup CPU and memory counters are cgroup-wide;
process CPU/RSS remain process observations. In native same-cgroup subprocess runs, harness and
specialist cgroup counters can refer to the same group and must not be added together.

An increase in `nr_throttled` or `throttled_usec` is direct evidence that a cgroup encountered
CPU quota throttling. It does not by itself establish that throttling caused a particular latency
change. `memory.peak` is lifetime state for the persistent campaign container and may reflect an
earlier randomized round; sampled `memory.current` and process RSS retain per-round scope but can
miss brief peaks. `memory.events` distinguishes pressure/allocation events from process RSS, but
the provided campaign does not intentionally force OOM kills. Docker Desktop enforces limits
inside its Linux VM; record the macOS host and Docker/VM allocation alongside the in-container
facts.

The profiles cap components, not aggregate architecture budgets: a remote round can consume the
harness quota plus a separate specialist quota, while local work shares only the harness quota.
Do not interpret a local/remote latency difference as boundary cost alone or as proof that
isolation is intrinsically faster. A future fixed-total-budget treatment requires scenario-aware
quota assignment.

Smoke execution validates wiring and schema only. A defensible comparison needs both profiles,
all planned repetitions, clean commits, no concurrent campaigns and complete raw data. No
resource-isolation measurements are committed merely by implementing this milestone.

## Official references

Consulted 2026-10-26:

- [Compose service CPU and memory attributes](https://docs.docker.com/reference/compose-file/services/)
- [Compose deploy resource limits](https://docs.docker.com/reference/compose-file/deploy/)
- [Linux cgroup v2 CPU controller](https://docs.kernel.org/admin-guide/cgroup-v2.html#cpu)
- [Linux cgroup v2 memory controller](https://docs.kernel.org/admin-guide/cgroup-v2.html#memory)
