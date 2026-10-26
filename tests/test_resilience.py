"""Controlled v0.3 failure, retry, idempotency and backpressure behavior."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from time import perf_counter
from typing import cast

import pytest
from a2a.client import Client
from a2a.client.errors import A2AClientTimeoutError

from agent_boundary_bench.adapters.local import LocalDelegate
from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.resilience import (
    DelegationFailure,
    DelegationMetadata,
    ExecutionController,
    ResiliencePolicy,
    RetryExhaustedError,
)
from agent_boundary_bench.application.supervisor import NullProbe, supervise
from agent_boundary_bench.benchmark.models import Config, Manifest, Sample
from agent_boundary_bench.benchmark.runner import expected_warmup_failures, one, run
from agent_boundary_bench.benchmark.runtime import runtime
from agent_boundary_bench.domain.credit import AnalysisTask, Specialist, evaluate, fixture


def task(wait_ms: int = 0) -> AnalysisTask:
    return AnalysisTask(Specialist.DOCUMENT, fixture(1024), wait_ms)


class TimeoutA2AClient:
    """Minimal public-client substitute that raises the SDK's timeout type."""

    async def send_message(self, request: object) -> AsyncIterator[object]:
        if request is not None:
            raise A2AClientTimeoutError("controlled timeout")
        yield object()


def test_policy_and_metadata_reject_invalid_controls() -> None:
    with pytest.raises(ValueError, match="fault controls"):
        ResiliencePolicy(fault_every=0)
    with pytest.raises(ValueError, match="retry controls"):
        ResiliencePolicy(max_attempts=0)
    with pytest.raises(ValueError, match="queue_capacity"):
        ResiliencePolicy(queue_capacity=1)
    with pytest.raises(ValueError, match="delegation id"):
        DelegationMetadata.create("bad id")
    with pytest.raises(ValueError, match="attempt"):
        DelegationMetadata.create("valid", 0)
    with pytest.raises(ValueError, match="only to delegation"):
        Config(scenario="mcp-inprocess", max_attempts=2)
    assert not expected_warmup_failures(Config(max_attempts=2), [])


async def test_after_commit_idempotency_prevents_duplicate_kernel_execution() -> None:
    policy = ResiliencePolicy(
        fault_mode="after-commit",
        max_attempts=2,
        idempotency=True,
    )
    controller = ExecutionController(policy, NullProbe())
    first = await controller.execute(task(), DelegationMetadata("stable-id", 1))
    assert first.error == "injected_after_commit"
    assert first.result is None
    assert first.kernel_executions == first.injected_failures == 1

    recovered = await controller.execute(task(), DelegationMetadata("stable-id", 2))
    assert recovered.result == evaluate(task())
    assert recovered.kernel_executions == 0
    assert recovered.idempotency_hits == 1

    duplicate = await controller.execute(task(), DelegationMetadata("stable-id", 2))
    assert duplicate.result == recovered.result
    assert duplicate.idempotency_hits == 1

    conflicting_task = AnalysisTask(Specialist.FINANCIAL, fixture(1024))
    conflict = await controller.execute(conflicting_task, DelegationMetadata("stable-id", 2))
    assert conflict.error == "idempotency_conflict"
    assert not conflict.transient
    assert conflict.result is None


async def test_after_commit_without_idempotency_reexecutes_kernel() -> None:
    policy = ResiliencePolicy(fault_mode="after-commit", max_attempts=2)
    controller = ExecutionController(policy, NullProbe())
    first = await controller.execute(task(), DelegationMetadata("duplicate-id", 1))
    recovered = await controller.execute(task(), DelegationMetadata("duplicate-id", 2))
    assert first.error == "injected_after_commit"
    assert first.kernel_executions == 1
    assert recovered.result == evaluate(task())
    assert recovered.kernel_executions == 1
    assert recovered.idempotency_hits == 0


