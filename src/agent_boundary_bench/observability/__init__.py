"""Public OpenTelemetry APIs and W3C propagation, no business payload capture."""

import json
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path

from opentelemetry import context, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import (
    SimpleSpanProcessor,
    SpanExporter,
    SpanExportResult,
)
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace import SpanKind
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from starlette.types import ASGIApp, Receive, Scope, Send

from agent_boundary_bench import __version__


class JsonExporter(SpanExporter):
    """Write bounded metadata-only JSONL spans synchronously for measurable export cost."""

    def __init__(self, path: Path) -> None:
        """Create an isolated output file per process/round."""
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.lock = threading.Lock()

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Persist IDs, parent relationship, names and durations only."""
        with self.lock, self.path.open("a", encoding="utf-8") as stream:
            for span in spans:
                ctx = span.context
                if ctx is None or span.start_time is None or span.end_time is None:
                    continue
                stream.write(
                    json.dumps(
                        {
                            "name": span.name,
                            "trace_id": f"{ctx.trace_id:032x}",
                            "span_id": f"{ctx.span_id:016x}",
                            "parent_id": f"{span.parent.span_id:016x}" if span.parent else None,
                            "duration_ms": (span.end_time - span.start_time) / 1000000,
                            "start_ns": span.start_time,
                            "status": span.status.status_code.name,
                            "service": str(span.resource.attributes.get("service.name", "unknown")),
                        }
                    )
                    + "\n"
                )
        return SpanExportResult.SUCCESS


class Telemetry:
    """Own a provider instead of replacing the global provider between campaigns."""

    def __init__(self, path: Path, service: str) -> None:
        """Use always-on local export with its overhead explicitly included."""
        self.provider = TracerProvider(
            resource=Resource.create({"service.name": service}), sampler=ALWAYS_ON
        )
        self.provider.add_span_processor(SimpleSpanProcessor(JsonExporter(path)))
        self.tracer = self.provider.get_tracer("agent-boundary-bench", __version__)

    @contextmanager
    def span(self, name: str) -> Iterator[trace.Span]:
        """Create a parentable span using public OTel interfaces."""
        with self.tracer.start_as_current_span(name) as span:
            yield span

    @contextmanager
    def remote_span(
        self,
        name: str,
        carrier: Mapping[str, object] | None,
    ) -> Iterator[trace.Span]:
        """Create a server span parented by a sanitized W3C metadata carrier."""
        text_carrier = {
            str(key): value for key, value in (carrier or {}).items() if isinstance(value, str)
        }
        # Direct in-process MCP dispatch carries the ambient context rather than a
        # serialized metadata carrier. Passing an explicitly empty Context here
        # would orphan that arm's server span.
        parent = TraceContextTextMapPropagator().extract(text_carrier) if text_carrier else None
        with self.tracer.start_as_current_span(
            name,
            context=parent,
            kind=SpanKind.SERVER,
        ) as span:
            yield span

    def close(self) -> None:
        """Flush and release the round's provider."""
        self.provider.shutdown()


def headers(enabled: bool) -> dict[str, str]:
    """Inject W3C traceparent only in enabled campaigns."""
    carrier: dict[str, str] = {}
    if enabled:
        TraceContextTextMapPropagator().inject(carrier)
    return carrier


class TraceMiddleware:
    """ASGI boundary propagation for both HTTP and SDK JSON-RPC routes."""

    def __init__(self, app: ASGIApp, telemetry: Telemetry | None) -> None:
        """Accept the ASGI application via its typed interface below."""
        self.app = app
        self.telemetry = telemetry

    async def __call__(self, scope: "Scope", receive: "Receive", send: "Send") -> None:
        """Extract request context without parsing or logging business content."""
        if scope["type"] != "http" or self.telemetry is None:
            await self.app(scope, receive, send)
            return
        carrier = {key.decode(): value.decode() for key, value in scope["headers"]}
        token = context.attach(TraceContextTextMapPropagator().extract(carrier))
        try:
            with self.telemetry.tracer.start_as_current_span(
                "transport.server", kind=SpanKind.SERVER
            ):
                await self.app(scope, receive, send)
        finally:
            context.detach(token)
