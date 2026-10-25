"""In-process delegation adapter."""

from time import perf_counter

from agent_boundary_bench.application.supervisor import Invocation, Probe
from agent_boundary_bench.domain.credit import AnalysisTask, execute


class LocalDelegate:
    """Call the shared kernel through the typed port without network services."""

    def __init__(self, probe: Probe) -> None:
        """Inject observation without global telemetry requirements."""
        self.probe = probe

    async def invoke(self, task: AnalysisTask) -> Invocation:
        """Measure only kernel execution as specialist time."""
        with self.probe.span("delegation.local"), self.probe.span("specialist.process"):
            start = perf_counter()
            result = await execute(task)
            return Invocation(result, (perf_counter() - start) * 1000)
