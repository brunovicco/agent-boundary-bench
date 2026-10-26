# ADR 0008: Separate requested resource treatments from observed cgroup evidence

- Status: Accepted for `0.3.0.dev0`
- Date: 2026-10-26

## Context

Compose can request CPU and memory limits, but a label or YAML value is not proof that the
runtime enforced it. Native macOS processes do not expose Linux cgroup counters, while Docker
Desktop containers run inside a Linux VM. Local delegation also shares the harness process and
cannot receive a separate specialist container limit without changing the A0 architecture.

## Decision

Keep `ABB_ISOLATION_LABEL` as descriptive metadata and independently sample cgroup v2 files from
each observed process/container. Record limits, cumulative CPU/throttling counters, memory
current/peak and memory event counters with nullable fields. Sample remote HTTP/A2A services
through a metadata-only public application endpoint and sample the harness locally. Retain
process CPU/RSS beside cgroup-wide counters.

Run the same factorized campaign in distinct generous and constrained Compose invocations.
The local arm stays inside the runner cgroup; HTTP/A2A services get their own equal specialist
limits. Add fixed SHA-256 iteration counts and fixed touched allocations as explicit CPU/memory
factors while retaining the original asynchronous wait as a separate factor.

## Consequences

- Reports can reject claims based only on treatment names and expose the observed enforcement.
- HTTP/A2A resource observations add a small control-plane request every sampling interval.
- Cgroup counters are not process counters and may include other processes in the same cgroup.
- Native and Docker measurements remain distinguishable; unavailable fields are null.
- A0 measures shared-resource behavior, not independent specialist isolation.
- Component quotas are not an equal aggregate CPU budget across local and remote topologies.
- The endpoint and monitor need real integration tests, and sampling attempts/failures become
  part of the manifest.
