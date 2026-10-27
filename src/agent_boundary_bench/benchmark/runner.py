"""Open-loop scheduled arrivals, raw observations and explicit generator overload."""

import asyncio
import hashlib
import importlib.metadata
import math
import os
import platform
import re
import shutil
import subprocess  # nosec B404
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx
import psutil
from opentelemetry import trace

from agent_boundary_bench.application.resilience import AttemptMetrics, RetryFailure, add_metrics
from agent_boundary_bench.application.supervisor import Delegate, NullProbe, Probe, supervise
from agent_boundary_bench.benchmark.models import Config, Manifest, ResourceSample, Sample
from agent_boundary_bench.benchmark.runtime import ResourceTarget, runtime
from agent_boundary_bench.domain.credit import CreditCase, digest, fixture
from agent_boundary_bench.observability import Telemetry
from agent_boundary_bench.observability.process import procfs_pid
from agent_boundary_bench.observability.resources import runtime_resource_snapshot


def file_hash(path: Path) -> str:
    """Digest raw files and lockfiles for auditability."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str | None:
    """Return provenance if this is a checkout, without requiring Git at runtime."""
    try:
        executable = shutil.which("git")
        if executable is None:
            return None
        output = subprocess.check_output(  # noqa: S603  # nosec B603
            [executable, *args],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return output.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def git_provenance() -> tuple[str | None, bool | None]:
    """Use explicit container provenance, falling back to the current checkout."""
    commit_sha = os.getenv("ABB_COMMIT_SHA") or git_value("rev-parse", "HEAD")
    if commit_sha is not None and re.fullmatch(r"[0-9a-fA-F]{40}", commit_sha) is None:
        raise ValueError("ABB_COMMIT_SHA must be a full 40-character hexadecimal SHA")

    configured_dirty = os.getenv("ABB_GIT_DIRTY")
    dirty: bool | None
    if configured_dirty is not None and configured_dirty != "":
        normalized = configured_dirty.casefold()
        if normalized in {"false", "0"}:
            dirty = False
        elif normalized in {"true", "1"}:
            dirty = True
        else:
            raise ValueError("ABB_GIT_DIRTY must be true, false, 1 or 0")
    else:
        status = git_value("status", "--porcelain")
        dirty = bool(status) if status is not None else None
    return commit_sha.lower() if commit_sha is not None else None, dirty


def environment() -> dict[str, object]:
    """Capture machine facts and cgroup constraints without guessing availability."""
    result: dict[str, object] = {
        "os": platform.platform(),
        "architecture": platform.machine(),
        "logical_cpus": os.cpu_count(),
        "physical_cpus": psutil.cpu_count(logical=False),
        "total_memory_bytes": psutil.virtual_memory().total,
        "cpu_affinity": sorted(os.sched_getaffinity(0))
        if hasattr(os, "sched_getaffinity")
        else None,
        "cpu_model": None,
    }
    cpuinfo = Path("/proc/cpuinfo")
    if cpuinfo.exists():
        result["cpu_model"] = next(
            (
                line.split(":", 1)[1].strip()
                for line in cpuinfo.read_text().splitlines()
                if line.startswith("model name")
            ),
            None,
        )
    for name in ("cpu.max", "memory.max", "cpuset.cpus.effective"):
        path = Path("/sys/fs/cgroup") / name
        result[name] = path.read_text().strip() if path.exists() else None
    snapshot = runtime_resource_snapshot()
    result["resource_isolation"] = {
        "label": os.getenv("ABB_ISOLATION_LABEL"),
        "cgroup_version": snapshot.cgroup_version,
        "cpu_limit_cores": snapshot.cpu_limit_cores,
        "memory_limit_bytes": snapshot.memory_limit_bytes,
    }
    return result


def resource_snapshot(pid: int, role: str, elapsed_ms: float) -> ResourceSample:
    """Measure process and cgroup counters; separate generator and specialist."""
    snapshot = runtime_resource_snapshot(pid)
    return ResourceSample(
        elapsed_ms=elapsed_ms,
        role=role,
        **snapshot.as_dict(),
    )


async def monitor(
    targets: dict[str, ResourceTarget],
    samples: list[ResourceSample],
    stop: asyncio.Event,
) -> dict[str, object]:
    """Sample every 100 ms and disclose any unavailable observations."""
    started = perf_counter()
    attempts = dict.fromkeys(targets, 0)
    failures = dict.fromkeys(targets, 0)
    request_timeout_seconds = 5.0
    async with httpx.AsyncClient(
        trust_env=False,
        timeout=request_timeout_seconds,
    ) as client:
        while True:
            for role, target in targets.items():
                attempts[role] += 1
                elapsed_ms = (perf_counter() - started) * 1000
                try:
                    if target.url is not None:
                        response = await client.get(target.url + "/resources")
                        response.raise_for_status()
                        samples.append(
                            ResourceSample.model_validate(
                                {"elapsed_ms": elapsed_ms, "role": role, **response.json()}
                            )
                        )
                    elif target.pid is not None:
                        samples.append(resource_snapshot(target.pid, role, elapsed_ms))
                    else:
                        failures[role] += 1
                except (httpx.HTTPError, OSError, TypeError, ValueError, psutil.Error):
                    failures[role] += 1
            if stop.is_set():
                return {
                    "interval_ms": 100,
                    "request_timeout_seconds": request_timeout_seconds,
                    "attempts": attempts,
                    "failures": failures,
                }
            try:
                await asyncio.wait_for(stop.wait(), 0.1)
            except TimeoutError:
                continue


async def one(
    index: int,
    scheduled: float,
    epoch: float,
    config: Config,
    delegate: Delegate,
    case: CreditCase,
    probe: Probe,
) -> Sample:
    """Record latency from scheduled arrival, including local scheduling delay."""
    started = perf_counter()
    status: str = "ok"
    error: str | None = None
    measured: dict[str, object] = {}
    with probe.span("benchmark.execution"):
        ctx = trace.get_current_span().get_span_context() if config.telemetry else None
        trace_id = f"{ctx.trace_id:032x}" if ctx and ctx.is_valid else None
        try:
            result = await supervise(
                delegate,
                case,
                config.wait_ms,
                config.parallel,
                config.timeout,
                probe,
                specialist_repetitions=config.specialist_repetitions,
                fanout_limit=config.fanout_limit,
                cpu_iterations=config.cpu_iterations,
                memory_bytes=config.memory_bytes,
                resilience=config.resilience_policy(),
                execution_id=f"measured:{config.seed}:{config.repetition}:{index}",
            )
            measured = {
                "specialist_ms": [v.specialist_ms for v in result.invocations],
                "remote_calls": sum(v.remote_calls for v in result.invocations),
                "request_bytes": sum(v.request_bytes for v in result.invocations),
                "response_bytes": sum(v.response_bytes for v in result.invocations),
                "serialization_ms": sum(v.serialization_ms for v in result.invocations),
                "transport_ms": sum(v.transport_ms for v in result.invocations),
                "tool_calls": sum(v.tool_calls for v in result.invocations),
                "resource_reads": sum(v.resource_reads for v in result.invocations),
                "context_bytes": sum(v.context_bytes for v in result.invocations),
                "attempts": sum(v.attempts for v in result.invocations),
                "retries": sum(v.retries for v in result.invocations),
                "kernel_executions": sum(v.kernel_executions for v in result.invocations),
                "idempotency_hits": sum(v.idempotency_hits for v in result.invocations),
                "injected_failures": sum(v.injected_failures for v in result.invocations),
                "rejections": sum(v.rejections for v in result.invocations),
                "backpressure_wait_ms": sum(v.backpressure_wait_ms for v in result.invocations),
            }
        except Exception as exc:  # measurement records failures rather than losing arrivals
            status = "timeout" if has_timeout(exc) else "error"
            failures = retry_failures(exc)
            if failures:
                cumulative = AttemptMetrics()
                for failure in failures:
                    cumulative = add_metrics(cumulative, failure.metrics)
                measured = {
                    "specialist_ms": [
                        failure.metrics.specialist_ms
                        for failure in failures
                        if failure.metrics.specialist_ms > 0
                    ],
                    "remote_calls": cumulative.remote_calls,
                    "request_bytes": cumulative.request_bytes,
                    "response_bytes": cumulative.response_bytes,
                    "serialization_ms": cumulative.serialization_ms,
                    "transport_ms": cumulative.transport_ms,
                    "attempts": sum(failure.attempts for failure in failures),
                    "retries": sum(failure.attempts - 1 for failure in failures),
                    "kernel_executions": cumulative.kernel_executions,
                    "idempotency_hits": cumulative.idempotency_hits,
                    "injected_failures": cumulative.injected_failures,
                    "rejections": cumulative.rejections,
                    "backpressure_wait_ms": cumulative.backpressure_wait_ms,
                }
                error = ",".join(sorted({failure.reason for failure in failures}))
            else:
                error = type(exc).__name__
    ended = perf_counter()
    return Sample.model_validate(
        {
            "index": index,
            "scheduled_ms": (scheduled - epoch) * 1000,
            "started_ms": (started - epoch) * 1000,
            "scheduler_lag_ms": max(0, started - scheduled) * 1000,
            "arrival_latency_ms": (ended - scheduled) * 1000,
            "service_duration_ms": (ended - started) * 1000,
            "status": status,
            "error": error,
            "trace_id": trace_id,
            **measured,
        }
    )


def has_timeout(exc: BaseException) -> bool:
    """Recognize timeout failures through structured-concurrency exception groups."""
    if isinstance(exc, BaseExceptionGroup):
        return any(has_timeout(item) for item in exc.exceptions)
    return isinstance(exc, TimeoutError) or "Timeout" in type(exc).__name__


def retry_failures(exc: BaseException) -> list[RetryFailure]:
    """Collect typed retry failures through structured-concurrency exception groups."""
    if isinstance(exc, BaseExceptionGroup):
        return [failure for item in exc.exceptions for failure in retry_failures(item)]
    return [exc] if isinstance(exc, RetryFailure) else []


def expected_warmup_failures(config: Config, failures: list[RetryFailure]) -> bool:
    """Allow only failures explicitly introduced by the configured treatment."""
    expected: set[str] = set()
    match config.fault_mode:
        case "fail-first":
            expected.add("injected_fail_first")
        case "delay-first":
            expected.update(("attempt_timeout", "injected_delay_first"))
        case "after-commit":
            expected.add("injected_after_commit")
    if config.service_concurrency:
        expected.update(("overloaded", "queue_timeout"))
    return bool(failures) and all(failure.reason in expected for failure in failures)


async def arrivals(
    config: Config, delegate: Delegate, case: CreditCase, probe: Probe
) -> tuple[list[Sample], float]:
    """Issue arrivals on fixed deadlines, never wait for a response to schedule the next."""
    epoch = perf_counter()
    pending: set[asyncio.Task[Sample]] = set()
    samples: list[Sample] = []
    for index in range(math.ceil(config.rate * config.duration)):
        scheduled = epoch + index / config.rate
        await asyncio.sleep(max(0, scheduled - perf_counter()))
        finished = {task for task in pending if task.done()}
        samples.extend(task.result() for task in finished)
        pending -= finished
        if len(pending) >= config.concurrency:
            now = perf_counter()
            samples.append(
                Sample(
                    index=index,
                    scheduled_ms=(scheduled - epoch) * 1000,
                    started_ms=(now - epoch) * 1000,
                    scheduler_lag_ms=(now - scheduled) * 1000,
                    arrival_latency_ms=(now - scheduled) * 1000,
                    service_duration_ms=0,
                    status="dropped",
                    error="generator_concurrency_limit",
                )
            )
        else:
            pending.add(
                asyncio.create_task(one(index, scheduled, epoch, config, delegate, case, probe))
            )
    samples.extend(await asyncio.gather(*pending))
    # Include the entire arrival window plus drain when calculating throughput.
    await asyncio.sleep(max(0, epoch + config.duration - perf_counter()))
    return sorted(samples, key=lambda sample: sample.index), perf_counter() - epoch


async def run(config: Config, output: Path) -> Path:
    """Execute warmup plus one real measured round and persist complete raw evidence."""
    started_at = datetime.now(UTC).isoformat()
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S") + "-" + uuid4().hex[:10]
    directory = output / run_id
    directory.mkdir(parents=True, exist_ok=False)
    telemetry = (
        Telemetry(directory / "harness-spans.jsonl", "abb-harness") if config.telemetry else None
    )
    probe: Probe = telemetry or NullProbe()
    case = fixture(config.payload_bytes, config.seed)
    resources: list[ResourceSample] = []
    resource_sampling: dict[str, object] = {}
    warmup_succeeded = 0
    warmup_failed = 0
    try:
        async with runtime(config, probe, directory) as (delegate, specialist_target):
            for _ in range(config.warmup):
                try:
                    await supervise(
                        delegate,
                        case,
                        config.wait_ms,
                        config.parallel,
                        config.timeout,
                        probe,
                        specialist_repetitions=config.specialist_repetitions,
                        fanout_limit=config.fanout_limit,
                        cpu_iterations=config.cpu_iterations,
                        memory_bytes=config.memory_bytes,
                        resilience=config.resilience_policy(),
                    )
                except Exception as exc:
                    failures = retry_failures(exc)
                    if not expected_warmup_failures(config, failures):
                        raise
                    warmup_failed += 1
                else:
                    warmup_succeeded += 1
            stop = asyncio.Event()
            targets = {"harness": ResourceTarget(pid=procfs_pid())}
            if specialist_target is not None:
                targets["specialist"] = specialist_target
            monitoring = asyncio.create_task(monitor(targets, resources, stop))
            try:
                samples, elapsed = await arrivals(config, delegate, case, probe)
            finally:
                stop.set()
                resource_sampling = await monitoring
    finally:
        if telemetry:
            telemetry.close()
    sample_file = directory / "samples.jsonl"
    sample_file.write_text("".join(s.model_dump_json() + "\n" for s in samples))
    resource_file = directory / "resources.jsonl"
    resource_file.write_text("".join(s.model_dump_json() + "\n" for s in resources))
    commit_sha, git_dirty = git_provenance()
    manifest = Manifest(
        run_id=run_id,
        started_at=started_at,
        completed_at=datetime.now(UTC).isoformat(),
        config=config,
        commit_sha=commit_sha,
        git_dirty=git_dirty,
        lock_sha256=file_hash(Path("uv.lock")),
        python=platform.python_version(),
        packages={
            name: importlib.metadata.version(name)
            for name in (
                "a2a-sdk",
                "fastapi",
                "httpx",
                "pydantic",
                "uvicorn",
                "opentelemetry-sdk",
                "psutil",
                "mcp",
                "mcp-types",
                "httpx2",
            )
        },
        environment=environment(),
        image_hashes={"application": os.getenv("ABB_IMAGE_DIGEST") or None},
        network={
            "topology": (
                "in-process"
                if config.scenario in ("local", "mcp-inprocess")
                else os.getenv("ABB_NETWORK_TOPOLOGY", "explicit external service endpoint")
                if specialist_target is not None and specialist_target.external
                else "same-host stdio child process"
                if config.scenario == "mcp-stdio"
                else "same-host loopback"
            ),
            "protocol": (
                "none"
                if config.scenario == "local"
                else "MCP direct dispatch"
                if config.scenario == "mcp-inprocess"
                else "MCP JSON-RPC stdio"
                if config.scenario == "mcp-stdio"
                else "MCP Streamable HTTP/1.1"
                if config.scenario == "mcp-streamable-http"
                else "HTTP/1.1"
            ),
            "workers": 0 if config.scenario in ("local", "mcp-inprocess") else 1,
            "specialist_processes": (0 if config.scenario in ("local", "mcp-inprocess") else 1),
            "tls": False,
            "keepalive": (
                True if config.scenario in ("http", "a2a", "mcp-streamable-http") else None
            ),
            "connection_limit": (
                128 if config.scenario in ("http", "a2a", "mcp-streamable-http") else 0
            ),
            "discovery": (
                "MCP server/discover plus tools/resources listing once before warmup"
                if config.scenario.startswith("mcp-")
                else "agent card once before warmup"
                if config.scenario == "a2a"
                else "none"
            ),
            "load_generator": "python monotonic fixed-arrival deadlines",
            "specialist_resource_endpoint": (
                specialist_target.url
                if specialist_target is not None and specialist_target.external
                else None
            ),
        },
        fixture_sha256=digest(case),
        warmup_succeeded=warmup_succeeded,
        warmup_failed=warmup_failed,
        offered=len(samples),
        completed=sum(s.status != "dropped" for s in samples),
        succeeded=sum(s.status == "ok" for s in samples),
        dropped=sum(s.status == "dropped" for s in samples),
        elapsed_seconds=elapsed,
        arrival_window_seconds=config.duration,
        sample_sha256=file_hash(sample_file),
        resource_sha256=file_hash(resource_file),
        resource_sampling=resource_sampling,
        limitations=[
            "Synthetic asynchronous wait is not CPU work or model inference.",
            "Synthetic CPU iterations and touched memory allocation are fixed work controls, "
            "not calibrated model workloads.",
            "Shared host; generator competes with system under test. No hardware isolation claim.",
            "cgroup counters are observational and sampled at 100 ms; the resource endpoint "
            "adds small control-plane work outside the business payload.",
            "A configured isolation label is descriptive; observed cgroup CPU/memory limits in "
            "the manifest and resources file are authoritative.",
            "Component resource caps do not equalize aggregate architecture budgets; remote "
            "topologies can use harness and specialist quotas while local work shares one quota.",
            "cgroup memory.peak is container-lifetime state; sampled memory.current and RSS "
            "provide round-scoped observations but can miss activity between samples.",
            "Body bytes exclude TCP/IP and HTTP headers. "
            "Serialization metric covers explicit domain codec only.",
            "A2A uses immediate Message replies; durable task lifecycle, polling and "
            "discovery cost are excluded. Explicitly configured application retries are included.",
            "OTel enabled includes synchronous local JSONL export; "
            "not a universal instrumentation overhead.",
            "No image digest for native subprocess runs; null means not used/not measured.",
            "MCP request/response bytes are explicit tool arguments, text results and "
            "resource URI/content bytes; JSON-RPC/HTTP framing and headers are excluded.",
            "The MCP stdio SDK does not expose its child PID through the public client API; "
            "specialist CPU/RSS are therefore unavailable for that arm.",
            "v0.3 fault injection is deterministic application-layer treatment, not a proxy "
            "for every network, host or process failure mode.",
            "Idempotency state is bounded, in-memory and worker-local; it is not a durable "
            "cross-worker guarantee.",
        ],
    )
    (directory / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
    return directory
