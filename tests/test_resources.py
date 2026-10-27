"""Linux cgroup parsing and explicitly nullable resource observations."""

from pathlib import Path

import pytest

from agent_boundary_bench.observability import resources


def test_cgroup_v2_snapshot_reads_limits_counters_and_events(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cgroup = tmp_path / "benchmark"
    cgroup.mkdir()
    (tmp_path / "cgroup.controllers").write_text("cpu memory\n")
    (cgroup / "cpu.max").write_text("50000 100000\n")
    (cgroup / "cpu.stat").write_text(
        "usage_usec 123456\nuser_usec 100000\nsystem_usec 23456\n"
        "nr_periods 20\nnr_throttled 4\nthrottled_usec 9000\n"
    )
    (cgroup / "memory.current").write_text("1048576\n")
    (cgroup / "memory.peak").write_text("2097152\n")
    (cgroup / "memory.max").write_text("268435456\n")
    (cgroup / "memory.events").write_text(
        "low 1\nhigh 2\nmax 3\noom 4\noom_kill 5\noom_group_kill 6\n"
    )
    monkeypatch.setattr(resources, "CGROUP_ROOT", tmp_path)
    monkeypatch.setattr(resources, "_cgroup_directory", lambda _pid: cgroup)

    snapshot = resources.runtime_resource_snapshot()

    assert snapshot.cgroup_version == "v2"
    assert snapshot.cpu_limit_cores == 0.5
    assert snapshot.cpu_usage_usec == 123456
    assert snapshot.cpu_nr_throttled == 4
    assert snapshot.memory_current_bytes == 1048576
    assert snapshot.memory_peak_bytes == 2097152
    assert snapshot.memory_limit_bytes == 268435456
    assert snapshot.memory_events_oom_kill == 5


def test_cgroup_unlimited_and_malformed_values_stay_null(tmp_path: Path) -> None:
    (tmp_path / "cpu.max").write_text("max 100000\n")
    (tmp_path / "memory.max").write_text("max\n")
    (tmp_path / "invalid").write_text("not-a-number\n")
    assert resources._cpu_limit(tmp_path / "cpu.max") is None
    assert resources._integer(tmp_path / "memory.max") is None
    assert resources._integer(tmp_path / "invalid") is None
    assert resources._flat_keyed(tmp_path / "missing") == {}
