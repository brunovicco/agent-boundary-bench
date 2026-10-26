"""Controlled failure, admission and idempotency treatments for delegation experiments."""

import asyncio
import hashlib
from collections import OrderedDict
from contextlib import AbstractContextManager
from dataclasses import asdict, dataclass, replace
from time import monotonic, perf_counter
from typing import Literal, Protocol
from uuid import uuid4

from agent_boundary_bench.domain.credit import AnalysisResult, AnalysisTask, canonical, execute

FaultMode = Literal["none", "fail-first", "delay-first", "after-commit"]


class SpanProbe(Protocol):
    """Minimal observation port required by the resilience controller."""

    def span(self, name: str) -> AbstractContextManager[object]:
        """Create a scoped observation."""
        ...


@dataclass(frozen=True)
class ResiliencePolicy:
    """Explicit controls shared by the client retry and specialist treatments."""

    fault_mode: FaultMode = "none"
    fault_every: int = 1
    fault_delay_ms: int = 100
    max_attempts: int = 1
    attempt_timeout: float = 5.0
    retry_backoff_ms: int = 0
    idempotency: bool = False
    idempotency_capacity: int = 10_000
    idempotency_ttl_seconds: float = 300.0
    service_concurrency: int = 0
    queue_capacity: int = 0
    queue_timeout_ms: int = 1000

    def __post_init__(self) -> None:
        """Reject invalid direct construction outside the Pydantic benchmark boundary."""
        if self.fault_every < 1 or self.fault_delay_ms < 1:
            raise ValueError("fault controls must be positive")
        if not 1 <= self.max_attempts <= 8 or self.attempt_timeout <= 0:
            raise ValueError("retry controls are outside supported bounds")
        if self.retry_backoff_ms < 0:
            raise ValueError("retry_backoff_ms must not be negative")
        if self.idempotency_capacity < 1 or self.idempotency_ttl_seconds <= 0:
            raise ValueError("idempotency bounds must be positive")
        if self.service_concurrency < 0 or self.queue_capacity < 0:
            raise ValueError("admission bounds must not be negative")
        if self.service_concurrency == 0 and self.queue_capacity:
            raise ValueError("queue_capacity requires service_concurrency")
        if self.queue_timeout_ms < 1:
            raise ValueError("queue_timeout_ms must be positive")

    @property
    def enabled(self) -> bool:
        """Keep the v0.2 baseline path free of resilience treatment overhead."""
        return (
            self.fault_mode != "none"
            or self.max_attempts != 1
            or self.idempotency
            or self.service_concurrency != 0
        )


@dataclass(frozen=True)
class DelegationMetadata:
    """Application metadata retained across retries but excluded from the domain contract."""

    delegation_id: str
    attempt: int = 1

    @classmethod
    def create(cls, delegation_id: str | None = None, attempt: int = 1) -> "DelegationMetadata":
        """Validate untrusted transport metadata and supply a bounded local identifier."""
        value = delegation_id or uuid4().hex
        if not value or len(value) > 160 or any(char.isspace() for char in value):
            raise ValueError("invalid delegation id")
        if attempt < 1 or attempt > 32:
            raise ValueError("attempt must be between 1 and 32")
        return cls(value, attempt)


@dataclass(frozen=True)
class ControlOutcome:
    """Specialist result or an intentional failure with directly observed counters."""

    result: AnalysisResult | None = None
    specialist_ms: float = 0.0
    error: str | None = None
    transient: bool = False
    kernel_executions: int = 0
    idempotency_hits: int = 0
    injected_failures: int = 0
    rejections: int = 0
    backpressure_wait_ms: float = 0.0


@dataclass(frozen=True)
class AttemptMetrics:
    """Measurements retained even when one boundary attempt fails."""

    remote_calls: int = 0
    request_bytes: int = 0
    response_bytes: int = 0
    serialization_ms: float = 0.0
    transport_ms: float = 0.0
    specialist_ms: float = 0.0
    kernel_executions: int = 0
    idempotency_hits: int = 0
    injected_failures: int = 0
    rejections: int = 0
    backpressure_wait_ms: float = 0.0


class DelegationFailure(RuntimeError):
    """Typed adapter failure used by the bounded retry policy."""

    def __init__(
        self,
        reason: str,
        *,
        transient: bool,
        metrics: AttemptMetrics | None = None,
    ) -> None:
        """Retain retry classification and partial measurements."""
        super().__init__(reason)
        self.reason = reason
        self.transient = transient
        self.metrics = metrics or AttemptMetrics()


