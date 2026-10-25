"""Run an independent k6 arrival smoke, retaining distinct topology and provenance."""

import argparse
import asyncio
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess  # nosec B404
import sys
from datetime import UTC, datetime
from pathlib import Path

from agent_boundary_bench.benchmark.runner import environment, file_hash, git_value
from agent_boundary_bench.benchmark.runtime import free_port, health


def main() -> None:
    """Own a gateway and its child, then run a fixed-rate k6 workload."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=[
            "local",
            "http",
            "a2a",
            "mcp-inprocess",
            "mcp-stdio",
            "mcp-streamable-http",
        ],
        required=True,
    )
    parser.add_argument("--k6-path", default=shutil.which("k6"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", default="2s")
    parser.add_argument("--rate", type=int, default=5)
    args = parser.parse_args()
    if not args.k6_path:
        parser.error("install k6 or provide --k6-path")
    binary = str(Path(args.k6_path).resolve())
    args.output.mkdir(parents=True, exist_ok=False)
    started = datetime.now(UTC).isoformat()
    port = free_port()
    gateway_command = [
        sys.executable,
        "-m",
        "agent_boundary_bench.entrypoints.cli",
        "gateway",
        "--scenario",
        args.scenario,
        "--port",
        str(port),
        "--output",
        str(args.output / "gateway"),
    ]
    with (args.output / "gateway.log").open("w") as logfile:
        child = subprocess.Popen(gateway_command, stdout=logfile, stderr=logfile)  # noqa: S603  # nosec B603
        try:
            asyncio.run(health(f"http://127.0.0.1:{port}"))
            env = os.environ.copy()
            env.update(
                ABB_URL=f"http://127.0.0.1:{port}",
                ABB_RATE=str(args.rate),
                ABB_DURATION=args.duration,
                ABB_VUS="64",
            )
            command = [
                binary,
                "run",
                "--out",
                f"json={args.output / 'raw.jsonl'}",
                "--summary-export",
                str(args.output / "summary.json"),
                "k6/arrival.js",
            ]
            with (args.output / "k6.log").open("w") as k6log:
                result = subprocess.run(command, env=env, stdout=k6log, stderr=k6log, check=False)  # noqa: S603  # nosec B603
        finally:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
    version = subprocess.check_output([binary, "version"], text=True).strip()  # noqa: S603  # nosec B603
    summary = json.loads((args.output / "summary.json").read_text())
    metrics = summary["metrics"]
    completed = int(metrics["abb_measured_completed"]["count"])
    dropped = int(metrics.get("dropped_iterations", {}).get("count", 0))
    record = {
        "schema_version": "k6-smoke-1",
        "python": platform.python_version(),
        "packages": {
            name: importlib.metadata.version(name)
            for name in (
                "a2a-sdk",
                "fastapi",
                "httpx",
                "pydantic",
                "uvicorn",
                "opentelemetry-sdk",
                "mcp",
                "mcp-types",
                "httpx2",
            )
        },
        "started_at": started,
        "completed_at": datetime.now(UTC).isoformat(),
        "scenario": args.scenario,
        "rate": args.rate,
        "duration": args.duration,
        "preallocated_vus": 64,
        "warmup": 3,
        "seed": 42,
        "payload_bytes": 1024,
        "wait_ms": 0,
        "parallel": False,
        "telemetry": False,
        "specialist_repetitions": 1,
        "fanout_limit": 64,
        "context_copies": 0,
        "tool_repetitions": 1,
        "resource_reads": 0,
        "k6_version": version,
        "commit_sha": git_value("rev-parse", "HEAD"),
        "git_dirty": bool(git_value("status", "--porcelain")),
        "environment": environment(),
        "lock_sha256": file_hash(Path("uv.lock")),
        "topology": "k6 -> common HTTP gateway -> selected boundary; same-host loopback",
        "image_digest": None,
        "exit_code": result.returncode,
        "offered": completed + dropped,
        "completed": completed,
        "dropped": dropped,
        "errors": int(metrics["abb_measured_errors"]["count"]),
        "raw_sha256": file_hash(args.output / "raw.jsonl"),
        "limitations": [
            "Generator and application share a host.",
            "k6 timers/topology differ from native harness; do not pool.",
            "No process CPU/RSS collection in supplemental k6 smoke.",
        ],
    }
    (args.output / "k6-manifest.json").write_text(json.dumps(record, indent=2) + "\n")
    if result.returncode:
        raise SystemExit(result.returncode)
    print(args.output)


if __name__ == "__main__":
    main()
