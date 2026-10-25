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
    fixture,
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
