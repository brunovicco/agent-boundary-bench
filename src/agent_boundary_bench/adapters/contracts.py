"""Pydantic validation at transport boundaries; domain models remain dataclasses."""

from pydantic import BaseModel, ConfigDict, TypeAdapter

from agent_boundary_bench.domain.credit import AnalysisResult, AnalysisTask

TASK = TypeAdapter(AnalysisTask)
RESULT = TypeAdapter(AnalysisResult)


class Reply(BaseModel):
    """Common specialist envelope separating business and measurement fields."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    result: AnalysisResult
    specialist_ms: float
