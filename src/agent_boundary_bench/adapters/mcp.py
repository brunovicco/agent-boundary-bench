"""Official MCP v2 tool/resource adapters for three distinct transport boundaries."""

import os
import sys
from collections.abc import Mapping
from contextlib import AsyncExitStack
from dataclasses import asdict
from pathlib import Path
from time import perf_counter
from typing import Any, cast

import httpx2
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.server import MCPServer
from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp_types import RequestParamsMeta, TextContent, TextResourceContents
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from agent_boundary_bench.adapters.contracts import TASK, Reply
from agent_boundary_bench.application.supervisor import Invocation, NullProbe, Probe
from agent_boundary_bench.domain.credit import AnalysisTask, canonical, execute, fixture
from agent_boundary_bench.observability import Telemetry, headers
from agent_boundary_bench.observability.process import procfs_pid

MCP_PROTOCOL_VERSION = "2026-07-28"
MCP_SCENARIOS = frozenset({"mcp-inprocess", "mcp-stdio", "mcp-streamable-http"})


def trace_metadata(enabled: bool) -> RequestParamsMeta | None:
    """Build typed MCP metadata using the public request-level propagation seam."""
    # RequestParamsMeta permits protocol extension keys (PEP 728 extra_items);
    # cast bridges Mypy's current TypedDict representation of that public type.
    carrier = cast(RequestParamsMeta, headers(enabled))
    return carrier or None


class MCPTraceMiddleware:
    """Correlate SDK requests with the harness tracer without global-provider mutation."""

    def __init__(self, telemetry: Telemetry) -> None:
        """Retain the isolated tracer used by this experimental arm."""
        self.telemetry = telemetry

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        """Extract the SDK-propagated W3C carrier from public request metadata."""
        carrier: Mapping[str, object] | None = ctx.meta
        with self.telemetry.remote_span("mcp.transport.server", carrier):
            return await call_next(ctx)


def create_mcp_server(telemetry: Telemetry | None = None) -> MCPServer[dict[str, Any]]:
    """Build one tool/resource server around the shared deterministic kernel."""
    middleware = [MCPTraceMiddleware(telemetry)] if telemetry else None
    server: MCPServer[dict[str, Any]] = MCPServer(
        "agent-boundary-bench-tools",
        description="Synthetic credit tools for boundary experiments",
        version="0.2.0",
        middleware=middleware,
        subscriptions=False,
    )

    @server.tool(
        name="analyze_credit",
        description="Run one deterministic synthetic specialist rule",
        structured_output=False,
    )
    async def analyze_credit(task_json: str, context: list[str]) -> str:
        if len(context) > 16 or any(copy != task_json for copy in context):
            raise ValueError("synthetic context must contain at most 16 exact task copies")
        task = TASK.validate_json(task_json)
        probe: Probe = telemetry if telemetry else NullProbe()
        with probe.span("specialist.process"):
            started = perf_counter()
            result = await execute(task)
            reply = Reply(result=result, specialist_ms=(perf_counter() - started) * 1000)
        return reply.model_dump_json()

    @server.resource(
        "credit://fixture/{size}/{seed}",
        name="synthetic_credit_fixture",
        description="Versioned deterministic synthetic credit case",
        mime_type="application/json",
    )
    def synthetic_credit_fixture(size: str, seed: str) -> str:
        case = fixture(int(size), int(seed))
        return canonical(asdict(case)).decode()

    async def health(_request: Request) -> Response:
        return JSONResponse(
            {
                "status": "ok",
                "scenario": "mcp-streamable-http",
                "version": "0.2.0",
                "procfs_pid": str(procfs_pid()),
            }
        )

    server.custom_route("/health", methods=["GET"], include_in_schema=False)(health)

    return server