async def test_concurrent_idempotency_executes_kernel_once() -> None:
    controller = ExecutionController(ResiliencePolicy(idempotency=True), NullProbe())
    first, second = await asyncio.gather(
        controller.execute(task(50), DelegationMetadata("concurrent-id", 1)),
        controller.execute(task(50), DelegationMetadata("concurrent-id", 1)),
    )
    assert first.result == second.result == evaluate(task(50))
    assert first.kernel_executions + second.kernel_executions == 1
    assert first.idempotency_hits + second.idempotency_hits == 1


async def test_idempotency_lock_state_is_removed_after_uncached_failure() -> None:
    controller = ExecutionController(
        ResiliencePolicy(
            fault_mode="fail-first",
            max_attempts=1,
            idempotency=True,
        ),
        NullProbe(),
    )
    for index in range(100):
        outcome = await controller.execute(task(), DelegationMetadata(f"failure-{index}", 1))
        assert outcome.error == "injected_fail_first"
    assert not controller._key_locks


async def test_delay_first_does_not_block_idempotent_retry_or_execute_kernel() -> None:
    controller = ExecutionController(
        ResiliencePolicy(
            fault_mode="delay-first",
            fault_delay_ms=50,
            max_attempts=2,
            idempotency=True,
        ),
        NullProbe(),
    )
    delayed = asyncio.create_task(controller.execute(task(), DelegationMetadata("delayed-id", 1)))
    await asyncio.sleep(0.005)
    retry = await controller.execute(task(), DelegationMetadata("delayed-id", 2))
    assert retry.result == evaluate(task())
    assert retry.kernel_executions == 1
    assert not delayed.done()
    first = await delayed
    assert first.error == "injected_delay_first"
    assert first.kernel_executions == 0


async def test_admission_rejects_or_times_out_a_bounded_queue() -> None:
    rejecting = ExecutionController(
        ResiliencePolicy(service_concurrency=1, queue_capacity=0), NullProbe()
    )
    active = asyncio.create_task(rejecting.execute(task(50), DelegationMetadata("active", 1)))
    await asyncio.sleep(0)
    rejected = await rejecting.execute(task(50), DelegationMetadata("rejected", 1))
    assert rejected.error == "overloaded"
    assert rejected.rejections == 1
    assert (await active).result == evaluate(task(50))

    queued = ExecutionController(
        ResiliencePolicy(
            service_concurrency=1,
            queue_capacity=1,
            queue_timeout_ms=1,
        ),
        NullProbe(),
    )
    active = asyncio.create_task(queued.execute(task(50), DelegationMetadata("active-2", 1)))
    await asyncio.sleep(0)
    timed_out = await queued.execute(task(), DelegationMetadata("queued", 1))
    assert timed_out.error == "queue_timeout"
    assert timed_out.rejections == 1
    assert timed_out.backpressure_wait_ms > 0
    await active


async def test_local_retry_modes_preserve_business_result_and_metrics() -> None:
    for fault_mode in ("fail-first", "delay-first", "after-commit"):
        policy = ResiliencePolicy(
            fault_mode=fault_mode,
            fault_delay_ms=25,
            max_attempts=2,
            attempt_timeout=0.005 if fault_mode == "delay-first" else 1,
            idempotency=fault_mode == "after-commit",
        )
        delegate = LocalDelegate(NullProbe(), policy)
        execution = await supervise(
            delegate,
            fixture(1024),
            0,
            False,
            2,
            NullProbe(),
            resilience=policy,
            execution_id=fault_mode,
        )
        assert all(
            value.result == evaluate(task_for(value.result.specialist))
            for value in execution.invocations
        )
        assert all(value.attempts == 2 and value.retries == 1 for value in execution.invocations)
        assert sum(value.injected_failures for value in execution.invocations) == 3
        assert sum(value.kernel_executions for value in execution.invocations) == 3
        if fault_mode == "after-commit":
            assert sum(value.idempotency_hits for value in execution.invocations) == 3


def task_for(specialist: Specialist) -> AnalysisTask:
    return AnalysisTask(specialist, fixture(1024))


