# Architecture

The domain uses frozen standard-library dataclasses and pure integer rules. Boundary adapters use Pydantic v2 TypeAdapter and a common Reply envelope to validate external values. This preserves the harness rule that domain code has no framework dependency. Timings live outside AnalysisResult, so nondeterminism never affects business equivalence.

Application code defines Delegate and Probe ports, Invocation observations and a supervisor. It owns task order, structured concurrency, deadlines and result validation. Adapters can be changed without changing the rules or supervisor.

The local adapter invokes the kernel. The HTTP adapter sends task JSON to FastAPI. The A2A adapter uses the official 1.x client, resolved public AgentCard and JSON-RPC routes. JSON text Parts carry the same task/reply envelope. Immediate Message responses avoid adding durable task storage and polling to only one experimental arm. The SDK's in-memory task-store dependency is constructed, but the workload does not create resumable tasks.

One subprocess owns three remote specialist roles, matching HTTP and A2A process/worker counts and deployment location. The application enforces one deadline; HTTPX provides per-operation network timeouts. Pools are reused per round. Discovery and startup precede warmup. All service processes are stopped in finally blocks, with bounded graceful termination then kill only for an unresponsive child owned by the harness.

The benchmark package owns open arrivals, manifests and resource sampling. Observability owns explicit providers and propagation. Reporting verifies data before deriving statistics. CLI/gateway entrypoints compose the pieces. The gateway is a uniform optional ingress for k6 and does not alter native harness latency.

The inherited architecture gate checks domain/application dependency direction. Tests exercise real SDK client/server exchanges, not a fully mocked A2A implementation. They do not constitute certification against the complete upstream TCK.

See ADRs 0001–0004 and methodology for trade-offs and inference limits.
