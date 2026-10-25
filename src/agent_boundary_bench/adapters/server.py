"""Equivalent one-worker specialist servers using public FastAPI and A2A routes."""

from time import perf_counter
from uuid import uuid4

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import (
    add_a2a_routes_to_fastapi,
    create_agent_card_routes,
    create_jsonrpc_routes,
)
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill, Message, Part, Role
from fastapi import FastAPI, HTTPException, Request
from pydantic import ValidationError

from agent_boundary_bench.adapters.contracts import TASK, Reply
from agent_boundary_bench.application.supervisor import NullProbe, Probe
from agent_boundary_bench.domain.credit import AnalysisTask, Specialist, execute
from agent_boundary_bench.observability import Telemetry, TraceMiddleware
from agent_boundary_bench.observability.process import procfs_pid


async def process(task: AnalysisTask, probe: Probe) -> Reply:
    """Measure the same shared kernel, without serialization, at the specialist."""
    with probe.span("specialist.process"):
        started = perf_counter()
        result = await execute(task)
        return Reply(result=result, specialist_ms=(perf_counter() - started) * 1000)


class CreditExecutor(AgentExecutor):
    """A2A immediate Message response; no task persistence or polling workload."""

    def __init__(self, probe: Probe) -> None:
        """Inject application observation."""
        self.probe = probe

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Translate the SDK message, execute shared logic and enqueue one reply."""
        task = TASK.validate_json(context.get_user_input())
        reply = await process(task, self.probe)
        await event_queue.enqueue_event(
            Message(
                message_id=str(uuid4()),
                role=Role.ROLE_AGENT,
                parts=[Part(text=reply.model_dump_json(), media_type="application/json")],
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Immediate responses expose no resumable task to cancel."""
        raise ValueError("immediate Message execution has no cancellable task")


def create_app(scenario: str, url: str, telemetry: Telemetry | None = None) -> FastAPI:
    """Serve all three skills in one worker for both remote scenarios."""
    app = FastAPI(title="Agent Boundary Bench specialist", docs_url=None, redoc_url=None)
    probe: Probe = telemetry if telemetry else NullProbe()
    app.add_middleware(TraceMiddleware, telemetry=telemetry)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "scenario": scenario,
            "version": "0.1.0",
            "procfs_pid": str(procfs_pid()),
        }

    if scenario == "http":

        @app.post("/analyze")
        async def analyze(request: Request) -> Reply:
            try:
                task = TASK.validate_json(await request.body())
                return await process(task, probe)
            except (ValidationError, ValueError) as exc:
                raise HTTPException(status_code=422, detail="invalid synthetic task") from exc
    elif scenario == "a2a":
        card = AgentCard(
            name="Synthetic credit specialists",
            description="Deterministic synthetic credit rules",
            version="0.1.0",
            capabilities=AgentCapabilities(streaming=False),
            default_input_modes=["application/json"],
            default_output_modes=["application/json"],
            supported_interfaces=[
                AgentInterface(
                    url=url + "/rpc",
                    protocol_binding="JSONRPC",
                    protocol_version="1.0",
                )
            ],
            skills=[
                AgentSkill(
                    id=s.value,
                    name=s.value,
                    description="Synthetic " + s.value,
                    tags=["synthetic"],
                )
                for s in Specialist
            ],
        )
        handler = DefaultRequestHandler(CreditExecutor(probe), InMemoryTaskStore(), card)
        add_a2a_routes_to_fastapi(
            app,
            agent_card_routes=create_agent_card_routes(card),
            jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/rpc"),
        )
    else:
        raise ValueError("server scenario must be http or a2a")
    return app
