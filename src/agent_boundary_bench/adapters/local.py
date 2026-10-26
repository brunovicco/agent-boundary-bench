"""In-process delegation adapter."""

import asyncio

from agent_boundary_bench.application.resilience import (
    AttemptMetrics,
    DelegationFailure,
    DelegationMetadata,
    ExecutionController,
    ResiliencePolicy,
    attempt_metrics,
)
from agent_boundary_bench.application.supervisor import Invocation, Probe
from agent_boundary_bench.domain.credit import AnalysisTask


class LocalDelegate:
    """Call the shared kernel through the typed port without network services."""

    def __init__(self, probe: Probe, policy: ResiliencePolicy | None = None) -> None:
        """Inject observation without global telemetry requirements."""
        self.probe = probe
        self.controller = ExecutionController(policy or ResiliencePolicy(), probe)

    async def invoke(
        self,
        task: AnalysisTask,
        *,
        delegation_id: str | None = None,
        attempt: int = 1,
    ) -> Invocation:
        """Measure only kernel execution as specialist time."""
        metadata = DelegationMetadata.create(delegation_id, attempt)
        try:
            with self.probe.span("delegation.local"), self.probe.span("specialist.process"):
                outcome = await self.controller.execute(task, metadata)
        except asyncio.CancelledError as exc:
            if delegation_id is None:
                raise
            raise DelegationFailure(
                "attempt_timeout",
                transient=True,
                metrics=AttemptMetrics(),
            ) from exc
        if outcome.error is not None:
            raise DelegationFailure(
                outcome.error,
                transient=outcome.transient,
                metrics=attempt_metrics(outcome),
            )
        if outcome.result is None:
            raise RuntimeError("controlled local execution returned no result")
        return Invocation(
            outcome.result,
            outcome.specialist_ms,
            kernel_executions=outcome.kernel_executions,
            idempotency_hits=outcome.idempotency_hits,
            injected_failures=outcome.injected_failures,
            rejections=outcome.rejections,
            backpressure_wait_ms=outcome.backpressure_wait_ms,
        )
