# Architecture

The domain uses frozen standard-library dataclasses and pure integer rules. Boundary adapters use Pydantic v2 TypeAdapter and a common Reply envelope to validate external values. This preserves the harness rule that domain code has no framework dependency. Timings live outside AnalysisResult, so nondeterminism never affects business equivalence.

Application code defines Delegate and Probe ports, Invocation observations and a supervisor. It owns task order, bounded structured concurrency, deadlines and result validation. `specialist_repetitions` generalizes fan-out while `fanout_limit` bounds active adapter calls; deterministic handle order provides fan-in. Adapters can be changed without changing the rules or supervisor.

v0.3 development adds an application-layer `ExecutionController`. It owns deterministic fault
selection, per-worker admission and a bounded TTL idempotency cache without adding transport or
SDK dependencies to the domain. The supervisor owns bounded retry attempts and keeps one
delegation ID stable across them. HTTP and A2A translate this metadata at their boundaries;
`AnalysisTask` and the fixture hash remain unchanged. With all resilience controls disabled, the
prior path sends no new metadata and does not enter retry/admission treatment logic.

The local adapter invokes the kernel. The HTTP adapter sends task JSON to FastAPI. The A2A adapter uses the official 1.x client, resolved public AgentCard and JSON-RPC routes. JSON text Parts carry the same task/reply envelope. Immediate Message responses avoid adding durable task storage and polling to only one experimental arm. The SDK's in-memory task-store dependency is constructed, but the workload does not create resumable tasks.

MCP is modeled as a distinct tool-access family. One `MCPServer` publishes `analyze_credit` plus the versioned `credit://fixture/{size}/{seed}` resource template. The official v2 `Client` connects through direct in-process dispatch, official stdio transport or official Streamable HTTP transport. Server discovery and tool/resource listing occur once before warmup. Tool arguments may carry 0/1/4/16 exact synthetic context copies; tool calls, uncached resource reads and specialist fan-out have independent controls. Every returned result and resource is validated against the same domain oracle/fixture.

One subprocess owns three remote specialist roles, matching HTTP and A2A process/worker counts and deployment location. MCP stdio and Streamable HTTP also use one tool-server process; MCP in-process deliberately does not. The application enforces one deadline; transport clients have explicit operation timeouts. Pools/sessions are reused per round. Discovery and startup precede warmup and use separate bounded readiness deadlines; measured tool/resource operations retain the configured round timeout. All owned service processes are closed in finally blocks; externally visible HTTP children use bounded graceful termination then kill only when unresponsive.

The benchmark package owns open arrivals, manifests and resource sampling. Observability owns explicit providers, propagation and nullable process/cgroup v2 observations. Reporting verifies data before deriving statistics. CLI/gateway entrypoints compose the pieces. The gateway is a uniform optional ingress for k6 and does not alter native harness latency.

Fault, pressure and resource-isolation controls currently apply to the A0/A1/A2 research family.
This preserves the distinction between agent delegation and MCP tool access. The isolation
Compose overlay runs the harness in one cgroup and HTTP/A2A workers in equal separate cgroups;
local delegation deliberately shares the harness cgroup. Cross-host network and process-crash
treatments remain separate pending milestones rather than implicit claims of the application
fault injector.

The inherited architecture gate checks domain/application dependency direction. Tests exercise real A2A and MCP SDK client/server exchanges across sockets, pipes and direct dispatch rather than protocol mocks. They do not constitute certification against complete upstream TCKs.

See ADRs 0001–0008 and methodology for trade-offs and inference limits.
