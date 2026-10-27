"""Executable laboratory interface: validate, serve, run, campaign and report."""

import argparse
import asyncio
import itertools
import json
import random
from dataclasses import asdict
from pathlib import Path

import uvicorn

from agent_boundary_bench.adapters.mcp import create_mcp_server
from agent_boundary_bench.adapters.server import create_app
from agent_boundary_bench.application.resilience import ResiliencePolicy
from agent_boundary_bench.benchmark.models import Config, Scenario
from agent_boundary_bench.benchmark.runner import run
from agent_boundary_bench.benchmark.runtime import health
from agent_boundary_bench.domain.credit import (
    AnalysisTask,
    Specialist,
    canonical,
    digest,
    evaluate,
    fixture,
)
from agent_boundary_bench.entrypoints.gateway import create_gateway
from agent_boundary_bench.observability import Telemetry
from agent_boundary_bench.reporting.report import report

SCENARIOS: tuple[Scenario, ...] = (
    "local",
    "http",
    "a2a",
    "mcp-inprocess",
    "mcp-stdio",
    "mcp-streamable-http",
)


def parser() -> argparse.ArgumentParser:
    """Declare only implemented CLI options."""
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="check deterministic fixture contracts offline")
    server = sub.add_parser("serve", help="one independent specialist worker")
    server.add_argument("--scenario", choices=["http", "a2a"], required=True)
    server.add_argument("--host", default="127.0.0.1")
    server.add_argument("--port", type=int, default=8100)
    server.add_argument("--public-url", help="advertised A2A URL, defaults to bind URL")
    server.add_argument("--trace-file", type=Path)
    _service_treatment_arguments(server)
    mcp_server = sub.add_parser("mcp-serve", help="official MCP v2 tool/resource server")
    mcp_server.add_argument("--transport", choices=["stdio", "streamable-http"], required=True)
    mcp_server.add_argument("--host", default="127.0.0.1")
    mcp_server.add_argument("--port", type=int, default=8300)
    mcp_server.add_argument("--trace-file", type=Path)
    gateway = sub.add_parser("gateway", help="uniform supervisor ingress for k6")
    gateway.add_argument("--scenario", choices=SCENARIOS, required=True)
    gateway.add_argument("--port", type=int, default=8200)
    gateway.add_argument("--payload-bytes", type=int, default=1024)
    gateway.add_argument("--wait-ms", type=int, default=0)
    gateway.add_argument("--parallel", action="store_true")
    gateway.add_argument("--telemetry", action="store_true")
    gateway.add_argument("--timeout", type=float, default=5)
    _topology_arguments(gateway)
    gateway.add_argument("--output", type=Path, default=Path("results/gateway"))
    check = sub.add_parser("health")
    check.add_argument("--url", required=True)
    bench = sub.add_parser(
        "run", help="native open-arrival round; automatically owns remote worker"
    )
    bench.add_argument("--scenario", choices=SCENARIOS, required=True)
    bench.add_argument("--profile", choices=["smoke", "pilot"], default="smoke")
    bench.add_argument("--payload-bytes", type=int, choices=[1024, 16384, 131072], default=1024)
    bench.add_argument("--wait-ms", type=int, choices=[0, 50, 250], default=0)
    bench.add_argument("--parallel", action="store_true")
    bench.add_argument("--telemetry", action="store_true")
    bench.add_argument("--rate", type=int)
    bench.add_argument("--duration", type=float)
    bench.add_argument("--warmup", type=int, default=3)
    bench.add_argument("--timeout", type=float, default=5)
    bench.add_argument("--concurrency", type=int, default=64)
    bench.add_argument("--seed", type=int, default=42)
    _topology_arguments(bench)
    bench.add_argument("--output", type=Path, default=Path("results"))
    campaign = sub.add_parser("campaign", help="execute a reproducibly shuffled matrix")
    campaign.add_argument("--config", type=Path, default=Path("experiments/full.json"))
    campaign.add_argument("--output", type=Path, default=Path("results"))
    render = sub.add_parser("report")
    render.add_argument("--input", type=Path, required=True)
    render.add_argument("--output", type=Path, default=Path("reports/latest"))
    return root


