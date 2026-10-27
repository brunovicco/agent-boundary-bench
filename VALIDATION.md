# Validation record — 2026-10-27

## Status

v0.2.0 is implemented and validated on Linux and macOS. The v0.1 delegation family remains
intact, and the official MCP v2 direct, stdio and Streamable HTTP tool-access family is
functional. Native quality gates pass on both platforms. Docker Compose was built and executed
successfully on the macOS Docker host: the HTTP, A2A and MCP services became healthy, the
verification container confirmed functional equivalence, and Compose shut down cleanly.

The canonical repository is public at
[brunovicco/agent-boundary-bench](https://github.com/brunovicco/agent-boundary-bench). GitHub
Actions passed the native quality and Compose functional release gate at commit `99a5979` in
[run 40230391324](https://github.com/brunovicco/agent-boundary-bench/actions/runs/40230391324).
Shared-runner timings are never promoted as comparable benchmark results.

The unreleased `0.3.0.dev0` line additionally has controlled resilience/backpressure smoke
evidence and a validated Docker resource-isolation smoke. The latter ran both generous and
constrained cgroup v2 profiles from clean commit `d910a570`; it is explicitly separate from the
v0.2.0 release claim and from sustained-capacity evidence.

The short smoke/pilot campaigns validate the experimental path and provide bounded observations.
They do not establish sustained capacity, fault isolation or a general architecture ranking.
The full 1,620-round matrices and 1,440-round MCP amplification campaign were not executed.

## Verified commands and quality

### Native Linux validation

- `uv sync --frozen --all-groups` and offline re-sync from the installed cache: PASS.
- `uv run abb validate` against exact versioned fixture bodies and hashes: PASS.
- `uv run python scripts/quality_gate.py`: PASS.
- 32 pytest tests PASS on Python 3.12.14; branch-aware coverage **92.87%**.
- Strict Mypy over 28 source/test files and Ruff lint/format: PASS.
- Architecture, MCP configuration, governance and vendored-schema checks: PASS.
- Bandit reports zero issues; no warnings were hidden to obtain a pass.
- pip-audit reports no known dependency vulnerabilities. The unpublished local package has no
  PyPI advisory target.
- All six `abb run` scenarios and factorized campaign execution were exercised.
- Reports were regenerated from all five native datasets with schema/count/hash verification.
- k6 2.3.0 `constant-arrival-rate` smoke passed for all six scenarios.
- `uv build` produced the 0.2.0 source distribution and wheel.

### Native macOS validation

The repository restored from the complete Git bundle was validated independently on macOS:

- `uv sync --frozen --all-groups`: PASS using CPython 3.12.13.
- `uv run abb validate`: PASS for the 1 KiB, 16 KiB and 128 KiB fixtures and expected SHA-256 hashes.
- `uv run python scripts/quality_gate.py`: PASS.
- 32 pytest tests PASS in 94.75 seconds; branch-aware coverage **92.40%**.
- The 80% coverage gate remained enforced.
- Mypy, Ruff, architecture checks, MCP configuration validation, governance checks and vendored
  schema validation: PASS.
- Bandit reports zero issues.
- pip-audit reports no known dependency vulnerabilities.

The small coverage difference between Linux and macOS is in platform-specific process/resource
sampling paths. It does not represent disabled tests or a reduced coverage threshold.

### Docker Compose validation on macOS

The following commands completed successfully:

```bash
docker compose up --build --wait
docker compose --profile tools run --rm verify
docker compose down --remove-orphans
```

Observed results:

- The pinned `python:3.12.14-slim-bookworm` base image was resolved and the
  `agent-boundary-bench:0.2.0` image built successfully.
- `http`, `a2a` and `mcp` containers all reached `healthy` status.
- The verification container completed with:
  `HTTP, A2A and MCP Streamable HTTP services are functionally equivalent`.
- The three service containers and the Compose network were removed cleanly.
- Commit `99a5979` replaced the package-loading health command with a lightweight standard-library
  HTTP probe after the first public CI run exposed a runner-speed-dependent false negative.

This validates container construction, health checks, service wiring and business-result
equivalence on the tested same-host Docker topology. It is not a container performance campaign,
cross-host network test or evidence of failure isolation.

### v0.3 resource-isolation validation on macOS

The resource-isolation overlay was built and executed on Docker Desktop. The complete native
quality gate passed with 53 tests and 91.62% branch-aware coverage before the final image build.
Both 12-round profiles passed strict validation of raw hashes/counts, observed cgroup v2 limits,
image digest, full expected commit and clean-worktree provenance.

| Profile | Remote specialist | Rounds | Offered/succeeded | Sampling failures |
|---|---|---:|---:|---:|
| constrained | 0.25 CPU, 256 MiB | 12 | 60/60 | 0/192 |
| generous | 1 CPU, 512 MiB | 12 | 60/60 | 0/212 |

The harness retained one CPU and 512 MiB in both profiles. All 24 warmups succeeded; no error,
timeout, drop, memory-pressure event or OOM kill was observed. Every manifest records commit
`d910a57008c43636c38f4324dd398127f0f781de`, `git_dirty=false`, lock hash and image digest
`sha256:7a342493c90b9ab08add17ee9618acf1147bc7cc1f04e48ba8fbfe6178043f16`.

The A2A CPU-plus-memory condition produced the strongest bounded observation: constrained P50
1,053.340 ms and 2.787763 seconds of specialist throttling versus generous P50 104.917 ms and
zero throttling. This is one five-request round per profile, not a repeated effect estimate or
portable protocol result. See the
[dedicated validation record](docs/validation/v0.3-resource-isolation.md).

### Public GitHub Actions validation

The first public workflow execution at commit `742ef24` provided useful independent evidence:

- The `quality` job passed dependency installation, strict quality gates, fixture validation and
  functional smoke runs for all six scenarios.
- The `compose` image build succeeded and HTTP/A2A became healthy, but MCP exceeded the original
  health-probe budget on the shared runner. The verification step was correctly skipped.
- The same topology had passed on macOS. Investigation identified the health probe itself as
  unnecessarily expensive because it loaded the complete CLI package for every attempt.
- Commit `99a5979` changed only the Compose health command to a lightweight `urllib.request`
  probe. The corrected topology then passed locally with all three services healthy and the
  equivalence verifier successful.
- The follow-up public workflow
  [run 40230391324](https://github.com/brunovicco/agent-boundary-bench/actions/runs/40230391324)
  completed successfully at `99a5979`; both `quality` and `compose` passed.

See the [quality workflow](https://github.com/brunovicco/agent-boundary-bench/actions/workflows/quality.yml)
for the live status. CI remains a functional gate; its latency is not benchmark evidence.

Tests use real native sockets/pipes and official SDK clients/servers. They cover all six
adapters, 1/16/128 KiB payloads, 0/50/250 ms requested waits, sequential/concurrent execution,
bounded fan-out, context/tool/resource amplification, malformed input, timeout followed by
successful recovery, A2A card/JSON-RPC, MCP discovery/tool/resource calls, W3C parent links,
metadata-only span export, raw-data integrity and report generation. They do not claim upstream
TCK certification or completion of the repeated v0.3 campaign matrices. Pytest treats warnings
as errors.

## Real measurements

The native v0.1 delegation datasets use clean commit
`5eefbd76acd5e410e249ed21ec610b2570ebb932`; MCP v0.2 datasets use clean commit
`cbf803b547b49336215b407ea3661fe33f6f0868`.

| Dataset | Rounds | Offered / successful | Errors | Timeouts | Drops |
| --- | ---: | ---: | ---: | ---: | ---: |
| Delegation repeated pilot | 30 | 1200 / 1200 | 0 | 0 | 0 |
| Delegation workload coverage | 54 | 270 / 270 | 0 | 0 | 0 |
| Delegation rate calibration | 18 | 1350 / 1350 | 0 | 0 | 0 |
| MCP smoke | 24 | 72 / 72 | 0 | 0 | 0 |
| MCP repeated pilot | 120 | 1200 / 1200 | 0 | 0 | 0 |
| Native total | 246 | 4092 / 4092 | 0 | 0 | 0 |

The MCP pilot has five repetitions for every combination of three boundaries, two context
levels, two resource-read levels and OTel off/on. Each round offered 10 requests at 10 RPS.
In the telemetry-off/no-context-copy/no-resource-read condition, median round P50 was 3.110 ms
for direct dispatch, 5.842 ms for stdio and 6.315 ms for Streamable HTTP. These are medians of
five per-round percentiles, not pooled or portable protocol constants.

Supplemental k6 adds 64 measured executions across all six scenarios, plus 18 warmup
executions, with zero errors or dropped iterations. Delegation k6 manifests use clean commit
`c3f573a`; MCP k6 manifests use `4fd93ebc`. The gateway ingress and timing model differ from
the native harness, so those latency samples are not pooled.

Unreleased v0.3 development evidence adds 45 resilience/timeout/backpressure smoke rounds and
24 resource-isolation rounds. The isolation dataset completed 120/120 requests and 24/24 warmups
with zero errors, timeouts, drops or sampling failures. It remains separate from the v0.1/v0.2
native totals above and from any sustained-capacity claim.

[Recorded insights](reports/INSIGHTS.md), [raw datasets](experiments/results/) and the
[reproduction guide](experiments/README.md) preserve outliers and scope. Native manifests
record Python/SDK versions, commit/dirty status, lock hash, OS/CPU/cgroup constraints,
network/pools/workers, seeds/configs, counts, content bytes, hashes and limitations. Image
digests are null for native runs; no nonexistent image measurement is invented.

The MCP benchmark host reported Linux 6.18.55 x86_64, AMD EPYC 9V74, nine visible CPUs, cgroup
quota equivalent to eight cores and an 8 GiB memory limit. The v0.1 host reported a Xeon
Platinum 8573C under equivalent visible CPU/cgroup constraints. These are host facts, not
dedicated resource claims. Generator and system under test shared each host. MCP stdio worker
CPU/RSS is null because the official high-level client does not expose its child PID through a
public API. The earlier v0.2 macOS execution was functional validation and is not pooled with
Linux benchmark measurements. The separately labeled v0.3 isolation smoke remains scoped to its
Docker Desktop environment.

## Artifacts and remaining checks

Committed artifacts include raw JSONL/JSON, summary CSV, paired telemetry deltas, measured-span
summaries, deterministic PNG charts, bilingual READMEs, schemas, methodology, compatibility
study and versioned ADRs. Quality/build logs are under `docs/validation/`. Reports derive exclusively
from raw data; missing or tampered samples are rejected. No LLM, commercial key or real
financial data was used.

Remaining work before claiming broader experimental validation:

1. Run longer isolated and repeated campaigns before article-level capacity conclusions.
2. Execute the complete repeated v0.3 matrices, including both 180-round resource profiles.
3. Add cross-host network fault and fixed-total-resource-budget treatments where justified.

The complete Git history can be restored with:

```bash
git clone --origin export agent-boundary-bench-v0.2.0.bundle agent-boundary-bench
```

The bundle is a recovery/export artifact, not the normal Git remote. The public repository was
created and populated by the owner on 2026-10-25.
