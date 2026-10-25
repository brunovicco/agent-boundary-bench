# ADR 0003: Preserve offered arrivals, lag and failures

Status: accepted. Date: 2026-10-25.

Context: response-paced loops can hide overload through coordinated omission.

Decision: schedule native arrivals on fixed monotonic deadlines independent of responses, retain late scheduling in latency, record explicit drops at bounded concurrency and preserve failed observations. Provide independent k6 constant-arrival-rate validation through a uniform ingress. Repeat full campaigns five times with seeded shuffled order. Record per-round data before calculating statistics.

Consequences: the generator's own lag remains visible and can invalidate a capacity claim. k6/native timers and topology differ and are never pooled. Resource sampling has finite resolution. Difference-of-means is not labeled causal network overhead. Long full campaigns are provided but not fabricated when unexecuted.
