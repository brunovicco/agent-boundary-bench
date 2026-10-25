"""Deterministic synthetic credit domain; no transport or telemetry dependencies."""

import asyncio
import hashlib
import json
import random
from dataclasses import asdict, dataclass, replace
from enum import StrEnum


class Specialist(StrEnum):
    """Three independent synthetic analytical responsibilities."""

    DOCUMENT = "document_analyst"
    FINANCIAL = "financial_analyst"
    COMPLIANCE = "compliance_analyst"


@dataclass(frozen=True)
class CreditCase:
    """Integer synthetic units, never real currency or personal data."""

    case_id: str
    revenue_units: int
    debt_units: int
    documents: tuple[str, ...]
    sanctions_flag: bool
    padding: str
    fixture_version: str = "1"


@dataclass(frozen=True)
class AnalysisTask:
    """A typed delegation with explicit synthetic I/O wait."""

    specialist: Specialist
    case: CreditCase
    wait_ms: int = 0


@dataclass(frozen=True)
class AnalysisResult:
    """Stable business output, excluding timing and runtime identifiers."""

    specialist: Specialist
    case_id: str
    score: int
    eligible: bool
    evidence: tuple[str, ...]
    input_sha256: str
    kernel_version: str = "1"


def canonical(value: object) -> bytes:
    """Encode JSON-compatible values consistently (not an RFC 8785 claim)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def digest(case: CreditCase) -> str:
    """Hash the complete domain payload, including padding."""
    return hashlib.sha256(canonical(asdict(case))).hexdigest()


def fixture(size: int, seed: int = 42) -> CreditCase:
    """Build an exact-size canonical case JSON body with a reproducible seed."""
    if size not in (1024, 16384, 131072):
        raise ValueError("payload size must be 1024, 16384 or 131072 bytes")
    rng = random.Random(seed)  # noqa: S311  # nosec B311
    case = CreditCase(
        case_id=f"synthetic-{seed}",
        revenue_units=rng.randint(10000, 100000),
        debt_units=rng.randint(1000, 20000),
        documents=("registration", "accounts", "ownership"),
        sanctions_flag=False,
        padding="",
    )
    return replace(case, padding="x" * (size - len(canonical(asdict(case)))))


def evaluate(task: AnalysisTask) -> AnalysisResult:
    """Compute deterministic rules shared by every adapter."""
    if task.wait_ms not in (0, 50, 250):
        raise ValueError("wait_ms must be 0, 50 or 250")
    case = task.case
    if case.revenue_units <= 0 or case.debt_units < 0:
        raise ValueError("invalid synthetic financial units")
    match task.specialist:
        case Specialist.DOCUMENT:
            score = min(100, len(set(case.documents)) * 30)
            evidence = (f"document_count={len(set(case.documents))}",)
        case Specialist.FINANCIAL:
            score = max(0, 100 - case.debt_units * 100 // case.revenue_units)
            evidence = (f"debt_ratio_bps={case.debt_units * 10000 // case.revenue_units}",)
        case Specialist.COMPLIANCE:
            score = 0 if case.sanctions_flag else 100
            evidence = (f"synthetic_flag={str(case.sanctions_flag).lower()}",)
    return AnalysisResult(task.specialist, case.case_id, score, score >= 60, evidence, digest(case))


async def execute(task: AnalysisTask) -> AnalysisResult:
    """Simulate I/O latency; this is explicitly NOT a CPU workload."""
    result = evaluate(task)
    if task.wait_ms:
        await asyncio.sleep(task.wait_ms / 1000)
    return result