def _topology_arguments(command: argparse.ArgumentParser) -> None:
    """Add topology, amplification and v0.3 resilience controls."""
    command.add_argument("--specialist-repetitions", type=int, default=1)
    command.add_argument("--cpu-iterations", type=int, default=0)
    command.add_argument("--memory-bytes", type=int, default=0)
    command.add_argument("--fanout-limit", type=int, default=64)
    command.add_argument("--context-copies", type=int, choices=[0, 1, 4, 16], default=0)
    command.add_argument("--tool-repetitions", type=int, default=1)
    command.add_argument("--resource-reads", type=int, default=0)
    command.add_argument(
        "--fault-mode",
        choices=["none", "fail-first", "delay-first", "after-commit"],
        default="none",
    )
    command.add_argument("--fault-every", type=int, default=1)
    command.add_argument("--fault-delay-ms", type=int, default=100)
    command.add_argument("--max-attempts", type=int, default=1)
    command.add_argument("--attempt-timeout", type=float, default=5)
    command.add_argument("--retry-backoff-ms", type=int, default=0)
    command.add_argument("--idempotency", action="store_true")
    command.add_argument("--idempotency-capacity", type=int, default=10000)
    command.add_argument("--idempotency-ttl-seconds", type=float, default=300)
    command.add_argument("--service-concurrency", type=int, default=0)
    command.add_argument("--queue-capacity", type=int, default=0)
    command.add_argument("--queue-timeout-ms", type=int, default=1000)


def _service_treatment_arguments(command: argparse.ArgumentParser) -> None:
    """Expose only specialist-side controls on standalone service commands."""
    command.add_argument(
        "--fault-mode",
        choices=["none", "fail-first", "delay-first", "after-commit"],
        default="none",
    )
    command.add_argument("--fault-every", type=int, default=1)
    command.add_argument("--fault-delay-ms", type=int, default=100)
    command.add_argument("--idempotency", action="store_true")
    command.add_argument("--idempotency-capacity", type=int, default=10000)
    command.add_argument("--idempotency-ttl-seconds", type=float, default=300)
    command.add_argument("--service-concurrency", type=int, default=0)
    command.add_argument("--queue-capacity", type=int, default=0)
    command.add_argument("--queue-timeout-ms", type=int, default=1000)


def _server_policy(args: argparse.Namespace) -> ResiliencePolicy:
    """Build the process-local service policy from validated CLI primitives."""
    return ResiliencePolicy(
        fault_mode=args.fault_mode,
        fault_every=args.fault_every,
        fault_delay_ms=args.fault_delay_ms,
        idempotency=args.idempotency,
        idempotency_capacity=args.idempotency_capacity,
        idempotency_ttl_seconds=args.idempotency_ttl_seconds,
        service_concurrency=args.service_concurrency,
        queue_capacity=args.queue_capacity,
        queue_timeout_ms=args.queue_timeout_ms,
    )


def validate() -> None:
    """Check the versioned fixtures and exact canonical payload sizes."""
    records = []
    for size in (1024, 16384, 131072):
        case = fixture(size)
        if len(canonical(asdict(case))) != size:
            raise ValueError("fixture size invariant failed")
        for specialist in Specialist:
            result = evaluate(AnalysisTask(specialist, case))
            if result.input_sha256 != digest(case):
                raise ValueError("fixture hash invariant failed")
        records.append({"bytes": size, "sha256": digest(case)})
    fixture_path = Path("fixtures/v1/manifest.json")
    if fixture_path.exists() and json.loads(fixture_path.read_text()) != records:
        raise ValueError("versioned fixture hashes do not match kernel")
    print(json.dumps({"status": "ok", "fixtures": records}, indent=2))


def campaign_configs(path: Path) -> list[Config]:
    """Expand a matrix, requiring five repeats for campaigns labelled full."""
    data = json.loads(path.read_text())
    repeats = int(data["repetitions"])
    if str(data["label"]).endswith("full") and repeats < 5:
        raise ValueError("full campaigns require at least five repetitions")
    rng = random.Random(int(data["seed"]))  # noqa: S311  # nosec B311
    rounds: list[Config] = []
    for repetition in range(repeats):
        block = [
            Config.model_validate(
                {
                    **data["defaults"],
                    "label": data["label"],
                    "seed": data["seed"],
                    "repetition": repetition,
                    **dict(zip(data["matrix"], values, strict=True)),
                }
            )
            for values in itertools.product(*data["matrix"].values())
        ]
        rng.shuffle(block)
        rounds.extend(block)
    return rounds


