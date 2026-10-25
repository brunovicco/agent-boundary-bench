# ADR 0006: Bound fan-out and factor amplification controls

Status: accepted. Date: 2026-10-25.

Context: fixed three-role orchestration cannot study graph width, while unbounded concurrency can overload the generator and make results irreproducible. Context copies, repeated tools and repeated resources affect different parts of an MCP exchange and should not be conflated implicitly.

Decision: expand fan-out only in complete deterministic three-role blocks, preserve task/result order at fan-in, and guard concurrent adapter calls with an explicit semaphore. Configure context copies, tool repetitions and uncached resource reads independently. Validate every repeated tool result and resource content. Provide separate boundary and amplification campaigns rather than presenting one large crossed matrix as a single causal estimate.

Consequences: callers can reproduce wider graphs without changing the domain or adapter contracts. Operation and context counts are recorded in raw samples. Summed per-operation times may exceed wall time in parallel runs. The synthetic copied context measures transfer/validation amplification, not tokenization, attention quality or model behavior.
