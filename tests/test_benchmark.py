"""Load scheduling, failure accounting, data integrity and reporting tests."""

import json
from pathlib import Path

import pytest

from agent_boundary_bench.adapters.local import LocalDelegate
from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.supervisor import Invocation, NullProbe, supervise
from agent_boundary_bench.benchmark.models import Config, Manifest, ResourceSample
from agent_boundary_bench.benchmark.runner import arrivals, has_timeout, one, run
from agent_boundary_bench.benchmark.runtime import runtime
from agent_boundary_bench.domain.credit import AnalysisTask, evaluate, fixture
from agent_boundary_bench.entrypoints.cli import campaign_configs, validate
from agent_boundary_bench.reporting.report import percentile, report, summarize


async def test_open_arrivals_retain_drops() -> None:
    config = Config(rate=100, duration=0.1, wait_ms=250, concurrency=1)
    samples, elapsed = await arrivals(
        config, LocalDelegate(NullProbe()), fixture(1024), NullProbe()
    )
    assert len(samples) == 10
    assert sum(s.status == "dropped" for s in samples) == 9
    assert samples[0].status == "ok"
    assert elapsed >= 0.7
    assert [s.index for s in samples] == list(range(10))


async def test_timeout_and_error_observations() -> None:
    import time

    now = time.perf_counter()
    sample = await one(
        0,
        now,
        now,
        Config(wait_ms=250, timeout=0.001),
        LocalDelegate(NullProbe()),
        fixture(1024),
        NullProbe(),
    )
    assert sample.status == "timeout"
    assert sample.remote_calls is None
    assert has_timeout(ExceptionGroup("group", [TimeoutError()]))

    class Broken:
        async def invoke(
            self,
            task: AnalysisTask,
            *,
            delegation_id: str | None = None,
            attempt: int = 1,
        ) -> Invocation:
            del delegation_id, attempt
            raise ValueError("bad data")

    sample = await one(0, now, now, Config(), Broken(), fixture(1024), NullProbe())
    assert sample.status == "error"
    with pytest.raises(ExceptionGroup):
        await supervise(Broken(), fixture(1024), 0, True, 1, NullProbe())


