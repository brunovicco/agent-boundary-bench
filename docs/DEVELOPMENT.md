# Development

Run all commands from the repository root.

```bash
uv sync --frozen --all-groups
uv run abb validate
uv run python scripts/quality_gate.py
```

The gate includes lock consistency, Ruff lint/format, strict Mypy, pytest with 80% minimum
branch-aware coverage, architecture/config/governance checks, Bandit and dependency audit.
Tests include subprocess and actual HTTP/A2A traffic; coverage captures child processes.
Warnings are errors in pytest. No external model, collector, database or credential is required.
Dependency auditing needs network access; application workloads work offline after installation.

Use `uv run abb --help`, the README and docs/METHODOLOGY.md for execution options.
The Dockerfile has a real default HTTP specialist command and a non-root runtime user.
Compose runs an equivalent HTTP and A2A worker and provides a functional verification service.

Generated Codex settings/hooks/skills are retained from the selected harness. Review and trust
them in your own environment before activation. Changes to experimental semantics require
new fixtures/ADRs and a clearly separated result dataset.
