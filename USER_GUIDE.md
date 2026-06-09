# Agente RME v1.0.0 GA — User Guide

This guide covers the most common workflows for the GA release.

## 1. Generate a world from a prompt

```bash
python rme.py generate "Issavi hunt level 300"
```

Output:

```
output/
├── generated.lua
├── generated.otbm
├── generated_preview.png
├── generated.monster.xml      (if spawns)
├── generated.houses.xml       (if houses)
├── generated.waypoints.xml    (if waypoints)
└── generated_report.json
```

### With explicit options

```bash
python rme.py generate \
  --type hunt \
  --theme issavi \
  --level 280 \
  --size 30x30 \
  --seed 42 \
  --output output/issavi_hunt_280
```

## 2. Analyze a generated world

```bash
python rme.py analyze
# or
python rme.py analyze --input output/issavi_hunt_280/generated.otbm --output output/analysis.json
```

The analysis reports tile count, region count, structure count, and (for OTBM) validation results.

## 3. Run the critic

```bash
python rme.py critic --target 80
```

Returns PASS / FAIL plus a critic score.

## 4. Build and search the knowledge dataset

```bash
# Build from the data/ directory
python rme.py knowledge build --dir data --output output/knowledge_dataset.json

# Search
python rme.py knowledge search "issavi hunt"

# Similar
python rme.py knowledge similar hunt "Asura Palace"

# Stats
python rme.py knowledge stats
```

## 5. Run health checks

```bash
python rme.py health
```

Exports `health_report.json`. The report contains:

- **system** — Python version, platform, memory, disk
- **module** — one check per core module (generators, exporters, otbm, preview, knowledge, critic, blueprint_intelligence)
- **pipeline** — a tiny generation succeeds
- **knowledge** — dataset present and loadable
- **blueprints** — at least one blueprint file present

Exit code 0 = healthy, 1 = unhealthy.

## 6. Run the production benchmark

```bash
python ga_benchmark.py --count 500 --output ga_benchmark.json
```

Reports:

- success rate (target ≥ 99%)
- worlds/second
- avg critic score
- avg / peak memory
- avg CPU%

A typical fast machine reports >200 worlds/s and 100% success.

## 7. Diagnose issues

```bash
python rme.py diagnose
```

Exports `diagnostics.json` containing environment details, file counts, recent log errors, and config presence.

## 8. Configuration profiles

```bash
# Use the production profile
python rme.py --profile production generate "Issavi hunt level 300"

# Or set the env var
RME_PROFILE=production python rme.py generate "..."
```

Profiles live in `config/`:

- `default.yaml` — neutral
- `development.yaml` — debug logging, no minification
- `production.yaml` — INFO logging, optimization on, validation strict

## 9. JSON output

Any command can emit machine-readable JSON:

```bash
python rme.py --json health
python rme.py --json metrics
python rme.py --json benchmark --count 50
```

## 10. Recovery

The agent checkpoints after every generation. To roll back an OTBM:

```python
from core.recovery import RecoveryManager
rm = RecoveryManager()
rm.rollback("output/generated.otbm")  # restores latest .bak
```

Inspect backups:

```python
for b in rm.list_backups():
    print(b["name"], b["size_bytes"], b["mtime"])
```

## Examples

### End-to-end GA workflow

```bash
# 1. Health
python rme.py health
# 2. Generate
python rme.py generate "Roshamuul raid level 400"
# 3. Analyze
python rme.py analyze
# 4. Critic
python rme.py critic --target 85
# 5. Benchmark
python ga_benchmark.py --count 500
# 6. Diagnostics
python rme.py diagnose
```

All artifacts land in the project root as `*.json` and under `output/`.
