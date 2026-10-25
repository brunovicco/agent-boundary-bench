"""Process identifiers as exposed by the mounted procfs, including PID namespaces."""

import os
from pathlib import Path


def procfs_pid() -> int:
    """Resolve our procfs-visible PID when procfs is mounted from a parent namespace."""
    status = Path("/proc/self/status")
    if status.exists():
        for line in status.read_text().splitlines():
            if line.startswith("Pid:"):
                return int(line.split()[1])
    return os.getpid()
