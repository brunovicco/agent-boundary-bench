# Harness choice and provenance

Compared on 2026-10-25:

| Candidate | Inspected source SHA | Fit |
|---|---|---|
| `brunovicco/codex-python-engineering-harness` | `e9e297456573d216f070a41a7cdaa108dd599c5b` | Chosen: Codex-native service profile, architecture checks, strict Mypy, central quality gate |
| `brunovicco/claude-python-engineering-harness` | `687182c590a32a401dbb879269820055d200ddc7` | Similar engineering foundation, Claude-specific runtime/plugin integration |

Generation command:

```bash
python bootstrap.py --name agent-boundary-bench --package agent_boundary_bench \
  --target agent-boundary-bench --profile service --python 3.12 --git-init
```

The generator reported harness 1.2.1, service profile, governance none. `.harness.json` retains the original generated-file identities. This is an engineering bootstrap, not an inherited runtime benchmark or an evidence claim.

Retained: project instructions/hooks/skills, strict typing/lint rules, architecture/config/governance validators, quality runner and vendored loop-schema validation. Adapted: dependencies, executable package, tests, README, Dockerfile and CI. Replaced the unused starter commercial tracing/logging modules with experiment-specific OpenTelemetry. No source checkout is a runtime dependency. Governance stays explicitly disabled because no production AI system or commercial LLM is being operated.

Upstream `bootstrap.py --check` would identify intentional customizations against its template; the project's own gate is authoritative for the implemented laboratory. Future template merges must preserve these customizations. Harness reuse follows its MIT license; see THIRD_PARTY_NOTICES.md.
