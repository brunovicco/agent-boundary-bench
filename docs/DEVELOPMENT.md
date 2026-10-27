# Development

Run all commands from the repository root.

```bash
uv sync --frozen --all-groups
uv run abb validate
uv run python scripts/quality_gate.py
```

The gate includes lock consistency, Ruff lint/format, strict Mypy, pytest with 80% minimum
branch-aware coverage, architecture/config/governance checks, Bandit and dependency audit.
Tests include subprocess and actual HTTP/A2A/MCP traffic over sockets, stdio and direct dispatch; coverage captures supported child processes.
Warnings are errors in pytest. No external model, collector, database or credential is required.
Dependency auditing needs network access; application workloads work offline after installation.

Use `uv run abb --help`, the README and docs/METHODOLOGY.md for execution options.
The Dockerfile has a real default HTTP specialist command and a non-root runtime user.
Compose runs equivalent HTTP, A2A and MCP Streamable HTTP workers and provides a functional verification service.
The optional `compose.isolation.yaml` overlay and its evidence validator are documented in
`docs/RESOURCE_ISOLATION.md`; recreate service containers when changing resource profiles.

Generated Codex settings/hooks/skills are retained from the selected harness. Review and trust
them in your own environment before activation. Changes to experimental semantics require
new fixtures/ADRs and a clearly separated result dataset.
