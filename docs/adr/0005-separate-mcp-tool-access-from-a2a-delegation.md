# ADR 0005: Separate MCP tool access from A2A delegation

Status: accepted. Date: 2026-10-25.

Context: A2A exposes an independent agent and delegation lifecycle, while MCP exposes tools/resources to a host. Putting both protocols in one undifferentiated ranking would change responsibilities together with transport and invite a false substitutability conclusion.

Decision: preserve A0/A1/A2 as a delegation family and add T0/T1/T2 as an MCP tool-access family. All arms reuse the same deterministic kernel and result oracle, but manifests retain exact scenario, topology, operation counts and byte scope. Use only public MCP v2 `Client`, `MCPServer`, stdio and Streamable HTTP interfaces. Discovery/listing happens before warmup. Legacy SSE is not labeled as Streamable HTTP.

Consequences: within-family boundary comparisons are defensible under matched configurations. Cross-family observations can inform end-to-end budgets but cannot establish that MCP replaces A2A or vice versa. MCP adds `mcp-types` and `httpx2` without replacing A2A's separate HTTPX client. Direct dispatch is clearly described as an SDK in-process facility, not a network transport.
