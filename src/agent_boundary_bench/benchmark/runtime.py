"""Lifecycle of local delegates and equivalent independent specialist workers."""

import asyncio
import os
import socket
import subprocess  # nosec B404
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import httpx

from agent_boundary_bench.adapters.local import LocalDelegate
from agent_boundary_bench.adapters.mcp import MCPDelegate
from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.supervisor import Delegate, Probe
from agent_boundary_bench.benchmark.models import Config


@dataclass(frozen=True)
class ResourceTarget:
    """A specialist resource source, either a local PID or a metadata endpoint."""

    pid: int | None = None
    url: str | None = None
    external: bool = False


def external_endpoint(config: Config) -> str | None:
    """Resolve an explicit Compose endpoint without accepting credentials or URL extras."""
    key = {"http": "ABB_HTTP_ENDPOINT", "a2a": "ABB_A2A_ENDPOINT"}.get(config.scenario)
    if key is None:
        return None
    value = os.getenv(key)
    if value is None:
        return None
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname is None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{key} must be a credential-free HTTP origin")
    return value.rstrip("/")


def free_port() -> int:
    """Ask the OS for a loopback port; readiness catches startup/race failures."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def health(url: str, attempts: int = 400) -> int:
    """Bounded health poll independent from measured requests."""
    async with httpx.AsyncClient(trust_env=False, timeout=0.5) as client:
        for _ in range(attempts):
            try:
                response = await client.get(url + "/health")
                response.raise_for_status()
                return int(str(response.json()["procfs_pid"]))
            except (httpx.HTTPError, OSError):
                await asyncio.sleep(0.05)
    raise RuntimeError(f"specialist did not become healthy: {url}")


@asynccontextmanager
async def runtime(
    config: Config,
    probe: Probe,
    directory: Path,
) -> AsyncIterator[tuple[Delegate, ResourceTarget | None]]:
    """Own each adapter and any one-worker process required by its boundary."""
    if config.scenario == "local":
        yield LocalDelegate(probe, config.resilience_policy()), None
        return
    configured_endpoint = external_endpoint(config)
    if configured_endpoint is not None:
        delegate = RemoteDelegate(
            configured_endpoint,
            config.scenario,
            probe,
            config.telemetry,
            config.timeout,
        )
        try:
            await health(configured_endpoint)
            await delegate.prepare()
            yield delegate, ResourceTarget(url=configured_endpoint, external=True)
        finally:
            await delegate.close()
        return
    if config.scenario in ("mcp-inprocess", "mcp-stdio"):
        mcp_delegate = MCPDelegate(
            config.scenario,
            probe,
            config.timeout,
            config.context_copies,
            config.tool_repetitions,
            config.resource_reads,
            directory,
        )
        try:
            await mcp_delegate.prepare()
            yield mcp_delegate, None
        finally:
            await mcp_delegate.close()
        return
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    if config.scenario == "mcp-streamable-http":
        command = [
            sys.executable,
            "-m",
            "agent_boundary_bench.entrypoints.cli",
            "mcp-serve",
            "--transport",
            "streamable-http",
            "--port",
            str(port),
        ]
    else:
        command = [
            sys.executable,
            "-m",
            "agent_boundary_bench.entrypoints.cli",
            "serve",
            "--scenario",
            config.scenario,
            "--port",
            str(port),
        ]
        policy = config.resilience_policy()
        if policy.enabled:
            command += [
                "--fault-mode",
                policy.fault_mode,
                "--fault-every",
                str(policy.fault_every),
                "--fault-delay-ms",
                str(policy.fault_delay_ms),
                "--idempotency-capacity",
                str(policy.idempotency_capacity),
                "--idempotency-ttl-seconds",
                str(policy.idempotency_ttl_seconds),
                "--service-concurrency",
                str(policy.service_concurrency),
                "--queue-capacity",
                str(policy.queue_capacity),
                "--queue-timeout-ms",
                str(policy.queue_timeout_ms),
            ]
            if policy.idempotency:
                command.append("--idempotency")
    if config.telemetry:
        command += ["--trace-file", str(directory / "specialist-spans.jsonl")]
    with (directory / "specialist.log").open("w", encoding="utf-8") as logfile:
        process = subprocess.Popen(command, stdout=logfile, stderr=logfile)  # noqa: S603  # nosec B603
        if config.scenario == "mcp-streamable-http":
            running_delegate: RemoteDelegate | MCPDelegate = MCPDelegate(
                config.scenario,
                probe,
                config.timeout,
                config.context_copies,
                config.tool_repetitions,
                config.resource_reads,
                directory,
                url,
            )
        else:
            running_delegate = RemoteDelegate(
                url,
                config.scenario,
                probe,
                config.telemetry,
                config.timeout,
            )
        try:
            visible_pid = await health(url)
            await running_delegate.prepare()
            yield running_delegate, ResourceTarget(pid=visible_pid)
        finally:
            await running_delegate.close()
            process.terminate()
            try:
                await asyncio.to_thread(process.wait, 5)
            except subprocess.TimeoutExpired:
                process.kill()
                await asyncio.to_thread(process.wait)
