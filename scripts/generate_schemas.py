#!/usr/bin/env python3
"""Write or verify the versioned JSON Schemas derived from public Pydantic models."""

import argparse
import json
from pathlib import Path

from agent_boundary_bench.benchmark.models import Config, Manifest, ResourceSample, Sample


def rendered() -> dict[Path, str]:
    """Return deterministic schema file contents."""
    models = {
        Path("schemas/config.schema.json"): Config,
        Path("schemas/manifest.schema.json"): Manifest,
        Path("schemas/resourcesample.schema.json"): ResourceSample,
        Path("schemas/sample.schema.json"): Sample,
    }
    return {
        path: json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
        for path, model in models.items()
    }


def main() -> int:
    """Write on request; otherwise fail when committed schemas are stale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    stale: list[str] = []
    for path, content in rendered().items():
        if args.write:
            path.write_text(content)
        elif not path.exists() or path.read_text() != content:
            stale.append(path.as_posix())
    if stale:
        print("Stale schemas: " + ", ".join(stale))
        print("Run: uv run python scripts/generate_schemas.py --write")
        return 1
    print("JSON Schemas match the Pydantic contracts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
