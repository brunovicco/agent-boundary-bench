"""Persistent HTTP/1.1 and A2A JSON-RPC clients with equivalent connection limits."""

import asyncio
from contextvars import ContextVar
from dataclasses import dataclass
from time import perf_counter
from uuid import uuid4

import httpx
from a2a.client import A2ACardResolver, Client, ClientConfig, ClientFactory
from a2a.client.errors import A2AClientTimeoutError
from a2a.types import Message, Part, Role, SendMessageConfiguration, SendMessageRequest

from agent_boundary_bench.adapters.contracts import TASK, Reply
from agent_boundary_bench.application.resilience import AttemptMetrics, DelegationFailure
from agent_boundary_bench.application.supervisor import Invocation, Probe
from agent_boundary_bench.domain.credit import AnalysisTask
from agent_boundary_bench.observability import headers


@dataclass
class Wire:
    """Per-coroutine HTTP body accounting (excludes TCP and HTTP headers)."""

    request_bytes: int = 0
    response_bytes: int = 0
    calls: int = 0


wire_context: ContextVar[Wire | None] = ContextVar("abb_wire", default=None)


class RemoteDelegate:
    """One reusable client/session per round; discovery stays outside measurement."""

    def __init__(
        self, url: str, scenario: str, probe: Probe, enabled: bool, timeout: float
    ) -> None:
        """Use identical HTTP pools, no environment proxies, HTTP/2 or retries."""
        self.url = url
        self.scenario = scenario
        self.probe = probe
        self.enabled = enabled
        self.http = httpx.AsyncClient(
            timeout=timeout,
            trust_env=False,
            http2=False,
            limits=httpx.Limits(max_connections=128, max_keepalive_connections=128),
            event_hooks={"request": [self.on_request], "response": [self.on_response]},
        )
        self.a2a: Client | None = None

    async def on_request(self, request: httpx.Request) -> None:
        """Inject distributed context through HTTPX's public event hook."""
        request.headers.update(headers(self.enabled))
        wire = wire_context.get()
        if wire is not None:
            wire.calls += 1
            wire.request_bytes += len(await request.aread())

    async def on_response(self, response: httpx.Response) -> None:
        """Count complete response body bytes without retaining payload content."""
        body = await response.aread()
        wire = wire_context.get()
        if wire is not None:
            wire.response_bytes += len(body)

    async def prepare(self) -> None:
        """Resolve and validate the public card once per A2A session."""
        if self.scenario == "a2a":
            card = await A2ACardResolver(self.http, self.url).get_agent_card()
            self.a2a = ClientFactory(
                ClientConfig(
                    streaming=False,
                    polling=False,
                    httpx_client=self.http,
                    supported_protocol_bindings=["JSONRPC"],
                )
            ).create(card)

    async def invoke(
        self,
        task: AnalysisTask,
        *,
        delegation_id: str | None = None,
        attempt: int = 1,
    ) -> Invocation:
        """Send identical business JSON through the selected boundary."""
        wire = Wire()
        token = wire_context.set(wire)
        encode_ms = 0.0
        transport_started: float | None = None
        try:
            with self.probe.span("delegation." + self.scenario):
                start = perf_counter()
                with self.probe.span("serialization.encode"):
                    payload = TASK.dump_json(task)
                encode_ms = (perf_counter() - start) * 1000
                start = perf_counter()
                transport_started = start
                with self.probe.span("transport.client"):
                    if self.scenario == "http":
                        request_headers = {"content-type": "application/json"}
                        if delegation_id is not None:
                            request_headers.update(
                                {
                                    "x-abb-delegation-id": delegation_id,
                                    "x-abb-attempt": str(attempt),
                                }
                            )
                        response = await self.http.post(
                            self.url + "/analyze",
                            content=payload,
                            headers=request_headers,
                        )
                        response.raise_for_status()
                        reply_json = response.content
                    else:
                        if self.a2a is None:
                            raise RuntimeError("prepare A2A client before delegation")
                        message = Message(
                            message_id=str(uuid4()),
                            role=Role.ROLE_USER,
                            parts=[Part(text=payload.decode(), media_type="application/json")],
                        )
                        if delegation_id is not None:
                            message.metadata.update(
                                {
                                    "abb_delegation_id": delegation_id,
                                    "abb_attempt": attempt,
                                }
                            )
                        request = SendMessageRequest(
                            message=message,
                            configuration=SendMessageConfiguration(return_immediately=False),
                        )
                        reply_json = b""
                        async for event in self.a2a.send_message(request):
                            if event.HasField("message"):
                                reply_json = event.message.parts[0].text.encode()
                        if not reply_json:
                            raise ValueError("A2A returned no immediate Message")
                transport_ms = (perf_counter() - start) * 1000
                start = perf_counter()
                with self.probe.span("serialization.decode"):
                    reply = Reply.model_validate_json(reply_json)
                serialization_ms = encode_ms + (perf_counter() - start) * 1000
                metrics = AttemptMetrics(
                    remote_calls=wire.calls,
                    request_bytes=wire.request_bytes,
                    response_bytes=wire.response_bytes,
                    serialization_ms=serialization_ms,
                    transport_ms=transport_ms,
                    specialist_ms=reply.specialist_ms,
                    kernel_executions=reply.kernel_executions,
                    idempotency_hits=reply.idempotency_hits,
                    injected_failures=reply.injected_failures,
                    rejections=reply.rejections,
                    backpressure_wait_ms=reply.backpressure_wait_ms,
                )
                if reply.error is not None:
                    raise DelegationFailure(
                        reply.error,
                        transient=reply.transient,
                        metrics=metrics,
                    )
                if reply.result is None:
                    raise ValueError("specialist returned no business result")
                return Invocation(
                    reply.result,
                    reply.specialist_ms,
                    wire.request_bytes,
                    wire.response_bytes,
                    serialization_ms,
                    transport_ms,
                    wire.calls,
                    kernel_executions=reply.kernel_executions,
                    idempotency_hits=reply.idempotency_hits,
                    injected_failures=reply.injected_failures,
                    rejections=reply.rejections,
                    backpressure_wait_ms=reply.backpressure_wait_ms,
                )
        except asyncio.CancelledError as exc:
            if delegation_id is None:
                raise
            transport_ms = (
                (perf_counter() - transport_started) * 1000
                if transport_started is not None
                else 0.0
            )
            raise DelegationFailure(
                "attempt_timeout",
                transient=True,
                metrics=AttemptMetrics(
                    remote_calls=wire.calls,
                    request_bytes=wire.request_bytes,
                    response_bytes=wire.response_bytes,
                    serialization_ms=encode_ms,
                    transport_ms=transport_ms,
                ),
            ) from exc
        except httpx.HTTPStatusError as exc:
            transient = exc.response.status_code in (429, 502, 503, 504)
            raise DelegationFailure(
                f"http_{exc.response.status_code}",
                transient=transient,
                metrics=AttemptMetrics(
                    remote_calls=wire.calls,
                    request_bytes=wire.request_bytes,
                    response_bytes=wire.response_bytes,
                    serialization_ms=encode_ms,
                    transport_ms=(
                        (perf_counter() - transport_started) * 1000
                        if transport_started is not None
                        else 0.0
                    ),
                ),
            ) from exc
        except A2AClientTimeoutError as exc:
            raise DelegationFailure(
                "transport_timeout",
                transient=True,
                metrics=AttemptMetrics(
                    remote_calls=wire.calls,
                    request_bytes=wire.request_bytes,
                    response_bytes=wire.response_bytes,
                    serialization_ms=encode_ms,
                    transport_ms=(
                        (perf_counter() - transport_started) * 1000
                        if transport_started is not None
                        else 0.0
                    ),
                ),
            ) from exc
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise DelegationFailure(
                "transport_failure",
                transient=True,
                metrics=AttemptMetrics(
                    remote_calls=wire.calls,
                    request_bytes=wire.request_bytes,
                    response_bytes=wire.response_bytes,
                    serialization_ms=encode_ms,
                    transport_ms=(
                        (perf_counter() - transport_started) * 1000
                        if transport_started is not None
                        else 0.0
                    ),
                ),
            ) from exc
        finally:
            wire_context.reset(token)

    async def close(self) -> None:
        """Release the owned HTTP connection pool."""
        await self.http.aclose()
