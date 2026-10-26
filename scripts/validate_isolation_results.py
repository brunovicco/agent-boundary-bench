#!/usr/bin/env python3
"""Validate completed isolation evidence against observed cgroup v2 limits."""

import argparse
import json
import math
from pathlib import Path

from agent_boundary_bench.benchmark.models import Manifest, ResourceSample
from agent_boundary_bench.reporting.report import summarize


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--harness-cpus", type=float, required=True)
    parser.add_argument("--specialist-cpus", type=float, required=True)
    parser.add_argument("--harness-memory-bytes", type=int, required=True)
    parser.add_argument("--specialist-memory-bytes", type=int, required=True)
    parser.add_argument("--max-sampling-failure-rate", type=float, default=0.5)
    parser.add_argument("--require-image-digest", action="store_true")
    return parser.parse_args()


def observed_limit(samples: list[ResourceSample], role: str, field: str) -> set[int | float]:
    """Return every non-null observed value for one role/field."""
    return {
        value
        for sample in samples
        if sample.role == role and (value := getattr(sample, field)) is not None
    }


def validate(args: argparse.Namespace) -> None:
    """Reject incomplete, unhashed or differently constrained campaign output."""
    if not 0 <= args.max_sampling_failure_rate <= 1:
        raise ValueError("max sampling failure rate must be between zero and one")
    campaign_path = args.input / "campaign.json"
    campaign = json.loads(campaign_path.read_text())
    planned = len(campaign["order"])
    completed = campaign["completed"]
    if len(completed) != planned:
        raise ValueError(f"campaign incomplete: {len(completed)}/{planned}")
    total_attempts = 0
    total_failures = 0
    for run_id in completed:
        directory = args.input / str(run_id)
        manifest_path = directory / "manifest.json"
        summarize(manifest_path)
        manifest = Manifest.model_validate_json(manifest_path.read_text())
        isolation = manifest.environment.get("resource_isolation")
        label = isolation.get("label") if isinstance(isolation, dict) else None
        if label != args.label:
            raise ValueError(f"{run_id}: isolation label {label!r} != {args.label!r}")
        if args.require_image_digest and not str(
            manifest.image_hashes.get("application") or ""
        ).startswith("sha256:"):
            raise ValueError(f"{run_id}: application image digest is absent")
        expected_roles = (
            {"harness"} if manifest.config.scenario == "local" else {"harness", "specialist"}
        )
        failures = manifest.resource_sampling.get("failures")
        attempts = manifest.resource_sampling.get("attempts")
        if not isinstance(failures, dict) or not isinstance(attempts, dict):
            raise ValueError(f"{run_id}: invalid resource sampling counts")
        if set(attempts) != expected_roles or set(failures) != expected_roles:
            raise ValueError(f"{run_id}: sampling roles do not match {expected_roles}")
        for role, raw_attempts in attempts.items():
            raw_failures = failures.get(role)
            if (
                not isinstance(raw_attempts, int)
                or isinstance(raw_attempts, bool)
                or raw_attempts <= 0
                or not isinstance(raw_failures, int)
                or isinstance(raw_failures, bool)
                or not 0 <= raw_failures <= raw_attempts
            ):
                raise ValueError(f"{run_id}: invalid sampling counts for {role}")
            failure_rate = raw_failures / raw_attempts
            if failure_rate > args.max_sampling_failure_rate:
                raise ValueError(
                    f"{run_id}: {role} sampling failure rate "
                    f"{failure_rate:.3f} exceeds {args.max_sampling_failure_rate:.3f}"
                )
            total_attempts += raw_attempts
            total_failures += raw_failures
        samples = [
            ResourceSample.model_validate_json(line)
            for line in (directory / "resources.jsonl").read_text().splitlines()
        ]
        if {sample.role for sample in samples} != expected_roles:
            raise ValueError(f"{run_id}: resource roles do not match {expected_roles}")
        for role in expected_roles:
            role_samples = [sample for sample in samples if sample.role == role]
            if len(role_samples) < 2 or any(
                sample.cgroup_version != "v2" for sample in role_samples
            ):
                raise ValueError(f"{run_id}: insufficient cgroup v2 samples for {role}")
            expected_cpu = args.harness_cpus if role == "harness" else args.specialist_cpus
            expected_memory = (
                args.harness_memory_bytes if role == "harness" else args.specialist_memory_bytes
            )
            cpu_limits = observed_limit(samples, role, "cpu_limit_cores")
            memory_limits = observed_limit(samples, role, "memory_limit_bytes")
            if len(cpu_limits) != 1 or not math.isclose(
                float(next(iter(cpu_limits))), expected_cpu
            ):
                raise ValueError(f"{run_id}: {role} CPU limits {cpu_limits!r}")
            if memory_limits != {expected_memory}:
                raise ValueError(f"{run_id}: {role} memory limits {memory_limits!r}")
    print(
        f"isolation evidence valid: {len(completed)}/{planned} rounds ({args.label}); "
        f"sampling failures: {total_failures}/{total_attempts}"
    )


def main() -> int:
    """CLI entrypoint."""
    validate(arguments())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
