"""Application ports and orchestration, independent of communication SDKs."""

import asyncio
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager, suppress
from dataclasses import dataclass, replace
from time import perf_counter
from typing import Protocol
from uuid import uuid4

from agent_boundary_bench.application.resilience import (
    AttemptMetrics,
    DelegationFailure,
    DelegationMetadata,
    ResiliencePolicy,
    RetryExhaustedError,
    RetryTimeoutError,
    add_metrics,
    selected_for_fault,
)
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
    tool_calls: int = 0
    resource_reads: int = 0
    context_bytes: int = 0
    attempts: int = 1
    retries: int = 0
    kernel_executions: int = 1
    idempotency_hits: int = 0
    injected_failures: int = 0
    rejections: int = 0
    backpressure_wait_ms: float = 0.0


class Delegate(Protocol):
    """Port implemented by local, HTTP and official A2A clients."""

    async def invoke(
        self,
        task: AnalysisTask,
        *,
        delegation_id: str | None = None,
        attempt: int = 1,
    ) -> Invocation:
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
    *,
    specialist_repetitions: int = 1,
    fanout_limit: int = 64,
    resilience: ResiliencePolicy | None = None,
    execution_id: str | None = None,
) -> Execution:
    """Run a deterministic fan-out/fan-in workload under one shared deadline."""
    if specialist_repetitions < 1:
        raise ValueError("specialist_repetitions must be positive")
    if fanout_limit < 1:
        raise ValueError("fanout_limit must be positive")
    started = perf_counter()
    policy = resilience or ResiliencePolicy()
    base_id = execution_id or uuid4().hex
    tasks = [
        AnalysisTask(specialist, case, wait_ms)
        for _ in range(specialist_repetitions)
        for specialist in Specialist
    ]

    async def invoke(position: int, task: AnalysisTask) -> Invocation:
        if not policy.enabled:
            return await delegate.invoke(task)
        delegation_id = f"{base_id}:{position}"
        cumulative = AttemptMetrics()
        last_reason = "unknown"

        async def call_attempt(attempt: int) -> Invocation:
            operation = asyncio.create_task(
                delegate.invoke(
                    task,
                    delegation_id=delegation_id,
                    attempt=attempt,
                )
            )
            try:
                done, _ = await asyncio.wait((operation,), timeout=policy.attempt_timeout)
            except asyncio.CancelledError:
                operation.cancel()
                with suppress(BaseException):
                    await operation
                raise
            if operation not in done:
                operation.cancel()
                observed = AttemptMetrics()
                try:
                    await operation
                except DelegationFailure as exc:
                    observed = exc.metrics
                except asyncio.CancelledError:
                    pass
                injected = int(
                    policy.fault_mode == "delay-first"
                    and selected_for_fault(
                        policy,
                        DelegationMetadata(delegation_id, attempt),
                    )
                )
                raise DelegationFailure(
                    "attempt_timeout",
                    transient=True,
                    metrics=add_metrics(
                        observed,
                        AttemptMetrics(injected_failures=injected),
                    ),
                )
            return operation.result()

        for attempt in range(1, policy.max_attempts + 1):
            try:
                with probe.span("retry.attempt"):
                    value = await call_attempt(attempt)
            except DelegationFailure as exc:
                cumulative = add_metrics(cumulative, exc.metrics)
                last_reason = exc.reason
                if not exc.transient or attempt == policy.max_attempts:
                    failure_type = (
                        RetryTimeoutError
                        if exc.reason in ("attempt_timeout", "transport_timeout")
                        else RetryExhaustedError
                    )
                    raise failure_type(last_reason, attempt, cumulative) from exc
                if policy.retry_backoff_ms:
                    with probe.span("retry.backoff"):
                        await asyncio.sleep(policy.retry_backoff_ms / 1000)
                continue
            except TimeoutError as exc:
                last_reason = "attempt_timeout"
                if attempt == policy.max_attempts:
                    raise RetryTimeoutError(last_reason, attempt, cumulative) from exc
                if policy.retry_backoff_ms:
                    with probe.span("retry.backoff"):
                        await asyncio.sleep(policy.retry_backoff_ms / 1000)
                continue
            successful = AttemptMetrics(
                remote_calls=value.remote_calls,
                request_bytes=value.request_bytes,
                response_bytes=value.response_bytes,
                serialization_ms=value.serialization_ms,
                transport_ms=value.transport_ms,
                specialist_ms=value.specialist_ms,
                kernel_executions=value.kernel_executions,
                idempotency_hits=value.idempotency_hits,
                injected_failures=value.injected_failures,
                rejections=value.rejections,
                backpressure_wait_ms=value.backpressure_wait_ms,
            )
            cumulative = add_metrics(cumulative, successful)
            return replace(
                value,
                specialist_ms=cumulative.specialist_ms,
                request_bytes=cumulative.request_bytes,
                response_bytes=cumulative.response_bytes,
                serialization_ms=cumulative.serialization_ms,
                transport_ms=cumulative.transport_ms,
                remote_calls=cumulative.remote_calls,
                attempts=attempt,
                retries=attempt - 1,
                kernel_executions=cumulative.kernel_executions,
                idempotency_hits=cumulative.idempotency_hits,
                injected_failures=cumulative.injected_failures,
                rejections=cumulative.rejections,
                backpressure_wait_ms=cumulative.backpressure_wait_ms,
            )
        raise AssertionError("positive max_attempts must return or raise")

    with probe.span("supervisor"):
        async with asyncio.timeout(timeout):
            if parallel:
                semaphore = asyncio.Semaphore(fanout_limit)

                async def bounded(position: int, task: AnalysisTask) -> Invocation:
                    async with semaphore:
                        return await invoke(position, task)

                # TaskGroup cancels sibling delegations after an error and retains
                # the deterministic task order through the handles below.
                async with asyncio.TaskGroup() as group:
                    pending = [
                        group.create_task(bounded(position, task))
                        for position, task in enumerate(tasks)
                    ]
                values = tuple(item.result() for item in pending)
            else:
                values = tuple(
                    [await invoke(position, task) for position, task in enumerate(tasks)]
                )
        with probe.span("result.validate"):
            for task, value in zip(tasks, values, strict=True):
                if value.result != evaluate(task):
                    raise ValueError("specialist business result differs from deterministic oracle")
        return Execution(
            values,
            (perf_counter() - started) * 1000,
            all(value.result.eligible for value in values),
        )
