"""End-to-end CLI workflows and the same ingress used by k6."""

import json
import sys
from pathlib import Path

import httpx
import pytest

from agent_boundary_bench.benchmark.models import Config
from agent_boundary_bench.entrypoints.cli import main
from agent_boundary_bench.entrypoints.gateway import create_gateway


def test_cli_workflow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "rounds"
    commands = [
        ["validate"],
        [
            "run",
            "--scenario",
            "local",
            "--profile",
            "smoke",
            "--duration",
            ".2",
            "--rate",
            "5",
            "--output",
            str(output),
        ],
        ["report", "--input", str(output), "--output", str(tmp_path / "reports")],
    ]
    config = tmp_path / "campaign.json"
    config.write_text(
        json.dumps(
            {
                "label": "test",
                "seed": 42,
                "repetitions": 1,
                "defaults": {"duration": 0.2, "warmup": 1},
                "matrix": {"scenario": ["local"]},
            }
        )
    )
    commands.append(["campaign", "--config", str(config), "--output", str(tmp_path / "campaign")])
    for command in commands:
        monkeypatch.setattr(sys, "argv", ["abb", *command])
        main()
    record = json.loads((tmp_path / "campaign/campaign.json").read_text())
    assert len(record["order"]) == len(record["completed"]) == 1
    assert (tmp_path / "reports/summary.csv").exists()


@pytest.mark.integration
@pytest.mark.parametrize(
    "scenario",
    ["local", "http", "a2a", "mcp-inprocess", "mcp-stdio", "mcp-streamable-http"],
)
async def test_gateway_real_delegation(scenario: str, tmp_path: Path) -> None:
    config = Config.model_validate({"scenario": scenario, "telemetry": True})
    app = create_gateway(config, tmp_path)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as client,
    ):
        assert (await client.get("/health")).status_code == 200
        response = await client.post("/execute")
        assert response.status_code == 200
        assert len(response.json()["results"]) == 3
        assert response.json()["remote_calls"] == (0 if scenario == "local" else 3)
