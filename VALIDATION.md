# Validation record — 2026-10-25

## Status

The native laboratory is implemented and validated. Docker/Compose execution and remote CI
acceptance remain pending because this environment has no Docker binary/daemon and no GitHub
repository-creation operation or authenticated Git remote. No public release or remote push
was performed. The full 1620-round campaign was not executed. This is not a claim of complete
container validation, sustained capacity, recovery or isolation.

## Verified commands and quality

- `uv sync --frozen --all-groups` and `UV_OFFLINE=1 uv sync --frozen --all-groups`.
- `uv run abb validate` against exact versioned fixture bodies/hashes.
- `uv run python scripts/quality_gate.py`: PASS after `uv run coverage erase`.
- 18 pytest tests PASS; clean branch-aware coverage **93.89%**, 80% gate retained.
- Strict Mypy, Ruff lint/format, architecture, MCP/config/governance and vendored-schema checks PASS.
- Bandit: no issues; no warning filtering was added to obtain a pass.
- pip-audit: no known dependency vulnerabilities. The unpublished local package has no PyPI advisory target.
- `uv run abb run --scenario local|http|a2a --profile smoke` and campaign execution.
- `uv run abb campaign --config experiments/pilot.json ...`, coverage-smoke and calibration configurations.
- `uv run abb report --input ... --output ...` for all three committed native datasets.
- `uv run python scripts/k6_smoke.py --scenario local|http|a2a ...`: PASS, actual k6 2.3.0.
- `uv build`: source distribution and wheel built successfully.
- Compose YAML parsed; Python base image digest resolved from Docker Hub. These checks do not execute containers.

The tests use real native sockets and official SDK clients/servers. They cover all adapters,
1/16/128 KiB payloads, 0/50/250 ms requested waits, sequential/concurrent execution, malformed
input, timeout and a subsequent successful call, A2A card/JSON-RPC exchanges, W3C parent links,
metadata-only span export, raw-data integrity and telemetry/report generation. Tests do not
claim upstream TCK certification or v0.3 failure-recovery validation. Pytest treats warnings as errors.

## Real measurements

All native campaigns used clean implementation commit `5eefbd76acd5e410e249ed21ec610b2570ebb932`:

| Dataset | Rounds | Offered / successful | Errors | Timeouts | Drops |
|---|---:|---:|---:|---:|---:|
| Repeated pilot | 30 | 1200 / 1200 | 0 | 0 | 0 |
| Workload coverage smoke | 54 | 270 / 270 | 0 | 0 | 0 |
| Rate calibration | 18 | 1350 / 1350 | 0 | 0 | 0 |
| Native total | 102 | 2820 / 2820 | 0 | 0 | 0 |

The pilot has five repetitions for each of six architecture/telemetry conditions, 40 samples
per round. Coverage/calibration have one repetition and are explicitly not full campaigns.
All configured 5, 20 and 50 RPS rates were exercised in calibration, without a sustained
saturation conclusion. k6 added 33 measured executions (11 per scenario), plus 9 warmup
executions, with zero errors/dropped iterations. Its independent clean commit and actual
versions/counts are in `experiments/results/k6/*/k6-manifest.json`.

[Recorded insights](reports/INSIGHTS.md), [raw datasets](experiments/results/) and
[reproduction guide](experiments/README.md) preserve outliers and scope. Native manifests
record Python/SDK versions, commit/dirty status, lock hash, OS/CPU/cgroup constraints,
network/pools/workers, seeds/configs, counts, body bytes, hashes and explicit limitations.
Image digests are null for native runs; no nonexistent image measurement is invented.

Environment: Linux 6.18.55, x86_64, reported Xeon Platinum 8573C, 9 visible CPUs,
cgroup CPU quota equivalent to 8 cores, 8 GiB cgroup memory limit. These are reported host
facts, not a claim of dedicated resources. Generator and system under test share this host.
The mounted procfs uses a parent PID namespace; the sampler explicitly resolves visible PIDs.

## Artifacts and remaining checks

Committed raw JSONL/JSON, summary CSV, paired telemetry deltas, measured-span summaries,
PNG charts, English/Portuguese READMEs, schemas, methodology, compatibility study and four ADRs.
Quality/build logs are under `docs/validation/`. Reports derive exclusively from these raw data;
missing or tampered samples are rejected. No LLM or commercial key was used.

Remaining acceptance: execute `docker compose up --build --wait` and the Compose `verify`
service on a Docker host, create/push the private GitHub repository and run its configured CI.
Then run longer isolated/repeated capacity experiments before article-level performance claims.
The full matrix's measurement windows alone require 13.5 hours, plus startup/warmup.
MCP tooling, generalized fan-out/context amplification and later failure/isolation experiments
remain the documented v0.2/v0.3 roadmap.

The export includes a Git bundle. Restore it with `git clone --origin export
agent-boundary-bench.bundle agent-boundary-bench`, enter that clone, then use the documented
private-only publication script if GitHub CLI authentication is available. An existing remote
repository is never overwritten. Public visibility requires separate owner authorization.
