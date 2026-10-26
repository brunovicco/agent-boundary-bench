#!/usr/bin/env python3
"""Capture host, Docker, image and Git facts beside a container campaign."""

import argparse
import hashlib
import json
import platform
import shutil
import subprocess  # nosec B404
from datetime import UTC, datetime
from pathlib import Path

import psutil


def command(*arguments: str) -> str:
    """Run one resolved executable and return its exact standard output."""
    executable = shutil.which(arguments[0])
    if executable is None:
        raise RuntimeError(f"required executable is unavailable: {arguments[0]}")
    return subprocess.check_output(  # noqa: S603  # nosec B603
        [executable, *arguments[1:]],
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def optional_command(*arguments: str) -> str | None:
    """Return null for unavailable provenance rather than inventing a value."""
    try:
        return command(*arguments)
    except (OSError, RuntimeError, subprocess.CalledProcessError):
        return None


def main() -> int:
    """Write one deterministic-shape, real environment observation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--image", default="agent-boundary-bench:0.3.0-dev0")
    args = parser.parse_args()
    lock = Path("uv.lock")
    record = {
        "schema_version": "1",
        "captured_at": datetime.now(UTC).isoformat(),
        "host": {
            "platform": platform.platform(),
            "architecture": platform.machine(),
            "logical_cpus": psutil.cpu_count(),
            "physical_cpus": psutil.cpu_count(logical=False),
            "memory_bytes": psutil.virtual_memory().total,
        },
        "git": {
            "commit_sha": optional_command("git", "rev-parse", "HEAD"),
            "status_porcelain": optional_command("git", "status", "--porcelain"),
            "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest()
            if lock.is_file()
            else None,
        },
        "docker_version": command("docker", "version", "--format", "{{json .}}"),
        "compose_version": command("docker", "compose", "version", "--short"),
        "image_inspect": command(
            "docker",
            "image",
            "inspect",
            args.image,
            "--format",
            "{{json .}}",
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