async def test_exhausted_retry_is_recorded_with_attempt_metrics() -> None:
    policy = ResiliencePolicy(fault_mode="after-commit", max_attempts=1)
    delegate = LocalDelegate(NullProbe(), policy)
    with pytest.raises(RetryExhaustedError) as captured:
        await supervise(
            delegate,
            fixture(1024),
            0,
            False,
            1,
            NullProbe(),
            resilience=policy,
            execution_id="exhausted",
        )
    assert captured.value.attempts == 1
    assert captured.value.metrics.kernel_executions == 1

    now = perf_counter()
    sample = await one(
        0,
        now,
        now,
        Config(fault_mode="after-commit", max_attempts=1),
        delegate,
        fixture(1024),
        NullProbe(),
    )
    assert sample.status == "error"
    assert sample.error == "injected_after_commit"
    assert sample.attempts == sample.kernel_executions == sample.injected_failures == 1


async def test_expected_warmup_rejection_is_recorded_not_hidden(tmp_path: Path) -> None:
    directory = await run(
        Config(
            rate=5,
            duration=0.2,
            warmup=1,
            wait_ms=50,
            parallel=True,
            service_concurrency=1,
            queue_capacity=0,
        ),
        tmp_path,
    )
    manifest = Manifest.model_validate_json((directory / "manifest.json").read_text())
    sample = Sample.model_validate_json((directory / "samples.jsonl").read_text())
    assert manifest.warmup_succeeded == 0
    assert manifest.warmup_failed == 1
    assert manifest.offered == manifest.completed == 1
    assert manifest.succeeded == 0
    assert sample.status == "error"
    assert sample.error == "overloaded"
    assert sample.rejections == 2


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.parametrize("scenario", ["http", "a2a"])
async def test_remote_after_commit_recovery_is_idempotent(scenario: str, tmp_path: Path) -> None:
    config = Config(
        scenario=scenario,
        fault_mode="after-commit",
        max_attempts=2,
        attempt_timeout=1,
        timeout=5,
        idempotency=True,
    )
    async with runtime(config, NullProbe(), tmp_path) as (delegate, _):
        result = await supervise(
            delegate,
            fixture(1024),
            0,
            False,
            config.timeout,
            NullProbe(),
            resilience=config.resilience_policy(),
            execution_id=f"remote-{scenario}",
        )
    assert all(value.attempts == 2 for value in result.invocations)
    assert all(value.retries == 1 for value in result.invocations)
    assert all(value.remote_calls == 2 for value in result.invocations)
    assert all(value.kernel_executions == 1 for value in result.invocations)
    assert all(value.idempotency_hits == 1 for value in result.invocations)
    assert all(value.injected_failures == 1 for value in result.invocations)


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.parametrize("scenario", ["http", "a2a"])
async def test_remote_delay_uses_application_attempt_deadline(
    scenario: str, tmp_path: Path
) -> None:
    config = Config(
        scenario=scenario,
        fault_mode="delay-first",
        fault_delay_ms=2000,
        max_attempts=2,
        attempt_timeout=1,
        retry_backoff_ms=1500,
        timeout=8,
        idempotency=True,
    )
    async with runtime(config, NullProbe(), tmp_path) as (delegate, _):
        assert isinstance(delegate, RemoteDelegate)
        assert delegate.http.timeout.read == config.timeout
        result = await supervise(
            delegate,
            fixture(1024),
            0,
            True,
            config.timeout,
            NullProbe(),
            resilience=config.resilience_policy(),
            execution_id=f"remote-delay-{scenario}",
        )
    assert all(value.attempts == 2 for value in result.invocations)
    assert all(value.retries == 1 for value in result.invocations)
    assert all(value.remote_calls == 2 for value in result.invocations)
    assert all(value.kernel_executions == 1 for value in result.invocations)
    assert all(value.injected_failures == 1 for value in result.invocations)


async def test_a2a_sdk_timeout_is_a_typed_transient_failure() -> None:
    delegate = RemoteDelegate("http://unused", "a2a", NullProbe(), False, 2)
    delegate.a2a = cast(Client, TimeoutA2AClient())
    try:
        with pytest.raises(DelegationFailure) as captured:
            await delegate.invoke(task(), delegation_id="timeout-id", attempt=1)
    finally:
        await delegate.close()
    assert captured.value.reason == "transport_timeout"
    assert captured.value.transient
