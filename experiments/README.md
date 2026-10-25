# Recorded experiments

All data under results/ are real measurements collected on 2026-10-25 UTC.
Native measurement commit: 5eefbd76 (full SHA is in every manifest).
Supplemental k6 measurement commit: c3f573a (full SHA is in its manifests).
All recorded measurement runs report git_dirty=false. They used the same installed lockfile.
Reports are generated with the final repository code; the subsequent code change affected
plot labeling/scale and supplemental k6 metadata, not native experiment execution.

| Dataset | Rounds | Successful executions | Purpose |
|---|---:|---:|---|
| pilot | 30 | 1200 | 5 repeats, minimal workload, 1 KiB, 20 RPS, sequential, OTel off/on |
| coverage | 54 | 270 | All payload/wait/mode combinations at 5 RPS, one repeat, telemetry off |
| calibration | 18 | 1350 | 16 KiB, 250 ms wait, sequential/parallel, 5/20/50 RPS, one repeat |
| k6 | 3 | 33 | Supplemental constant-arrival-rate checks, 11 measured executions per scenario |

Native offered=completed=succeeded for all 2820 executions; error/timeout/drop counts are zero.
Each k6 scenario additionally has three warmup executions. k6's boundary scheduling can yield
11 measured iterations in a 2s window at a configured 5/s; actual counts are retained, not
replaced with a theoretical rate*duration count. k6 built-in HTTP summaries include warmup;
custom abb_measured_* metrics do not. No k6/native latency pooling is performed.

Rebuild the native reports:

```bash
uv run abb report --input experiments/results/pilot --output reports/pilot
uv run abb report --input experiments/results/coverage --output reports/coverage
uv run abb report --input experiments/results/calibration --output reports/calibration
```

Do not infer sustained saturation from these short measurements. The full 1620-round campaign
was NOT executed. Native raw schemas/manifests include process CPU/RSS. Supplemental k6 smoke
has no process resource collection, as stated in its manifests. This host is shared, not an
isolated performance rig. Independent per-round results/outliers are deliberately preserved.