class RetryFailure(RuntimeError):
    """Base final failure preserving all completed attempt observations."""

    def __init__(self, reason: str, attempts: int, metrics: AttemptMetrics) -> None:
        """Retain the terminal reason, attempt count and cumulative measurements."""
        super().__init__(reason)
        self.reason = reason
        self.attempts = attempts
        self.metrics = metrics


class RetryTimeoutError(RetryFailure, TimeoutError):
    """A retry sequence whose last classified failure was an attempt timeout."""


class RetryExhaustedError(RetryFailure):
    """A terminal non-timeout failure or an exhausted transient retry sequence."""


@dataclass(frozen=True)
class _CacheEntry:
    result: AnalysisResult
    task_sha256: str
    expires_at: float


@dataclass
class _KeyLock:
    """Reference-counted per-key lock removable after uncached failures."""

    lock: asyncio.Lock
    users: int = 0


class ExecutionController:
    """Per-worker deterministic fault, admission and bounded idempotency state."""

    def __init__(self, policy: ResiliencePolicy, probe: SpanProbe) -> None:
        """Create worker-local bounded state for one declared policy."""
        self.policy = policy
        self.probe = probe
        self._condition = asyncio.Condition()
        self._active = 0
        self._waiting = 0
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()
        self._key_locks: dict[str, _KeyLock] = {}

    def _selected_for_fault(self, metadata: DelegationMetadata) -> bool:
        return selected_for_fault(self.policy, metadata)

    async def _admit(self) -> tuple[bool, float, str | None]:
        if self.policy.service_concurrency == 0:
            return True, 0.0, None
        started = perf_counter()
        async with self._condition:
            if self._active >= self.policy.service_concurrency:
                if self._waiting >= self.policy.queue_capacity:
                    return False, 0.0, "overloaded"
                self._waiting += 1
                timed_out = False
                try:
                    with self.probe.span("backpressure.wait"):
                        async with asyncio.timeout(self.policy.queue_timeout_ms / 1000):
                            while self._active >= self.policy.service_concurrency:
                                await self._condition.wait()
                except TimeoutError:
                    timed_out = True
                finally:
                    self._waiting -= 1
                if timed_out:
                    return False, (perf_counter() - started) * 1000, "queue_timeout"
            self._active += 1
        return True, (perf_counter() - started) * 1000, None

    async def _release(self) -> None:
        if self.policy.service_concurrency == 0:
            return
        async with self._condition:
            self._active -= 1
            self._condition.notify(1)

    def _cached(
        self,
        delegation_id: str,
        task_sha256: str,
    ) -> tuple[AnalysisResult | None, bool]:
        entry = self._cache.get(delegation_id)
        if entry is None:
            return None, False
        if entry.expires_at <= monotonic():
            self._cache.pop(delegation_id, None)
            return None, False
        if entry.task_sha256 != task_sha256:
            return None, True
        self._cache.move_to_end(delegation_id)
        return entry.result, False

    def _store(self, delegation_id: str, task_sha256: str, result: AnalysisResult) -> None:
        self._cache[delegation_id] = _CacheEntry(
            result,
            task_sha256,
            monotonic() + self.policy.idempotency_ttl_seconds,
        )
        self._cache.move_to_end(delegation_id)
        while len(self._cache) > self.policy.idempotency_capacity:
            evicted, _ = self._cache.popitem(last=False)
            state = self._key_locks.get(evicted)
            if state is not None and state.users == 0 and not state.lock.locked():
                self._key_locks.pop(evicted, None)

    async def execute(
        self,
        task: AnalysisTask,
        metadata: DelegationMetadata,
    ) -> ControlOutcome:
        """Apply one declared treatment and execute the unchanged domain kernel."""
        admitted, wait_ms, rejection = await self._admit()
        if not admitted:
            return ControlOutcome(
                error=rejection,
                transient=True,
                rejections=1,
                backpressure_wait_ms=wait_ms,
            )
        try:
            if not self.policy.enabled:
                started = perf_counter()
                result = await execute(task)
                return ControlOutcome(
                    result=result,
                    specialist_ms=(perf_counter() - started) * 1000,
                    kernel_executions=1,
                    backpressure_wait_ms=wait_ms,
                )
            selected = self._selected_for_fault(metadata)
            if selected and self.policy.fault_mode == "fail-first":
                with self.probe.span("fault.inject.fail_first"):
                    return ControlOutcome(
                        error="injected_fail_first",
                        transient=True,
                        injected_failures=1,
                        backpressure_wait_ms=wait_ms,
                    )
            if selected and self.policy.fault_mode == "delay-first":
                with self.probe.span("fault.inject.delay_first"):
                    await asyncio.sleep(self.policy.fault_delay_ms / 1000)
                return ControlOutcome(
                    error="injected_delay_first",
                    transient=True,
                    injected_failures=1,
                    backpressure_wait_ms=wait_ms,
                )
            if not self.policy.idempotency:
                return await self._execute_uncached(task, metadata, wait_ms)
            state = self._key_locks.setdefault(
                metadata.delegation_id,
                _KeyLock(asyncio.Lock()),
            )
            state.users += 1
            try:
                async with state.lock:
                    task_sha256 = hashlib.sha256(canonical(asdict(task))).hexdigest()
                    cached, conflict = self._cached(metadata.delegation_id, task_sha256)
                    if conflict:
                        return ControlOutcome(
                            error="idempotency_conflict",
                            transient=False,
                            backpressure_wait_ms=wait_ms,
                        )
                    if cached is not None:
                        with self.probe.span("idempotency.hit"):
                            return ControlOutcome(
                                result=cached,
                                idempotency_hits=1,
                                backpressure_wait_ms=wait_ms,
                            )
                    return await self._execute_uncached(task, metadata, wait_ms, task_sha256)
            finally:
                state.users -= 1
                if state.users == 0 and metadata.delegation_id not in self._cache:
                    self._key_locks.pop(metadata.delegation_id, None)
        finally:
            await self._release()

    async def _execute_uncached(
        self,
        task: AnalysisTask,
        metadata: DelegationMetadata,
        wait_ms: float,
        task_sha256: str | None = None,
    ) -> ControlOutcome:
        selected = self._selected_for_fault(metadata)
        started = perf_counter()
        result = await execute(task)
        specialist_ms = (perf_counter() - started) * 1000
        if self.policy.idempotency:
            if task_sha256 is None:
                raise RuntimeError("idempotent execution requires a task hash")
            self._store(metadata.delegation_id, task_sha256, result)
        if selected and self.policy.fault_mode == "after-commit":
            with self.probe.span("fault.inject.after_commit"):
                return ControlOutcome(
                    error="injected_after_commit",
                    transient=True,
                    specialist_ms=specialist_ms,
                    kernel_executions=1,
                    injected_failures=1,
                    backpressure_wait_ms=wait_ms,
                )
        return ControlOutcome(
            result=result,
            specialist_ms=specialist_ms,
            kernel_executions=1,
            backpressure_wait_ms=wait_ms,
        )


