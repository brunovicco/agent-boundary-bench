"""Versioned raw data contracts; absent measurements remain null."""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_boundary_bench.application.resilience import FaultMode, ResiliencePolicy

Scenario = Literal[
    "local",
    "http",
    "a2a",
    "mcp-inprocess",
    "mcp-stdio",
    "mcp-streamable-http",
]
MCP_SCENARIOS = frozenset({"mcp-inprocess", "mcp-stdio", "mcp-streamable-http"})


class Config(BaseModel):
    """Controlled variables for a single experimental round."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    scenario: Scenario = "local"
    payload_bytes: Literal[1024, 16384, 131072] = 1024
    wait_ms: Literal[0, 50, 250] = 0
    cpu_iterations: int = Field(default=0, ge=0, le=1000000)
    memory_bytes: int = Field(default=0, ge=0, le=67108864)
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
    specialist_repetitions: int = Field(default=1, ge=1, le=32)
    fanout_limit: int = Field(default=64, ge=1, le=128)
    context_copies: Literal[0, 1, 4, 16] = 0
    tool_repetitions: int = Field(default=1, ge=1, le=16)
    resource_reads: int = Field(default=0, ge=0, le=16)
    fault_mode: FaultMode = "none"
    fault_every: int = Field(default=1, ge=1, le=10000)
    fault_delay_ms: int = Field(default=100, ge=1, le=60000)
    max_attempts: int = Field(default=1, ge=1, le=8)
    attempt_timeout: float = Field(default=5, gt=0, le=3600)
    retry_backoff_ms: int = Field(default=0, ge=0, le=60000)
    idempotency: bool = False
    idempotency_capacity: int = Field(default=10000, ge=1, le=1000000)
    idempotency_ttl_seconds: float = Field(default=300, gt=0, le=86400)
    service_concurrency: int = Field(default=0, ge=0, le=10000)
    queue_capacity: int = Field(default=0, ge=0, le=100000)
    queue_timeout_ms: int = Field(default=1000, ge=1, le=60000)

    @model_validator(mode="after")
    def mcp_only_controls(self) -> Self:
        """Keep MCP tool/resource variables out of delegation experiments."""
        if self.scenario not in MCP_SCENARIOS and (
            self.context_copies or self.tool_repetitions != 1 or self.resource_reads
        ):
            raise ValueError("context/tool/resource amplification is valid only for MCP scenarios")
        if self.service_concurrency == 0 and self.queue_capacity:
            raise ValueError("queue_capacity requires service_concurrency")
        active_tasks = (
            min(3 * self.specialist_repetitions, self.fanout_limit) if self.parallel else 1
        )
        if self.memory_bytes * active_tasks > 256 * 1024 * 1024:
            raise ValueError("declared per-execution concurrent memory exceeds 256 MiB")
        if self.scenario in MCP_SCENARIOS and self.resilience_policy().enabled:
            raise ValueError("v0.3 resilience controls apply only to delegation scenarios")
        return self

    def resilience_policy(self) -> ResiliencePolicy:
        """Translate validated benchmark controls into the framework-free application policy."""
        return ResiliencePolicy(
            fault_mode=self.fault_mode,
            fault_every=self.fault_every,
            fault_delay_ms=self.fault_delay_ms,
            max_attempts=self.max_attempts,
            attempt_timeout=self.attempt_timeout,
            retry_backoff_ms=self.retry_backoff_ms,
            idempotency=self.idempotency,
            idempotency_capacity=self.idempotency_capacity,
            idempotency_ttl_seconds=self.idempotency_ttl_seconds,
            service_concurrency=self.service_concurrency,
            queue_capacity=self.queue_capacity,
            queue_timeout_ms=self.queue_timeout_ms,
        )


class Sample(BaseModel):
    """One offered arrival, including explicit generator drops and failures."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "3"
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
    tool_calls: int | None = None
    resource_reads: int | None = None
    context_bytes: int | None = None
    attempts: int | None = None
    retries: int | None = None
    kernel_executions: int | None = None
    idempotency_hits: int | None = None
    injected_failures: int | None = None
    rejections: int | None = None
    backpressure_wait_ms: float | None = None


class ResourceSample(BaseModel):
    """OS process/cgroup sample; cumulative and instantaneous fields remain distinct."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "2"
    elapsed_ms: float
    role: Literal["harness", "specialist"]
    pid: int
    cpu_seconds: float
    rss_bytes: int
    cgroup_version: Literal["v2"] | None = None
    cpu_usage_usec: int | None = None
    cpu_user_usec: int | None = None
    cpu_system_usec: int | None = None
    cpu_nr_periods: int | None = None
    cpu_nr_throttled: int | None = None
    cpu_throttled_usec: int | None = None
    cpu_limit_cores: float | None = None
    memory_current_bytes: int | None = None
    memory_peak_bytes: int | None = None
    memory_limit_bytes: int | None = None
    memory_events_low: int | None = None
    memory_events_high: int | None = None
    memory_events_max: int | None = None
    memory_events_oom: int | None = None
    memory_events_oom_kill: int | None = None
    memory_events_oom_group_kill: int | None = None


class Manifest(BaseModel):
    """Machine-readable provenance of a real round, never fabricated hardware data."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: str = "4"
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
    warmup_succeeded: int = 0
    warmup_failed: int = 0
    offered: int
    completed: int
    succeeded: int
    dropped: int
    elapsed_seconds: float
    arrival_window_seconds: float
    sample_sha256: str
    resource_sha256: str
    resource_sampling: dict[str, object] = Field(default_factory=dict)
    limitations: list[str]
