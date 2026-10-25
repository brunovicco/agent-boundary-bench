"""Open-loop scheduled arrivals, raw observations and explicit generator overload."""

import asyncio
import hashlib
import importlib.metadata
import math
import os
import platform
import shutil
import subprocess  # nosec B404
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import psutil
from opentelemetry import trace

from agent_boundary_bench.application.supervisor import Delegate, NullProbe, Probe, supervise
from agent_boundary_bench.benchmark.models import Config, Manifest, ResourceSample, Sample
from agent_boundary_bench.benchmark.runtime import runtime
from agent_boundary_bench.domain.credit import CreditCase, digest, fixture
from agent_boundary_bench.observability import Telemetry
from agent_boundary_bench.observability.process import procfs_pid


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
    return result


def resource_snapshot(pid: int, role: str, elapsed_ms: float) -> ResourceSample:
    """Measure process CPU and RSS; separate generator and specialist."""
    process = psutil.Process(pid)
    cpu = process.cpu_times()
    return ResourceSample(
        elapsed_ms=elapsed_ms,
        role=role,
        pid=pid,
        cpu_seconds=cpu.user + cpu.system,
        rss_bytes=process.memory_info().rss,
    )


async def monitor(pids: dict[str, int], samples: list[ResourceSample], stop: asyncio.Event) -> None:
    """Sample every 100 ms, retaining first/last points for CPU deltas."""
    started = perf_counter()
    while True:
        for role, pid in pids.items():
            samples.append(resource_snapshot(pid, role, (perf_counter() - started) * 1000))
        if stop.is_set():
            return
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
            }
        except Exception as exc:  # measurement records failures rather than losing arrivals
            status = "timeout" if has_timeout(exc) else "error"
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
    try:
        async with runtime(config, probe, directory) as (delegate, pid):
            for _ in range(config.warmup):
                await supervise(
                    delegate,
                    case,
                    config.wait_ms,
                    config.parallel,
                    config.timeout,
                    probe,
                    specialist_repetitions=config.specialist_repetitions,
                    fanout_limit=config.fanout_limit,
                )
            stop = asyncio.Event()
            pids = {"harness": procfs_pid()}
            if pid is not None:
                pids["specialist"] = pid
            monitoring = asyncio.create_task(monitor(pids, resources, stop))
            try:
                samples, elapsed = await arrivals(config, delegate, case, probe)
            finally:
                stop.set()
                await monitoring
    finally:
        if telemetry:
            telemetry.close()
    sample_file = directory / "samples.jsonl"
    sample_file.write_text("".join(s.model_dump_json() + "\n" for s in samples))
    resource_file = directory / "resources.jsonl"
    resource_file.write_text("".join(s.model_dump_json() + "\n" for s in resources))
    dirty = git_value("status", "--porcelain")
    manifest = Manifest(
        run_id=run_id,
        started_at=started_at,
        completed_at=datetime.now(UTC).isoformat(),
        config=config,
        commit_sha=git_value("rev-parse", "HEAD"),
        git_dirty=bool(dirty) if dirty is not None else None,
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
        image_hashes={"application": os.getenv("ABB_IMAGE_DIGEST")},
        network={
            "topology": (
                "in-process"
                if config.scenario in ("local", "mcp-inprocess")
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
        },
        fixture_sha256=digest(case),
        offered=len(samples),
        completed=sum(s.status != "dropped" for s in samples),
        succeeded=sum(s.status == "ok" for s in samples),
        dropped=sum(s.status == "dropped" for s in samples),
        elapsed_seconds=elapsed,
        arrival_window_seconds=config.duration,
        sample_sha256=file_hash(sample_file),
        resource_sha256=file_hash(resource_file),
        limitations=[
            "Synthetic asynchronous wait is not CPU work or model inference.",
            "Shared host; generator competes with system under test. No hardware isolation claim.",
            "Body bytes exclude TCP/IP and HTTP headers. "
            "Serialization metric covers explicit domain codec only.",
            "A2A uses immediate Message replies; "
            "task lifecycle, retries and discovery cost are excluded.",
            "OTel enabled includes synchronous local JSONL export; "
            "not a universal instrumentation overhead.",
            "No image digest for native subprocess runs; null means not used/not measured.",
            "MCP request/response bytes are explicit tool arguments, text results and "
            "resource URI/content bytes; JSON-RPC/HTTP framing and headers are excluded.",
            "The MCP stdio SDK does not expose its child PID through the public client API; "
            "specialist CPU/RSS are therefore unavailable for that arm.",
        ],
    )
    (directory / "manifest.json").write_text(manifest.model_dump_json(indent=2) + "\n")
    return directory