def attempt_metrics(outcome: ControlOutcome, **wire: int | float) -> AttemptMetrics:
    """Translate a controlled outcome into retry-safe cumulative measurements."""
    return AttemptMetrics(
        remote_calls=int(wire.get("remote_calls", 0)),
        request_bytes=int(wire.get("request_bytes", 0)),
        response_bytes=int(wire.get("response_bytes", 0)),
        serialization_ms=float(wire.get("serialization_ms", 0.0)),
        transport_ms=float(wire.get("transport_ms", 0.0)),
        specialist_ms=outcome.specialist_ms,
        kernel_executions=outcome.kernel_executions,
        idempotency_hits=outcome.idempotency_hits,
        injected_failures=outcome.injected_failures,
        rejections=outcome.rejections,
        backpressure_wait_ms=outcome.backpressure_wait_ms,
    )


def selected_for_fault(policy: ResiliencePolicy, metadata: DelegationMetadata) -> bool:
    """Reproduce the declared stable selection in client and worker observations."""
    if policy.fault_mode == "none" or metadata.attempt != 1:
        return False
    digest = hashlib.sha256(metadata.delegation_id.encode()).digest()
    return int.from_bytes(digest[:8], "big") % policy.fault_every == 0


def add_metrics(left: AttemptMetrics, right: AttemptMetrics) -> AttemptMetrics:
    """Add measurements from sequential attempts without inventing missing values."""
    return replace(
        left,
        remote_calls=left.remote_calls + right.remote_calls,
        request_bytes=left.request_bytes + right.request_bytes,
        response_bytes=left.response_bytes + right.response_bytes,
        serialization_ms=left.serialization_ms + right.serialization_ms,
        transport_ms=left.transport_ms + right.transport_ms,
        specialist_ms=left.specialist_ms + right.specialist_ms,
        kernel_executions=left.kernel_executions + right.kernel_executions,
        idempotency_hits=left.idempotency_hits + right.idempotency_hits,
        injected_failures=left.injected_failures + right.injected_failures,
        rejections=left.rejections + right.rejections,
        backpressure_wait_ms=left.backpressure_wait_ms + right.backpressure_wait_ms,
    )