class MCPDelegate:
    """Persistent official v2 client implementing the application's Delegate port."""

    def __init__(
        self,
        scenario: str,
        probe: Probe,
        timeout: float,
        context_copies: int,
        tool_repetitions: int,
        resource_reads: int,
        directory: Path,
        url: str | None = None,
    ) -> None:
        """Configure one persistent client and its MCP workload shape."""
        if scenario not in MCP_SCENARIOS:
            raise ValueError("unknown MCP scenario")
        self.scenario = scenario
        self.probe = probe
        self.timeout = timeout
        self.context_copies = context_copies
        self.tool_repetitions = tool_repetitions
        self.resource_reads = resource_reads
        self.directory = directory
        self.url = url
        self.trace_enabled = isinstance(probe, Telemetry)
        self.stack = AsyncExitStack()
        self.client: Client | None = None
        self.protocol_version: str | None = None

    async def prepare(self) -> None:
        """Connect once and move protocol discovery/listing outside warmup and measurement."""
        telemetry = self.probe if isinstance(self.probe, Telemetry) else None
        target: object
        if self.scenario == "mcp-inprocess":
            target = create_mcp_server(telemetry)
        elif self.scenario == "mcp-stdio":
            error_stream = self.stack.enter_context(
                (self.directory / "specialist.log").open("w", encoding="utf-8")
            )
            args = [
                "-m",
                "agent_boundary_bench.entrypoints.cli",
                "mcp-serve",
                "--transport",
                "stdio",
            ]
            if telemetry:
                args += ["--trace-file", str(self.directory / "specialist-spans.jsonl")]
            coverage_env = {
                key: value for key, value in os.environ.items() if key.startswith("COVERAGE_")
            }
            params = StdioServerParameters(
                command=sys.executable,
                args=args,
                env=coverage_env,
                cwd=Path.cwd(),
            )
            target = stdio_client(params, errlog=error_stream)
        else:
            if self.url is None:
                raise ValueError("Streamable HTTP requires a URL")
            http = await self.stack.enter_async_context(
                httpx2.AsyncClient(
                    timeout=httpx2.Timeout(self.timeout),
                    trust_env=False,
                    http2=False,
                    limits=httpx2.Limits(
                        max_connections=128,
                        max_keepalive_connections=128,
                    ),
                )
            )
            target = streamable_http_client(
                self.url + "/mcp",
                http_client=http,
                terminate_on_close=False,
            )
        client = Client(target, read_timeout_seconds=self.timeout, cache=None)
        self.client = await self.stack.enter_async_context(client)
        self.protocol_version = self.client.protocol_version
        if self.protocol_version != MCP_PROTOCOL_VERSION:
            raise RuntimeError(f"unexpected MCP protocol version: {self.protocol_version}")
        tools = await self.client.list_tools(cache_mode="bypass")
        templates = await self.client.list_resource_templates(cache_mode="bypass")
        if {tool.name for tool in tools.tools} != {"analyze_credit"}:
            raise RuntimeError("MCP tool discovery differs from the experiment contract")
        if not any(
            template.uri_template == "credit://fixture/{size}/{seed}"
            for template in templates.resource_templates
        ):
            raise RuntimeError("MCP fixture resource template is unavailable")

    async def invoke(self, task: AnalysisTask) -> Invocation:
        """Call tools/resources repeatedly while returning one oracle-compatible result."""
        if self.client is None:
            raise RuntimeError("prepare MCP client before tool access")
        request_bytes = 0
        response_bytes = 0
        specialist_ms = 0.0
        serialization_ms = 0.0
        transport_ms = 0.0
        selected: Reply | None = None

        started = perf_counter()
        with self.probe.span("serialization.encode"):
            task_payload = TASK.dump_json(task)
            task_json = task_payload.decode()
            arguments = {
                "task_json": task_json,
                "context": [task_json] * self.context_copies,
            }
            encoded_arguments = canonical(arguments)
        serialization_ms += (perf_counter() - started) * 1000

        with self.probe.span("delegation." + self.scenario):
            for _ in range(self.tool_repetitions):
                started = perf_counter()
                with self.probe.span("transport.client"):
                    result = await self.client.call_tool(
                        "analyze_credit",
                        arguments,
                        read_timeout_seconds=self.timeout,
                        meta=trace_metadata(self.trace_enabled),
                    )
                transport_ms += (perf_counter() - started) * 1000
                request_bytes += len(encoded_arguments)
                if result.is_error or len(result.content) != 1:
                    raise ValueError("MCP tool returned an error or unexpected content count")
                content = result.content[0]
                if not isinstance(content, TextContent):
                    raise ValueError("MCP tool did not return text content")
                reply_json = content.text.encode()
                response_bytes += len(reply_json)
                started = perf_counter()
                with self.probe.span("serialization.decode"):
                    reply = Reply.model_validate_json(reply_json)
                serialization_ms += (perf_counter() - started) * 1000
                if selected is not None and reply.result != selected.result:
                    raise ValueError("repeated MCP tool calls returned different business results")
                selected = reply
                specialist_ms += reply.specialist_ms

            resource_uri = f"credit://fixture/{len(canonical(asdict(task.case)))}/{task.case.case_id.removeprefix('synthetic-')}"
            for _ in range(self.resource_reads):
                started = perf_counter()
                with self.probe.span("transport.client.resource"):
                    resource = await self.client.read_resource(
                        resource_uri,
                        meta=trace_metadata(self.trace_enabled),
                        cache_mode="bypass",
                    )
                transport_ms += (perf_counter() - started) * 1000
                request_bytes += len(resource_uri.encode())
                if len(resource.contents) != 1 or not isinstance(
                    resource.contents[0], TextResourceContents
                ):
                    raise ValueError("MCP resource returned an unexpected content shape")
                resource_body = resource.contents[0].text.encode()
                response_bytes += len(resource_body)
                if resource_body != canonical(asdict(task.case)):
                    raise ValueError("MCP resource differs from the delegated synthetic fixture")

        if selected is None:
            raise RuntimeError("MCP tool repetition count produced no result")
        return Invocation(
            selected.result,
            specialist_ms,
            request_bytes,
            response_bytes,
            serialization_ms,
            transport_ms,
            self.tool_repetitions + self.resource_reads,
            self.tool_repetitions,
            self.resource_reads,
            len(task_payload) * self.context_copies * self.tool_repetitions,
        )

    async def close(self) -> None:
        """Close client, transport, subprocess/file handles and HTTP pool in order."""
        await self.stack.aclose()