async def test_raw_manifest_and_report(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Native manifest assertions must not depend on Docker evidence variables
    # exported by a developer's interactive shell.
    monkeypatch.delenv("ABB_IMAGE_DIGEST", raising=False)
    monkeypatch.delenv("ABB_ISOLATION_LABEL", raising=False)
    directory = await run(Config(rate=5, duration=0.4, telemetry=True), tmp_path / "raw")
    manifest = Manifest.model_validate_json((directory / "manifest.json").read_text())
    assert manifest.offered == manifest.succeeded == 2
    assert manifest.commit_sha is None or len(manifest.commit_sha) == 40
    assert manifest.packages["a2a-sdk"] == "1.2.3"
    assert manifest.image_hashes["application"] is None
    assert manifest.warmup_succeeded == manifest.config.warmup
    assert manifest.warmup_failed == 0
    assert manifest.schema_version == "4"
    assert manifest.resource_sampling["interval_ms"] == 100
    assert manifest.resource_sampling["request_timeout_seconds"] == 5.0
    summary = summarize(directory / "manifest.json")
    assert summary["n_success"] == 2
    assert summary["specialist_peak_rss_bytes"] is None
    assert summary["cpu_iterations"] == 0
    assert summary["memory_bytes"] == 0
    await run(Config(rate=5, duration=0.4, telemetry=False), tmp_path / "raw")
    output = report(tmp_path / "raw", tmp_path / "report")
    assert "real observations" in output.read_text()
    assert (output.parent / "latency.png").stat().st_size > 1000
    assert len((output.parent / "telemetry-deltas.csv").read_text().splitlines()) == 2
    assert len((output.parent / "span-summary.csv").read_text().splitlines()) > 1
    for csv_name in ("summary.csv", "telemetry-deltas.csv", "span-summary.csv"):
        assert b"\r\n" not in (output.parent / csv_name).read_bytes()
    # Reports must reject missing/tampered samples rather than fill them in.
    (directory / "samples.jsonl").write_text("")
    with pytest.raises(ValueError, match="hash mismatch"):
        summarize(directory / "manifest.json")
    with pytest.raises(ValueError, match="no completed"):
        report(tmp_path / "empty", tmp_path / "empty-report")


async def test_external_worker_resource_series_and_topology(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service_directory = tmp_path / "service"
    service_directory.mkdir()
    config = Config(scenario="http", rate=2, duration=0.5, warmup=1)
    async with runtime(config, NullProbe(), service_directory) as (delegate, _):
        assert isinstance(delegate, RemoteDelegate)
        monkeypatch.setenv("ABB_HTTP_ENDPOINT", delegate.url)
        monkeypatch.setenv("ABB_ISOLATION_LABEL", "integration-test")
        directory = await run(config, tmp_path / "raw-external")

    manifest = Manifest.model_validate_json((directory / "manifest.json").read_text())
    assert manifest.network["topology"] == "explicit external service endpoint"
    assert manifest.network["specialist_resource_endpoint"] == delegate.url
    isolation = manifest.environment["resource_isolation"]
    assert isinstance(isolation, dict)
    assert isolation["label"] == "integration-test"
    assert set(isolation) == {
        "label",
        "cgroup_version",
        "cpu_limit_cores",
        "memory_limit_bytes",
    }
    resources = [
        ResourceSample.model_validate_json(line)
        for line in (directory / "resources.jsonl").read_text().splitlines()
    ]
    assert {sample.role for sample in resources} == {"harness", "specialist"}
    assert manifest.resource_sampling["failures"] == {"harness": 0, "specialist": 0}


def test_statistics_campaign_and_fixtures(tmp_path: Path) -> None:
    assert percentile([], 0.5) is None
    assert percentile([1, 2, 3], 0.5) == 2
    assert percentile([1, 2, 3], 0.95) == pytest.approx(2.9)
    validate()
    full = campaign_configs(Path("experiments/full.json"))
    assert len(full) == 1620
    assert full == campaign_configs(Path("experiments/full.json"))
    assert {c.repetition for c in full} == set(range(5))
    assert len(campaign_configs(Path("experiments/mcp-smoke.json"))) == 24
    assert len(campaign_configs(Path("experiments/mcp-pilot.json"))) == 120
    assert len(campaign_configs(Path("experiments/mcp-full.json"))) == 1620
    assert len(campaign_configs(Path("experiments/mcp-amplification-full.json"))) == 1440
    assert len(campaign_configs(Path("experiments/resilience-smoke.json"))) == 24
    assert len(campaign_configs(Path("experiments/resilience-full.json"))) == 1920
    assert len(campaign_configs(Path("experiments/timeout-smoke.json"))) == 3
    assert len(campaign_configs(Path("experiments/timeout-full.json"))) == 120
    assert len(campaign_configs(Path("experiments/backpressure-smoke.json"))) == 18
    assert len(campaign_configs(Path("experiments/backpressure-full.json"))) == 270
    assert len(campaign_configs(Path("experiments/resource-isolation-smoke.json"))) == 12
    assert len(campaign_configs(Path("experiments/resource-isolation-full.json"))) == 180
    data = json.loads(Path("experiments/full.json").read_text())
    data["repetitions"] = 1
    path = tmp_path / "invalid.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="five repetitions"):
        campaign_configs(path)
    with pytest.raises(ValueError, match="only for MCP"):
        Config(scenario="a2a", context_copies=1)
    with pytest.raises(ValueError, match="concurrent memory"):
        Config(parallel=True, memory_bytes=64 * 1024 * 1024, specialist_repetitions=2)


async def test_bounded_generalized_fanout() -> None:
    class CountingDelegate:
        def __init__(self) -> None:
            self.active = 0
            self.peak = 0

        async def invoke(
            self,
            task: AnalysisTask,
            *,
            delegation_id: str | None = None,
            attempt: int = 1,
        ) -> Invocation:
            import asyncio

            del delegation_id, attempt
            self.active += 1
            self.peak = max(self.peak, self.active)
            try:
                await asyncio.sleep(0.005)
                return Invocation(evaluate(task), 5)
            finally:
                self.active -= 1

    delegate = CountingDelegate()
    result = await supervise(
        delegate,
        fixture(1024),
        0,
        True,
        1,
        NullProbe(),
        specialist_repetitions=4,
        fanout_limit=2,
    )
    assert len(result.invocations) == 12
    assert delegate.peak == 2
