#!/usr/bin/env bash
# Requires the user's own authenticated gh CLI. Never changes an existing repository.
set -euo pipefail
owner="$(gh api user --jq .login)"
repository="$owner/agent-boundary-bench"
if gh repo view "$repository" >/dev/null 2>&1; then
  echo "Repository already exists; refusing to create or overwrite: $repository" >&2
  exit 1
fi
gh repo create "$repository" --private --source=. --remote=origin --push
