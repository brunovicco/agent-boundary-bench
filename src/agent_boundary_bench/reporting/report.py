"""Round-level statistics, tables and reproducible Matplotlib charts."""

import csv
import json
import math
import statistics
from pathlib import Path

from agent_boundary_bench.benchmark.models import Manifest, ResourceSample, Sample
from agent_boundary_bench.benchmark.runner import file_hash


def percentile(values: list[float], quantile: float) -> float | None:
    """Use linear interpolation on sorted observations; no absent samples added."""
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * quantile
    low = int(position)
    high = min(low + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summarize(path: Path) -> dict[str, str | int | float | None]:
    """Verify hashes, counts and schema before deriving any statistics."""
    manifest = Manifest.model_validate_json(path.read_text())
    directory = path.parent
    if file_hash(directory / "samples.jsonl") != manifest.sample_sha256:
        raise ValueError(f"sample hash mismatch: {directory}")
    if file_hash(directory / "resources.jsonl") != manifest.resource_sha256:
        raise ValueError(f"resource hash mismatch: {directory}")
    samples = [
        Sample.model_validate_json(line)
        for line in (directory / "samples.jsonl").read_text().splitlines()
    ]
    if manifest.offered != math.ceil(manifest.config.rate * manifest.config.duration):
        raise ValueError("manifest offered count differs from scheduled workload")
    if len(samples) != manifest.offered or sorted(s.index for s in samples) != list(
        range(manifest.offered)
    ):
        raise ValueError("offered count/index mismatch")
    successful = [s for s in samples if s.status == "ok"]
    completed = [s for s in samples if s.status != "dropped"]
    if (
        len(successful) != manifest.succeeded
        or len(completed) != manifest.completed
        or sum(s.status == "dropped" for s in samples) != manifest.dropped
    ):
        raise ValueError("manifest outcome counts differ from raw samples")
    latencies = [s.arrival_latency_ms for s in successful]
    resources = [
        ResourceSample.model_validate_json(line)
        for line in (directory / "resources.jsonl").read_text().splitlines()
    ]
    row: dict[str, str | int | float | None] = {
        "run_id": manifest.run_id,
        "scenario": manifest.config.scenario,
        "payload_bytes": manifest.config.payload_bytes,
        "wait_ms": manifest.config.wait_ms,
        "mode": "parallel" if manifest.config.parallel else "sequential",
        "telemetry": str(manifest.config.telemetry).lower(),
        "target_rps": manifest.config.rate,
        "repetition": manifest.config.repetition,
        "n_success": len(successful),
        "offered": manifest.offered,
        "completed": len(completed),
        "dropped": manifest.dropped,
        "errors": sum(s.status == "error" for s in samples),
        "timeouts": sum(s.status == "timeout" for s in samples),
        "error_rate": (len(completed) - len(successful)) / len(completed) if completed else None,
        "effective_arrival_rps": len(completed) / manifest.arrival_window_seconds,
        "successful_throughput_rps": len(successful) / manifest.elapsed_seconds,
        "p50_ms": percentile(latencies, 0.5),
        "p95_ms": percentile(latencies, 0.95),
        "p99_ms": percentile(latencies, 0.99),
        "mean_ms": statistics.mean(latencies) if latencies else None,
        "median_ms": statistics.median(latencies) if latencies else None,
        "scheduler_lag_p95_ms": percentile([s.scheduler_lag_ms for s in completed], 0.95),
        "request_body_bytes_mean": statistics.mean(
            [s.request_bytes for s in successful if s.request_bytes is not None]
        )
        if successful
        else None,
        "response_body_bytes_mean": statistics.mean(
            [s.response_bytes for s in successful if s.response_bytes is not None]
        )
        if successful
        else None,
        "remote_calls": sum(s.remote_calls or 0 for s in successful),
        "commit_sha": manifest.commit_sha,
    }
    row["specialist_ms_mean"] = (
        statistics.mean(value for sample in successful for value in sample.specialist_ms)
        if successful
        else None
    )
    for field in ("service_duration_ms", "serialization_ms", "transport_ms"):
        values = [
            float(value) for sample in successful if (value := getattr(sample, field)) is not None
        ]
        row[field + "_mean"] = statistics.mean(values) if values else None
    for role in ("harness", "specialist"):
        points = [r for r in resources if r.role == role]
        row[role + "_peak_rss_bytes"] = max(p.rss_bytes for p in points) if points else None
        row[role + "_cpu_seconds"] = (
            points[-1].cpu_seconds - points[0].cpu_seconds if points else None
        )
    return row


def report(source: Path, output: Path) -> Path:
    """Generate a report from existing manifests, refusing an empty input."""
    manifests = sorted(source.rglob("manifest.json"))
    if not manifests:
        raise ValueError("no completed round manifests found; no report generated")
    rows = [summarize(path) for path in manifests]
    output.mkdir(parents=True, exist_ok=True)
    with (output / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    telemetry_effects(manifests, rows, output / "telemetry-deltas.csv")
    span_statistics(manifests, output / "span-summary.csv")
    lines = [
        "# Measured round results",
        "",
        "These are real observations, not illustrative numbers. One row per independent round.",
        "Latency percentiles use successful scheduled-arrival-to-completion "
        "observations, including generator delay.",
        "Errors and drops are separate; success latency is not an availability measure.",
        "P99 with small n is exploratory. No saturation or cross-hardware conclusion "
        "follows from smoke runs.",
        "",
        "| Scenario | Payload | Wait | Mode | OTel | Target RPS | n | Drops | "
        "Errors/timeouts | P50 ms | P95 ms | P99 ms |",
        "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:

        def fmt(key: str, row: dict[str, str | int | float | None] = r) -> str:
            value = row[key]
            return f"{value:.3f}" if isinstance(value, (float, int)) else "N/A"

        lines.append(
            f"| {r['scenario']} | {r['payload_bytes']} | {r['wait_ms']} | {r['mode']} | "
            f"{r['telemetry']} | {r['target_rps']} | {r['n_success']} | {r['dropped']} | "
            f"{r['errors']}/{r['timeouts']} | {fmt('p50_ms')} | {fmt('p95_ms')} | {fmt('p99_ms')} |"
        )
    lines += [
        "",
        "## Architectural Decision Insights",
        "",
        "Compare repetitions within identical workload, topology, rate and telemetry settings.",
        "A boundary's observed cost includes SDK work, codecs, kernel execution, "
        "scheduling and transport.",
        "A difference between means does not identify a causal transport component.",
        "Use isolation, independent deployment and interoperability requirements "
        "alongside measured latency budgets.",
        "A2A immediate replies do not measure durable delegation, failure recovery or "
        "remote trust boundaries.",
        "Local deployment has fewer processes; the experiment does not prove a "
        "universal topology winner.",
        "",
        "## Provenance and limits",
        "",
        "See each manifest for exact commit, hardware, constraints, versions, seed and "
        "limitations.",
        "CPU deltas and sampled peak RSS are in summary.csv. Harness CPU includes "
        "generator and supervisor.",
        "Native runs use no container image; an absent image digest is null, never an "
        "invented hash.",
        "Spans include warmup; correlate measured requests through samples.jsonl trace_id.",
    ]
    (output / "report.md").write_text("\n".join(lines) + "\n")
    plot(rows, output / "latency.png")
    return output / "report.md"


def telemetry_effects(
    manifests: list[Path],
    rows: list[dict[str, str | int | float | None]],
    path: Path,
) -> None:
    """Pair identical repeated conditions, emitting nothing for missing pairs."""
    groups: dict[str, dict[bool, list[dict[str, str | int | float | None]]]] = {}
    for manifest_path, row in zip(manifests, rows, strict=True):
        manifest = Manifest.model_validate_json(manifest_path.read_text())
        key = json.dumps(
            {
                "config": manifest.config.model_dump(exclude={"telemetry"}),
                "environment": manifest.environment,
                "commit": manifest.commit_sha,
                "lock": manifest.lock_sha256,
            },
            sort_keys=True,
        )
        group = groups.setdefault(key, {})
        group.setdefault(manifest.config.telemetry, []).append(row)
    fields = ["off_run_id", "on_run_id", "scenario", "mean_delta_ms", "p95_delta_ms"]
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for group in groups.values():
            if False not in group or True not in group:
                continue
            if len(group[False]) != 1 or len(group[True]) != 1:
                continue  # Ambiguous repeats stay in the round table, never guessed into pairs.
            off, on = group[False][0], group[True][0]
            if off["mean_ms"] is None or on["mean_ms"] is None:
                continue
            writer.writerow(
                {
                    "off_run_id": off["run_id"],
                    "on_run_id": on["run_id"],
                    "scenario": on["scenario"],
                    "mean_delta_ms": float(str(on["mean_ms"])) - float(str(off["mean_ms"])),
                    "p95_delta_ms": float(str(on["p95_ms"])) - float(str(off["p95_ms"])),
                }
            )


def span_statistics(manifests: list[Path], path: Path) -> None:
    """Summarize existing measured-trace spans only; warmup stays excluded."""
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["run_id", "service", "span", "n", "mean_ms", "p95_ms"]
        )
        writer.writeheader()
        for manifest_path in manifests:
            directory = manifest_path.parent
            trace_ids = {
                sample.trace_id
                for line in (directory / "samples.jsonl").read_text().splitlines()
                if (sample := Sample.model_validate_json(line)).trace_id is not None
            }
            groups: dict[tuple[str, str], list[float]] = {}
            for span_file in directory.glob("*-spans.jsonl"):
                for line in span_file.read_text().splitlines():
                    span = json.loads(line)
                    if span["trace_id"] in trace_ids:
                        groups.setdefault((span["service"], span["name"]), []).append(
                            span["duration_ms"]
                        )
            for (service, name), values in sorted(groups.items()):
                writer.writerow(
                    {
                        "run_id": directory.name,
                        "service": service,
                        "span": name,
                        "n": len(values),
                        "mean_ms": statistics.mean(values),
                        "p95_ms": percentile(values, 0.95),
                    }
                )


def plot(rows: list[dict[str, str | int | float | None]], path: Path) -> None:
    """Plot measured P50/P95 only, keeping missing observations absent."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    valid = [r for r in rows if r["p50_ms"] is not None]
    figure, axis = plt.subplots(figsize=(max(9, len(valid) * 0.35), 5))
    labels = [
        f"{r['scenario']}\n{r['payload_bytes']}B/{r['wait_ms']}ms\n{str(r['mode'])[:3]}/otel={r['telemetry']}\nr{r['repetition']}"
        for r in valid
    ]
    axis.plot(range(len(valid)), [float(str(r["p50_ms"])) for r in valid], "o", label="P50")
    axis.plot(range(len(valid)), [float(str(r["p95_ms"])) for r in valid], "x", label="P95")
    axis.set_xticks(range(len(valid)), labels, rotation=90, fontsize=7)
    axis.set_ylabel("Scheduled-arrival latency (ms), successes")
    axis.set_title(
        "Real measurements · individual rounds · inspect configurations before comparison"
    )
    axis.legend()
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(path, dpi=150, metadata={"Software": "agent-boundary-bench"})
    plt.close(figure)
