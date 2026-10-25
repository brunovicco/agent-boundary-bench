# ADR 0004: Treat telemetry as an experimental variable

Status: accepted. Date: 2026-10-25.

Context: SDK tracing, sampling and exporters can alter the overhead being measured; ambient sampling settings can also silently remove evidence.

Decision: explicit off/on campaigns. Off uses NullProbe. On owns an always-on SDK provider and synchronous local metadata exporter. HTTP/A2A use public HTTPX hooks and ASGI middleware; MCP uses public request metadata and server middleware for W3C propagation. Never monkey patch SDK internals or export business payloads. Keep provider configuration independent from inherited global sampler settings.

Consequences: traces are correlatable through measured sample trace IDs. Enabled overhead includes serialization and local filesystem export, and cannot be generalized to every collector/sampler. SDK-global automatic spans are not activated. `a2a-otel-kit` remains a separately declared optional treatment, not a hidden change to the baseline or a kernel dependency.
