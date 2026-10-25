# Contributing

Run `uv sync --frozen --all-groups` and `uv run python scripts/quality_gate.py` before a pull request. Keep strict types, behavior-focused tests and inward dependencies. New protocol code must use public documented APIs and real integration tests. Never weaken checks or replace real protocol tests with mocks to obtain a green build.

Changes to workload semantics, canonical JSON or fixtures require a new fixture/kernel version and regenerated expected results. Document any compatibility impact and ADR. Keep synthetic waits labeled as such. Never check in private data, tokens or `.env` files containing secrets.

Benchmark contributions must include raw records, exact commit/dirty status, versions, environment, topology, seed, warmup, arrival model, errors/drops and repetitions. Keep unexecuted hypotheses and illustrative examples separate. Do not publish shared-runner CI performance as a comparable experiment. Explain missing observations; never fill them with invented values.

Reports and charts must regenerate solely from committed raw observations. State sample sizes and limitations. For telemetry comparisons, match all other settings and preserve repetitions. Independent runs from different machines belong in separate datasets. Public publication of this repository requires the owner's authorization.
