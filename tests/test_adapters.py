"""Real sockets and official A2A client/server, with no SDK protocol mocks."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from agent_boundary_bench.adapters.mcp import MCP_PROTOCOL_VERSION, MCPDelegate, create_mcp_server
from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.supervisor import NullProbe, supervise
from agent_boundary_bench.benchmark.models import Config
from agent_boundary_bench.benchmark.runtime import external_endpoint, runtime
from agent_boundary_bench.domain.credit import AnalysisTask, Specialist, evaluate, fixture
from agent_boundary_bench.observability import Telemetry


def test_mcp_server_fixes_non_measured_logging_level() -> None:
    assert create_mcp_server().settings.log_level == "WARNING"


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.parametrize(
    "scenario",
    ["local", "http", "a2a", "mcp-inprocess", "mcp-stdio", "mcp-streamable-http"],
)
async def test_real_adapter_equivalence(scenario: str, tmp_path: Path) -> None:
    config = Config.model_validate({"scenario": scenario})
    async with runtime(config, NullProbe(), tmp_path) as (delegate, target):
        assert (target is not None) == (scenario in ("http", "a2a", "mcp-streamable-http"))
        if target is not None:
            assert target.pid is not None
            if scenario in ("http", "a2a"):
                assert isinstance(delegate, RemoteDelegate)
                resource_response = await delegate.http.get(delegate.url + "/resources")
                resource_response.raise_for_status()
                assert resource_response.json()["pid"] == target.pid
        for size in (1024, 16384, 131072):
            for wait in (0, 50, 250):
                for specialist in Specialist:
                    task = AnalysisTask(specialist, fixture(size), wait)
                    value = await delegate.invoke(task)
                    assert value.result == evaluate(task)
                    assert value.specialist_ms >= wait * 0.9
                    assert value.remote_calls == (0 if scenario == "local" else 1)
                    if scenario != "local":
                        assert value.request_bytes > size
                        assert value.response_bytes > 0
        sequential = await supervise(delegate, fixture(1024), 0, False, 2, NullProbe())
        parallel = await supervise(delegate, fixture(1024), 0, True, 2, NullProbe())
        assert [v.result for v in sequential.invocations] == [
            v.result for v in parallel.invocations
        ]
        with pytest.raises(TimeoutError):
            await supervise(delegate, fixture(1024), 250, False, 0.01, NullProbe())
        recovered = await delegate.invoke(AnalysisTask(Specialist.DOCUMENT, fixture(1024)))
        assert recovered.result == evaluate(AnalysisTask(Specialist.DOCUMENT, fixture(1024)))
        resource_treated = AnalysisTask(
            Specialist.DOCUMENT,
            fixture(1024),
            wait_ms=50,
            cpu_iterations=100,
            memory_bytes=8192,
        )
        assert (await delegate.invoke(resource_treated)).result == evaluate(resource_treated)


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.parametrize("scenario", ["mcp-inprocess", "mcp-stdio", "mcp-streamable-http"])
async def test_mcp_v2_tool_resource_and_context_amplification(
    scenario: str, tmp_path: Path
) -> None:
    config = Config.model_validate(
        {
            "scenario": scenario,
            "context_copies": 4,
            "tool_repetitions": 2,
            "resource_reads": 2,
        }
    )
    async with runtime(config, NullProbe(), tmp_path) as (delegate, _):
        assert isinstance(delegate, MCPDelegate)
        assert delegate.protocol_version == MCP_PROTOCOL_VERSION
        task = AnalysisTask(Specialist.FINANCIAL, fixture(16384))
        invocation = await delegate.invoke(task)
        assert invocation.result == evaluate(task)
        assert invocation.remote_calls == 4
        assert invocation.tool_calls == 2
        assert invocation.resource_reads == 2
        assert invocation.context_bytes > 4 * 16384
        assert invocation.request_bytes > invocation.context_bytes
        assert invocation.response_bytes > 2 * 16384


@pytest.mark.integration
@pytest.mark.parametrize("scenario", ["mcp-inprocess", "mcp-stdio", "mcp-streamable-http"])
async def test_mcp_trace_context_uses_public_request_metadata(
    scenario: str, tmp_path: Path
) -> None:
    telemetry = Telemetry(tmp_path / "harness-spans.jsonl", "test-mcp-client")
    config = Config.model_validate({"scenario": scenario, "telemetry": True})
    try:
        async with runtime(config, telemetry, tmp_path) as (delegate, _):
            with telemetry.span("mcp-test-root"):
                await delegate.invoke(AnalysisTask(Specialist.DOCUMENT, fixture(1024)))
    finally:
        telemetry.close()
    spans = [
        json.loads(line)
        for path in tmp_path.glob("*-spans.jsonl")
        for line in path.read_text().splitlines()
    ]
    root = next(span for span in spans if span["name"] == "mcp-test-root")
    server = [
        span
        for span in spans
        if span["name"] == "mcp.transport.server" and span["trace_id"] == root["trace_id"]
    ]
    assert len(server) == 1
    assert not any("synthetic-42" in json.dumps(span) for span in spans)


@pytest.mark.integration
@pytest.mark.parametrize("scenario", ["http", "a2a"])
async def test_invalid_input_and_trace_propagation(scenario: str, tmp_path: Path) -> None:
    telemetry = Telemetry(tmp_path / "harness-spans.jsonl", "test")
    config = Config.model_validate({"scenario": scenario, "telemetry": True})
    try:
        async with runtime(config, telemetry, tmp_path) as (delegate, _):
            assert isinstance(delegate, RemoteDelegate)
            await supervise(delegate, fixture(1024), 0, False, 2, telemetry)
            if scenario == "http":
                response = await delegate.http.post(delegate.url + "/analyze", content=b"{}")
                assert response.status_code == 422
            else:
                response = await delegate.http.post(
                    delegate.url + "/rpc",
                    json={
                        "jsonrpc": "2.0",
                        "id": "invalid",
                        "method": "SendMessage",
                        "params": {},
                    },
                    headers={"A2A-Version": "1.0"},
                )
                assert "error" in response.json()
                card = (
                    await delegate.http.get(delegate.url + "/.well-known/agent-card.json")
                ).json()
                assert card["supportedInterfaces"][0]["protocolVersion"] == "1.0"
    finally:
        telemetry.close()
    client_spans = [
        json.loads(line) for line in (tmp_path / "harness-spans.jsonl").read_text().splitlines()
    ]
    server_spans = [
        json.loads(line) for line in (tmp_path / "specialist-spans.jsonl").read_text().splitlines()
    ]
    client_ids = {s["span_id"] for s in client_spans}
    linked = [
        s for s in server_spans if s["name"] == "transport.server" and s["parent_id"] in client_ids
    ]
    assert len(linked) == 3
    assert not any("synthetic-42" in json.dumps(s) for s in client_spans + server_spans)
    # Ensure none of the business JSON is exported in spans.
    assert not any(asdict(fixture(1024))["padding"] in json.dumps(s) for s in server_spans)


def test_external_endpoint_requires_a_plain_http_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ABB_HTTP_ENDPOINT", "http://http:8100/")
    assert external_endpoint(Config(scenario="http")) == "http://http:8100"
    monkeypatch.setenv("ABB_HTTP_ENDPOINT", "http://user:secret@http:8100/path?query=1")
    with pytest.raises(ValueError, match="credential-free HTTP origin"):
        external_endpoint(Config(scenario="http"))
    monkeypatch.delenv("ABB_HTTP_ENDPOINT")
    assert external_endpoint(Config(scenario="http")) is None
