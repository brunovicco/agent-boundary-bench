# ADR 0002: Match HTTP and A2A deployment and response semantics

Status: accepted. Date: 2026-10-25.

Context: comparing a local call with a remote workflow can accidentally compare storage, discovery and worker counts.

Decision: HTTP and A2A use one separate worker containing the same three synthetic roles, same runtime/host/HTTP version/pool limits, no TLS/retries/storage workload and one immediate response per delegation. A2A performs cached card resolution before warmup and uses JSON-RPC only. A0 uses the same application port and domain objects without network or JSON round trips.

Consequences: this isolates a specific warm steady-state boundary treatment. It does not estimate cold discovery, durable tasks, streaming, independent scaling or security isolation. Native and Compose topologies are distinct experiments. A remote process is deliberately absent from A0 and must be reported as such.
