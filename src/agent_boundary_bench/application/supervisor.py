"""Application ports and orchestration, independent of communication SDKs."""

import asyncio
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Protocol

from agent_boundary_bench.domain.credit import (
    AnalysisResult,
    AnalysisTask,
    CreditCase,
    Specialist,
    evaluate,
)


class Probe(Protocol):
    """Replaceable span boundary, keeping telemetry outside the kernel."""

    def span(self, name: str) -> AbstractContextManager[object]:
        """Create a scoped observation."""
        ...


class NullProbe:
    """Baseline with no OpenTelemetry API calls."""

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        """Return a no-op scope."""
        yield


@dataclass(frozen=True)
class Invocation:
    """Business output plus separate, explicitly scoped measurements."""

    result: AnalysisResult
    specialist_ms: float
    request_bytes: int = 0
    response_bytes: int = 0
    serialization_ms: float = 0
    transport_ms: float = 0
    remote_calls: int = 0


class Delegate(Protocol):
    """Port implemented by local, HTTP and official A2A clients."""

    async def invoke(self, task: AnalysisTask) -> Invocation:
        """Execute one typed specialist task."""
        ...


@dataclass(frozen=True)
class Execution:
    """Validated supervisor result with per-delegation observations."""

    invocations: tuple[Invocation, ...]
    duration_ms: float
    accepted: bool


async def supervise(
    delegate: Delegate,
    case: CreditCase,
    wait_ms: int,
    parallel: bool,
    timeout: float,
    probe: Probe,
) -> Execution:
    """Run the same three tasks sequentially or concurrently under one deadline."""
    started = perf_counter()
    tasks = [AnalysisTask(specialist, case, wait_ms) for specialist in Specialist]
    with probe.span("supervisor"):
        async with asyncio.timeout(timeout):
            if parallel:
                # TaskGroup cancels sibling delegations after an error.
                async with asyncio.TaskGroup() as group:
                    pending = [group.create_task(delegate.invoke(task)) for task in tasks]
                values = tuple(item.result() for item in pending)
            else:
                values = tuple([await delegate.invoke(task) for task in tasks])
        with probe.span("result.validate"):
            for task, value in zip(tasks, values, strict=True):
                if value.result != evaluate(task):
                    raise ValueError("specialist business result differs from deterministic oracle")
        return Execution(
            values,
            (perf_counter() - started) * 1000,
            all(value.result.eligible for value in values),
        )
