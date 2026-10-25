# Validation record — 2026-10-25

Implementation uses Python 3.12.14 and uv 0.13.4. The complete project quality gate passed:
18 pytest tests, 94.16% branch-aware coverage, strict Mypy, Ruff lint/format, architecture,
MCP/config/governance and vendored-schema checks, Bandit and pip-audit. pip-audit found no
known dependency vulnerabilities; the unpublished local package itself is not a PyPI advisory target.

Real protocol tests cover all three adapters, 1/16/128 KiB payloads, 0/50/250 ms workloads,
sequential/concurrent orchestration, malformed inputs, deadlines and a subsequent successful
call, official A2A card/JSON-RPC interaction, W3C parent links and metadata-only spans.
Reports reject raw sample hash mismatches and test paired telemetry/span summaries.

The first k6 A2A smoke also ran with no errors or dropped iterations. It predates the clean
measurement commit and is not included as curated evidence. Committed pilot/matrix evidence
and final environment limitations will be recorded after those campaigns complete.

Docker/Compose runtime validation and remote GitHub Actions have not run in this environment.
Docker is not installed and no daemon socket is available. The Compose YAML parses, and the
pinned Python image digest was resolved from Docker Hub. This is not a container execution claim.

The GitHub connection can inspect and modify existing repositories, but exposes no creation
operation. The terminal has no authenticated Git remote credentials. No remote repository has
been created or made public. A private-only publication script is included for authenticated use.
