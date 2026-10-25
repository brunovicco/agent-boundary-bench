"""Versioned raw data contracts; absent measurements remain null."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Config(BaseModel):
    """Controlled variables for a single experimental round."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    scenario: Literal["local", "http", "a2a"] = "local"
    payload_bytes: Literal[1024, 16384, 131072] = 1024
    wait_ms: Literal[0, 50, 250] = 0
    parallel: bool = False
    telemetry: bool = False
    rate: int = Field(default=5, ge=1, le=10000)
    duration: float = Field(default=2, gt=0, le=3600)
    warmup: int = Field(default=3, ge=1)
    concurrency: int = Field(default=64, ge=1)
    timeout: float = Field(default=5, gt=0)
    seed: int = 42
    repetition: int = Field(default=0, ge=0)
    label: str = "smoke"


class Sample(BaseModel):
    """One offered arrival, including explicit generator drops and failures."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1"
    index: int
    scheduled_ms: float
    started_ms: float
    scheduler_lag_ms: float
    arrival_latency_ms: float
    service_duration_ms: float
    status: Literal["ok", "error", "timeout", "dropped"]
    error: str | None = None
    specialist_ms: list[float] = Field(default_factory=list)
    remote_calls: int | None = None
    request_bytes: int | None = None
    response_bytes: int | None = None
    serialization_ms: float | None = None
    transport_ms: float | None = None
    trace_id: str | None = None


class ResourceSample(BaseModel):
    """OS process sample; CPU seconds are cumulative, RSS is instantaneous."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    elapsed_ms: float
    role: Literal["harness", "specialist"]
    pid: int
    cpu_seconds: float
    rss_bytes: int


class Manifest(BaseModel):
    """Machine-readable provenance of a real round, never fabricated hardware data."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "1"
    run_id: str
    started_at: str
    completed_at: str
    config: Config
    commit_sha: str | None
    git_dirty: bool | None
    lock_sha256: str
    python: str
    packages: dict[str, str]
    environment: dict[str, object]
    image_hashes: dict[str, str | None]
    network: dict[str, object]
    fixture_sha256: str
    offered: int
    completed: int
    succeeded: int
    dropped: int
    elapsed_seconds: float
    arrival_window_seconds: float
    sample_sha256: str
    resource_sha256: str
    limitations: list[str]
