"""Lifecycle of local delegates and equivalent independent specialist workers."""

import asyncio
import socket
import subprocess  # nosec B404
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx

from agent_boundary_bench.adapters.local import LocalDelegate
from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.supervisor import Delegate, Probe
from agent_boundary_bench.benchmark.models import Config


def free_port() -> int:
    """Ask the OS for a loopback port; readiness catches startup/race failures."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


async def health(url: str, attempts: int = 100) -> int:
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
) -> AsyncIterator[tuple[Delegate, int | None]]:
    """Own exactly one worker for HTTP/A2A; local needs no external service."""
    if config.scenario == "local":
        yield LocalDelegate(probe), None
        return
    port = free_port()
    url = f"http://127.0.0.1:{port}"
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
    if config.telemetry:
        command += ["--trace-file", str(directory / "specialist-spans.jsonl")]
    with (directory / "specialist.log").open("w", encoding="utf-8") as logfile:
        process = subprocess.Popen(command, stdout=logfile, stderr=logfile)  # noqa: S603  # nosec B603
        delegate = RemoteDelegate(url, config.scenario, probe, config.telemetry, config.timeout)
        try:
            visible_pid = await health(url)
            await delegate.prepare()
            yield delegate, visible_pid
        finally:
            await delegate.close()
            process.terminate()
            try:
                await asyncio.to_thread(process.wait, 5)
            except subprocess.TimeoutExpired:
                process.kill()
                await asyncio.to_thread(process.wait)
