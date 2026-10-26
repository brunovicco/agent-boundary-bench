"""Versioned deterministic data and rule validation."""

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from agent_boundary_bench.domain.credit import (
    AnalysisTask,
    Specialist,
    canonical,
    digest,
    evaluate,
    execute,
    fixture,
    synthetic_cpu_work,
    synthetic_memory_work,
)


@pytest.mark.parametrize("size", [1024, 16384, 131072])
def test_versioned_fixtures(size: int) -> None:
    case = fixture(size)
    path = Path(f"fixtures/v1/case-{size}.json")
    assert path.read_bytes() == canonical(asdict(case))
    assert len(path.read_bytes()) == size
    assert fixture(size, 43) != case
    expected = json.loads(Path("fixtures/v1/expected.json").read_text())
    for specialist in Specialist:
        result = evaluate(AnalysisTask(specialist, case))
        assert json.loads(canonical(asdict(result))) in expected
        assert result.input_sha256 == digest(case)


def test_rules_and_invalid_inputs() -> None:
    case = fixture(1024)
    flagged = replace(case, sanctions_flag=True)
    assert not evaluate(AnalysisTask(Specialist.COMPLIANCE, flagged)).eligible
    assert evaluate(AnalysisTask(Specialist.DOCUMENT, replace(case, documents=()))).score == 0
    with pytest.raises(ValueError, match="payload size"):
        fixture(2)
    with pytest.raises(ValueError, match="wait_ms"):
        evaluate(AnalysisTask(Specialist.DOCUMENT, case, 1))
    with pytest.raises(ValueError, match="financial units"):
        evaluate(AnalysisTask(Specialist.FINANCIAL, replace(case, revenue_units=0)))
    with pytest.raises(ValueError, match="cpu_iterations"):
        evaluate(AnalysisTask(Specialist.DOCUMENT, case, cpu_iterations=-1))
    with pytest.raises(ValueError, match="memory_bytes"):
        evaluate(AnalysisTask(Specialist.DOCUMENT, case, memory_bytes=64 * 1024 * 1024 + 1))


async def test_cpu_work_is_deterministic_and_business_neutral() -> None:
    case = fixture(1024)
    baseline = AnalysisTask(Specialist.DOCUMENT, case)
    treated = AnalysisTask(
        Specialist.DOCUMENT,
        case,
        cpu_iterations=100,
        memory_bytes=8192,
    )
    assert synthetic_cpu_work(treated) == synthetic_cpu_work(treated)
    assert synthetic_cpu_work(treated) != synthetic_cpu_work(
        AnalysisTask(Specialist.FINANCIAL, case, cpu_iterations=100)
    )
    allocation = synthetic_memory_work(treated)
    assert len(allocation) == 8192
    assert allocation[0] == 0
    assert allocation[4096] == 1
    assert await execute(treated) == await execute(baseline)