async def campaign(path: Path, output: Path) -> None:
    """Persist planned order first, then update the actual completed rounds."""
    configs = campaign_configs(path)
    output.mkdir(parents=True, exist_ok=True)
    plan = output / "campaign.json"
    if plan.exists():
        raise ValueError("campaign.json exists; use a new output directory")
    record: dict[str, object] = {
        "source": json.loads(path.read_text()),
        "order": [c.model_dump() for c in configs],
        "completed": [],
    }
    completed: list[str] = []
    plan.write_text(json.dumps(record, indent=2) + "\n")
    for index, config in enumerate(configs):
        print(f"[{index + 1}/{len(configs)}] {config.model_dump_json()}", flush=True)
        directory = await run(config, output)
        completed.append(directory.name)
        record["completed"] = completed
        plan.write_text(json.dumps(record, indent=2) + "\n")


def main() -> None:
    """Dispatch CLI operations and fail visibly on validation/runtime errors."""
    args = parser().parse_args()
    match args.command:
        case "validate":
            validate()
        case "serve":
            telemetry = Telemetry(args.trace_file, "abb-specialist") if args.trace_file else None
            app = create_app(
                args.scenario,
                args.public_url or f"http://{args.host}:{args.port}",
                telemetry,
                _server_policy(args),
            )
            try:
                uvicorn.run(
                    app,
                    host=args.host,
                    port=args.port,
                    workers=1,
                    loop="asyncio",
                    http="h11",
                    access_log=False,
                    log_level="warning",
                )
            finally:
                if telemetry:
                    telemetry.close()
        case "mcp-serve":
            telemetry = (
                Telemetry(args.trace_file, "abb-mcp-specialist") if args.trace_file else None
            )
            mcp = create_mcp_server(telemetry)
            try:
                if args.transport == "stdio":
                    asyncio.run(mcp.run_stdio_async())
                else:
                    uvicorn.run(
                        mcp.streamable_http_app(
                            streamable_http_path="/mcp",
                            json_response=True,
                            stateless_http=True,
                            host=args.host,
                        ),
                        host=args.host,
                        port=args.port,
                        workers=1,
                        loop="asyncio",
                        http="h11",
                        access_log=False,
                        log_level="warning",
                    )
            finally:
                if telemetry:
                    telemetry.close()
        case "health":
            asyncio.run(health(args.url, attempts=1))
            print("healthy")
        case "gateway":
            config = Config.model_validate(
                {
                    key: getattr(args, key)
                    for key in (
                        "scenario",
                        "payload_bytes",
                        "wait_ms",
                        "cpu_iterations",
                        "memory_bytes",
                        "parallel",
                        "telemetry",
                        "timeout",
                        "specialist_repetitions",
                        "fanout_limit",
                        "context_copies",
                        "tool_repetitions",
                        "resource_reads",
                        "fault_mode",
                        "fault_every",
                        "fault_delay_ms",
                        "max_attempts",
                        "attempt_timeout",
                        "retry_backoff_ms",
                        "idempotency",
                        "idempotency_capacity",
                        "idempotency_ttl_seconds",
                        "service_concurrency",
                        "queue_capacity",
                        "queue_timeout_ms",
                    )
                }
            )
            uvicorn.run(
                create_gateway(config, args.output),
                host="127.0.0.1",
                port=args.port,
                workers=1,
                loop="asyncio",
                http="h11",
                access_log=False,
                log_level="warning",
            )
        case "run":
            config = Config.model_validate(
                {
                    key: getattr(args, key)
                    for key in (
                        "scenario",
                        "payload_bytes",
                        "wait_ms",
                        "cpu_iterations",
                        "memory_bytes",
                        "parallel",
                        "telemetry",
                        "timeout",
                        "concurrency",
                        "warmup",
                        "seed",
                        "specialist_repetitions",
                        "fanout_limit",
                        "context_copies",
                        "tool_repetitions",
                        "resource_reads",
                        "fault_mode",
                        "fault_every",
                        "fault_delay_ms",
                        "max_attempts",
                        "attempt_timeout",
                        "retry_backoff_ms",
                        "idempotency",
                        "idempotency_capacity",
                        "idempotency_ttl_seconds",
                        "service_concurrency",
                        "queue_capacity",
                        "queue_timeout_ms",
                    )
                }
                | {
                    "label": args.profile,
                    "rate": args.rate
                    if args.rate is not None
                    else (5 if args.profile == "smoke" else 20),
                    "duration": args.duration
                    if args.duration is not None
                    else (2 if args.profile == "smoke" else 10),
                }
            )
            print(asyncio.run(run(config, args.output)))
        case "campaign":
            asyncio.run(campaign(args.config, args.output))
        case "report":
            print(report(args.input, args.output))


if __name__ == "__main__":
    main()
