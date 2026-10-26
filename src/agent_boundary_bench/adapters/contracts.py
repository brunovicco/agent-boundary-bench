"""Pydantic validation at transport boundaries; domain models remain dataclasses."""

from typing import Self

from pydantic import BaseModel, ConfigDict, TypeAdapter, model_validator

from agent_boundary_bench.domain.credit import AnalysisResult, AnalysisTask

TASK = TypeAdapter(AnalysisTask)
RESULT = TypeAdapter(AnalysisResult)


class Reply(BaseModel):
    """Common success/failure envelope separating business and measurement fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    result: AnalysisResult | None = None
    specialist_ms: float = 0.0
    error: str | None = None
    transient: bool = False
    kernel_executions: int = 0
    idempotency_hits: int = 0
    injected_failures: int = 0
    rejections: int = 0
    backpressure_wait_ms: float = 0.0

    @model_validator(mode="after")
    def exactly_one_outcome(self) -> Self:
        """Reject ambiguous envelopes at every transport boundary."""
        if (self.result is None) == (self.error is None):
            raise ValueError("reply must contain exactly one of result or error")
        return self
