# Compatibility research — 2026-10-25 UTC

Official documentation and repository release metadata were checked before adapter implementation. Installed APIs were inspected and exercised afterward; no old 0.3 A2A examples were copied into a 1.0 server.

| Component | Stable release observed | Used in v0.1 | Decision |
|---|---|---|---|
| A2A specification | v1.0.1, released 2026-05-28 | Advertised protocol family `1.0` | JSON-RPC binding; immediate Message response |
| Official A2A Python | v1.2.3, released 2026-10-19 | `a2a-sdk[http-server]==1.2.3` | Public ClientFactory and route APIs; no compat namespace |
| MCP specification | 2026-07-28 | Research only | Tools/resources experiment postponed |
| Official MCP Python | v2.3.0, released 2026-10-02 | Not installed | Stable v2; no v1 FastMCP assumptions |
| OpenTelemetry Python | 1.45.1 on package index | API/SDK 1.45.1 | Explicit provider, sampler and metadata exporter |
| k6 | v2.3.0 | Binary tested, Go 1.26.8 | constant-arrival-rate; raw output and summary |
| FastAPI / Starlette | 0.162.0 / 1.10.0 | Locked | Real-socket tests avoid deprecated httpx TestClient integration |
| HTTPX / Uvicorn | 0.28.1 / 0.54.0 | Locked | HTTP/1.1 + h11 + asyncio, one worker |
| Pydantic / Matplotlib / psutil | 2.14.1 / 3.11.2 / 7.2.2 | Locked | Boundary validation, deterministic plotting, process metrics |
| Python / uv | 3.12.14 / 0.13.4 runtime | Validated | Requires Python >=3.12,<3.15 |

The lockfile is authoritative for every transitive version. Mypy 1.19.1 is intentionally pinned: the available 2.4.0 crashed inside its automatic psutil affinity discovery on this host's mismatched PID/procfs namespaces. Strict checking remains enabled. No warnings or tests were disabled to bypass that crash.

## A2A 1.0 and public implementation APIs

A2A documents JSON-RPC, HTTP+JSON/REST and gRPC bindings. v0.1 selects only JSON-RPC. 1.0 changed part representation, enum values, AgentCard interfaces, method names and error models from 0.3. In SDK 1.2.3, `a2a.types` exposes generated protobuf classes; legacy Pydantic 0.3 objects are not interchangeable.

Client: `A2ACardResolver`, `ClientConfig(streaming=False, polling=False, httpx_client=...)`, `ClientFactory.create`, `Client.send_message(SendMessageRequest)`. Server: `AgentExecutor`, `RequestContext`, `EventQueue`, `DefaultRequestHandler`, `InMemoryTaskStore`, `create_agent_card_routes`, `create_jsonrpc_routes`, `add_a2a_routes_to_fastapi`. The card uses `AgentInterface(protocol_binding="JSONRPC", protocol_version="1.0")`; the official client sets required version headers. Requests use `SendMessage`, and replies contain one JSON text Part carrying the validated common envelope. Both directions advertise application/json. Task persistence/streaming/push/cancel/recovery features are not benchmarked. Real sockets test card resolution, invocation, invalid messages and context correlation. This is interoperability between the selected SDK client/server, not full protocol TCK certification.

## MCP v2 implications for v0.2

v2 is stable, not a hypothetical prerelease. Its high-level server is `MCPServer` (`from mcp.server import MCPServer`), with a first-class `Client`. The 2026-07-28 revision changes connection/session semantics and request metadata; wire types live in `mcp-types` and use snake_case. Standard transport bindings are stdio and Streamable HTTP; legacy SSE compatibility must be distinguished from the current standard. An in-process client/server path is an SDK facility, not a third standard network binding. The v2.3.0 release requires httpx2>=2.10.0; v0.2 must recheck coexistence with A2A's HTTPX dependency rather than assume identical clients. None of these APIs are required by v0.1's kernel.

## Official sources

- [A2A protocol](https://a2a-protocol.org/) and [spec repository releases](https://github.com/a2aproject/A2A/releases)
- [A2A 1.0 changes](https://a2a-protocol.org/latest/whats-new-v1/)
- [A2A Python releases](https://github.com/a2aproject/a2a-python/releases/tag/v1.2.3) and [public API](https://a2a-protocol.org/latest/sdk/python/api/)
- [MCP specification transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [MCP Python releases](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.3.0) and [v2 changes](https://py.sdk.modelcontextprotocol.io/whats-new/)
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [k6 executor](https://grafana.com/docs/k6/latest/using-k6/scenarios/executors/constant-arrival-rate/) and [k6 releases](https://github.com/grafana/k6/releases/tag/v2.3.0)
- [Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/)
- Package metadata was also queried from PyPI for installed version/Requires-Python compatibility.
