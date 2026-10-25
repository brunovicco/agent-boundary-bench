# Validation record — 2026-10-25

## Status

v0.2.0 is implemented and validated natively: the v0.1 delegation family remains intact and
the official MCP v2 direct, stdio and Streamable HTTP tool-access family is functional. Docker
Compose execution and remote CI acceptance remain pending because this execution environment
has no Docker binary/daemon and no configured Git remote. The connected GitHub account is
`brunovicco`; repository search returned no `agent-boundary-bench`, but this connector exposes
no repository-creation operation. The user-reported macOS Docker host was not mounted into this
isolated Linux workspace. No public release or remote push occurred.

The short smoke/pilot campaigns validate the experiment path and provide bounded observations.
They do not establish sustained capacity, fault isolation or a general architecture ranking.
The full 1,620-round matrices and 1,440-round MCP amplification campaign were not executed.

## Verified commands and quality

- `uv sync --frozen --all-groups` and offline re-sync from the installed cache.
- `uv run abb validate` against exact versioned fixture bodies and hashes.
- `uv run python scripts/quality_gate.py`: PASS.
- 32 pytest tests PASS; branch-aware coverage **92.87%**, with the 80% gate retained.
- Strict Mypy over 28 source/test files and Ruff lint/format PASS.
- Architecture, MCP configuration, governance and vendored-schema checks PASS.
- Bandit reports zero issues; no warnings were hidden to obtain a pass.
- pip-audit reports no known dependency vulnerabilities. The unpublished local package has no PyPI advisory target.
- All six `abb run` scenarios and factorized campaign execution were exercised.
- Reports were regenerated from all five native datasets with schema/count/hash verification.
- k6 2.3.0 `constant-arrival-rate` smoke passed for all six scenarios.
- `uv build` produced the 0.2.0 source distribution and wheel.
- `compose.yaml` parses and contains `http`, `a2a`, `mcp` and `verify`; containers were not executed here.

Tests use real native sockets/pipes and official SDK clients/servers. They cover all six
adapters, 1/16/128 KiB payloads, 0/50/250 ms requested waits, sequential/concurrent execution,
bounded fan-out, context/tool/resource amplification, malformed input, timeout followed by
successful recovery, A2A card/JSON-RPC, MCP discovery/tool/resource calls, W3C parent links,
metadata-only span export, raw-data integrity and report generation. They do not claim upstream
TCK certification or v0.3 fault-injection/recovery validation. Pytest treats warnings as errors.

## Real measurements

The native v0.1 delegation datasets use clean commit
`5eefbd76acd5e410e249ed21ec610b2570ebb932`; MCP v0.2 datasets use clean commit
`cbf803b547b49336215b407ea3661fe33f6f0868`.

| Dataset | Rounds | Offered / successful | Errors | Timeouts | Drops |
|---|---:|---:|---:|---:|---:|
| Delegation repeated pilot | 30 | 1200 / 1200 | 0 | 0 | 0 |
| Delegation workload coverage | 54 | 270 / 270 | 0 | 0 | 0 |
| Delegation rate calibration | 18 | 1350 / 1350 | 0 | 0 | 0 |
| MCP smoke | 24 | 72 / 72 | 0 | 0 | 0 |
| MCP repeated pilot | 120 | 1200 / 1200 | 0 | 0 | 0 |
| Native total | 246 | 4092 / 4092 | 0 | 0 | 0 |

The MCP pilot has five repetitions for every combination of three boundaries, two context
levels, two resource-read levels and OTel off/on. Each round offered 10 requests at 10 RPS.
In the telemetry-off/no-context-copy/no-resource-read condition, median round P50 was 3.110 ms for direct
dispatch, 5.842 ms for stdio and 6.315 ms for Streamable HTTP. These are medians of five
per-round percentiles, not pooled or portable protocol constants.

Supplemental k6 adds 64 measured executions across all six scenarios, plus 18 warmup
executions, with zero errors or dropped iterations. Delegation k6 manifests use clean commit
`c3f573a`; MCP k6 manifests use `4fd93ebc`. The gateway ingress and timing model differ from
the native harness, so those latency samples are not pooled.

[Recorded insights](reports/INSIGHTS.md), [raw datasets](experiments/results/) and the
[reproduction guide](experiments/README.md) preserve outliers and scope. Native manifests
record Python/SDK versions, commit/dirty status, lock hash, OS/CPU/cgroup constraints,
network/pools/workers, seeds/configs, counts, content bytes, hashes and limitations. Image
digests are null for native runs; no nonexistent image measurement is invented.

The MCP host reported Linux 6.18.55 x86_64, AMD EPYC 9V74, nine visible CPUs, cgroup quota
equivalent to eight cores and an 8 GiB memory limit. The v0.1 host reported a Xeon Platinum
8573C under equivalent visible CPU/cgroup constraints. These are host facts, not dedicated
resource claims. Generator and system under test shared each host. MCP stdio worker CPU/RSS
is null because the official high-level client does not expose its child PID through a public API.

## Artifacts and remaining checks

Committed artifacts include raw JSONL/JSON, summary CSV, paired telemetry deltas, measured-span
summaries, deterministic PNG charts, bilingual READMEs, schemas, methodology, compatibility
study and six ADRs. Quality/build logs are under `docs/validation/`. Reports derive exclusively
from raw data; missing or tampered samples are rejected. No LLM, commercial key or real financial
data was used.

Remaining acceptance checks on the user's Docker host:

```bash
docker compose up --build --wait
docker compose --profile tools run --rm verify
docker compose down --remove-orphans
```

After that, create/push the private GitHub repository and let the configured CI run. Longer
isolated repeated campaigns are still required before article-level capacity claims. v0.3 fault
injection, retries, backpressure and resource-isolation treatments remain roadmap work.

The export includes a Git bundle. Restore it with `git clone --origin export
agent-boundary-bench-v0.2.0.bundle agent-boundary-bench`, or fetch the bundle into a clone that
shares this history. The private-only publication helper refuses to overwrite an existing remote
repository. Public visibility requires separate owner authorization.
