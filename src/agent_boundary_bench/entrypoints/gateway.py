"""Uniform HTTP ingress for independent k6 open-arrival validation."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI

from agent_boundary_bench.application.supervisor import Delegate, NullProbe, supervise
from agent_boundary_bench.benchmark.models import Config
from agent_boundary_bench.benchmark.runtime import runtime
from agent_boundary_bench.domain.credit import fixture
from agent_boundary_bench.observability import Telemetry, TraceMiddleware
from agent_boundary_bench.observability.process import procfs_pid


def create_gateway(config: Config, directory: Path) -> FastAPI:
    """Add the same ingress to all scenarios; do not mix these latencies with native runs."""
    delegate: Delegate
    directory.mkdir(parents=True, exist_ok=True)
    telemetry = (
        Telemetry(directory / "gateway-spans.jsonl", "abb-gateway") if config.telemetry else None
    )
    probe = telemetry or NullProbe()
    case = fixture(config.payload_bytes, config.seed)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        nonlocal delegate
        try:
            async with runtime(config, probe, directory) as (active, _):
                delegate = active
                yield
        finally:
            if telemetry:
                telemetry.close()

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)
    app.add_middleware(TraceMiddleware, telemetry=telemetry)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "procfs_pid": str(procfs_pid())}

    @app.post("/execute")
    async def execute() -> dict[str, object]:
        result = await supervise(
            delegate,
            case,
            config.wait_ms,
            config.parallel,
            config.timeout,
            probe,
            specialist_repetitions=config.specialist_repetitions,
            fanout_limit=config.fanout_limit,
            resilience=config.resilience_policy(),
        )
        return {
            "accepted": result.accepted,
            "results": [asdict(v.result) for v in result.invocations],
            "remote_calls": sum(v.remote_calls for v in result.invocations),
            "tool_calls": sum(v.tool_calls for v in result.invocations),
            "resource_reads": sum(v.resource_reads for v in result.invocations),
            "context_bytes": sum(v.context_bytes for v in result.invocations),
            "attempts": sum(v.attempts for v in result.invocations),
            "retries": sum(v.retries for v in result.invocations),
            "kernel_executions": sum(v.kernel_executions for v in result.invocations),
            "idempotency_hits": sum(v.idempotency_hits for v in result.invocations),
            "injected_failures": sum(v.injected_failures for v in result.invocations),
            "rejections": sum(v.rejections for v in result.invocations),
            "backpressure_wait_ms": sum(v.backpressure_wait_ms for v in result.invocations),
        }

    return app
