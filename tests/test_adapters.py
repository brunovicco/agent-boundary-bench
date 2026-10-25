"""Real sockets and official A2A client/server, with no SDK protocol mocks."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from agent_boundary_bench.adapters.remote import RemoteDelegate
from agent_boundary_bench.application.supervisor import NullProbe, supervise
from agent_boundary_bench.benchmark.models import Config
from agent_boundary_bench.benchmark.runtime import runtime
from agent_boundary_bench.domain.credit import AnalysisTask, Specialist, evaluate, fixture
from agent_boundary_bench.observability import Telemetry


@pytest.mark.integration
@pytest.mark.contract
@pytest.mark.parametrize("scenario", ["local", "http", "a2a"])
async def test_real_adapter_equivalence(scenario: str, tmp_path: Path) -> None:
    config = Config.model_validate({"scenario": scenario})
    async with runtime(config, NullProbe(), tmp_path) as (delegate, pid):
        assert (pid is None) == (scenario == "local")
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
