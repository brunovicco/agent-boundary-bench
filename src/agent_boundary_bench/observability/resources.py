"""Public OS/process observations with optional Linux cgroup v2 counters."""

from dataclasses import asdict, dataclass
from pathlib import Path

import psutil

from agent_boundary_bench.observability.process import procfs_pid

CGROUP_ROOT = Path("/sys/fs/cgroup")


@dataclass(frozen=True)
class RuntimeResourceSnapshot:
    """One process observation; unavailable cgroup fields remain null."""

    pid: int
    cpu_seconds: float
    rss_bytes: int
    cgroup_version: str | None = None
    cpu_usage_usec: int | None = None
    cpu_user_usec: int | None = None
    cpu_system_usec: int | None = None
    cpu_nr_periods: int | None = None
    cpu_nr_throttled: int | None = None
    cpu_throttled_usec: int | None = None
    cpu_limit_cores: float | None = None
    memory_current_bytes: int | None = None
    memory_peak_bytes: int | None = None
    memory_limit_bytes: int | None = None
    memory_events_low: int | None = None
    memory_events_high: int | None = None
    memory_events_max: int | None = None
    memory_events_oom: int | None = None
    memory_events_oom_kill: int | None = None
    memory_events_oom_group_kill: int | None = None

    def as_dict(self) -> dict[str, int | float | str | None]:
        """Return JSON-compatible primitives for the metadata-only resource endpoint."""
        return asdict(self)


def _flat_keyed(path: Path) -> dict[str, int]:
    """Parse cgroup flat-keyed files without assuming a stable key order."""
    if not path.is_file():
        return {}
    values: dict[str, int] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            key, raw = line.split(maxsplit=1)
            values[key] = int(raw)
    except (OSError, ValueError):
        return {}
    return values


def _integer(path: Path) -> int | None:
    """Read one numeric cgroup value, preserving unavailable or `max` as null."""
    try:
        raw = path.read_text(encoding="utf-8").strip()
        return None if raw == "max" else int(raw)
    except (OSError, ValueError):
        return None


def _cpu_limit(path: Path) -> float | None:
    """Translate cgroup v2 quota/period into CPU cores; `max` remains null."""
    try:
        quota, period = path.read_text(encoding="utf-8").split()
        if quota == "max":
            return None
        parsed_period = int(period)
        return int(quota) / parsed_period if parsed_period > 0 else None
    except (OSError, ValueError):
        return None


def _cgroup_directory(pid: int) -> Path | None:
    """Resolve the process' unified hierarchy without escaping the cgroup mount."""
    try:
        unified = next(
            line.split("::", 1)[1]
            for line in Path(f"/proc/{pid}/cgroup").read_text(encoding="utf-8").splitlines()
            if line.startswith("0::")
        )
        candidate = (CGROUP_ROOT / unified.lstrip("/")).resolve()
        root = CGROUP_ROOT.resolve()
        return candidate if candidate.is_relative_to(root) else None
    except (OSError, StopIteration):
        return None


def runtime_resource_snapshot(pid: int | None = None) -> RuntimeResourceSnapshot:
    """Read process and same-cgroup counters through stable procfs/cgroup interfaces."""
    process = psutil.Process(procfs_pid() if pid is None else pid)
    cpu = process.cpu_times()
    cgroup = _cgroup_directory(process.pid)
    cgroup_v2 = cgroup is not None and (CGROUP_ROOT / "cgroup.controllers").is_file()
    cpu_stat = _flat_keyed(cgroup / "cpu.stat") if cgroup_v2 and cgroup else {}
    memory_events = _flat_keyed(cgroup / "memory.events") if cgroup_v2 and cgroup else {}
    return RuntimeResourceSnapshot(
        pid=process.pid,
        cpu_seconds=cpu.user + cpu.system,
        rss_bytes=process.memory_info().rss,
        cgroup_version="v2" if cgroup_v2 else None,
        cpu_usage_usec=cpu_stat.get("usage_usec"),
        cpu_user_usec=cpu_stat.get("user_usec"),
        cpu_system_usec=cpu_stat.get("system_usec"),
        cpu_nr_periods=cpu_stat.get("nr_periods"),
        cpu_nr_throttled=cpu_stat.get("nr_throttled"),
        cpu_throttled_usec=cpu_stat.get("throttled_usec"),
        cpu_limit_cores=_cpu_limit(cgroup / "cpu.max") if cgroup_v2 and cgroup else None,
        memory_current_bytes=_integer(cgroup / "memory.current") if cgroup_v2 and cgroup else None,
        memory_peak_bytes=_integer(cgroup / "memory.peak") if cgroup_v2 and cgroup else None,
        memory_limit_bytes=_integer(cgroup / "memory.max") if cgroup_v2 and cgroup else None,
        memory_events_low=memory_events.get("low"),
        memory_events_high=memory_events.get("high"),
        memory_events_max=memory_events.get("max"),
        memory_events_oom=memory_events.get("oom"),
        memory_events_oom_kill=memory_events.get("oom_kill"),
        memory_events_oom_group_kill=memory_events.get("oom_group_kill"),
    )
