# v0.3 resource-isolation macOS smoke evidence

This directory contains real Docker Desktop measurements captured on 2026-10-27 UTC from clean
commit `d910a57008c43636c38f4324dd398127f0f781de`. The application image digest was
`sha256:7a342493c90b9ab08add17ee9618acf1147bc7cc1f04e48ba8fbfe6178043f16`.

The source archive supplied by the experiment operator had SHA-256
`a8b20badce926c14b2b019e87d168832bd0b655d71118e789ab96b9a1fd93914`. AppleDouble files and
extended filesystem attributes were excluded while curating the repository copy; measured JSON,
JSONL, CSV, Markdown and PNG content was not rewritten.

Both 12-round profiles passed `scripts/validate_isolation_results.py` with their exact expected
commit, clean-worktree requirement, image provenance, cgroup v2 limits and raw-file hashes. The
constrained profile recorded zero sampling failures in 192 attempts; the generous profile
recorded zero in 212 attempts. Across both profiles, 120/120 offered executions and 24/24 warmups
succeeded, with no errors, timeouts or drops.

`environment.json` records the macOS and Docker environment. Each profile contains its campaign
plan plus the raw per-round manifests, samples and resource observations. `SHA256SUMS` covers the
curated files in this directory. Derived artifacts are under
`reports/v030-resource-isolation-macos/` and regenerate from these raw files.

This is a functional 24-round smoke with one round and five measured requests per configuration.
It validates the treatment and preserves bounded observations; it is not sustained-capacity,
cross-host or repeated causal evidence. The two 180-round repeated profiles remain unexecuted.
