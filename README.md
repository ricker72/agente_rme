# Agente RME v1.0.0 GA

> **Status:** GENERAL AVAILABILITY — PRODUCTION READY — SUPPORTED RELEASE

Agente RME is an AI-powered Tibia map generator for **RME** (Remere's Map Editor) and **OpenTibiaBR** servers. It produces `.otbm` binary maps, `.lua` spawn scripts, and accompanying XML metadata, all driven by natural-language prompts and a knowledge base harvested from real hunts, cities, and boss rooms.

This release is the **General Availability** build: hardened, installable in under five minutes, observable, recoverable, and supported.

---

## Quick Start

```bash
# 1. Install (Linux / macOS)
./installer/install_linux.sh
# or macOS:
./installer/install_macos.sh
# or Windows (PowerShell):
powershell -ExecutionPolicy Bypass -File installer/install_windows.ps1

# 2. Run a health check
python rme.py health

# 3. Generate a world
python rme.py generate "Issavi hunt level 300"

# 4. Run a production benchmark
python ga_benchmark.py --count 500
```

---

## CLI Reference (v1.0.0 GA)

| Command | Description |
|---|---|
| `rme generate <prompt>` | Generate a world from a natural-language prompt |
| `rme analyze` | Analyze a generated world or OTBM file |
| `rme critic` | Run the critic on a world and report score |
| `rme knowledge {build,search,similar,stats}` | Manage the knowledge dataset |
| `rme blueprint {build,similar,cluster,evolve,fuse,recommend,rank,generate}` | Blueprint intelligence |
| `rme autonomous {generate,optimize,benchmark,report}` | Autonomous world designer |
| `rme health` | Run system health checks → `health_report.json` |
| `rme metrics` | Export runtime metrics → `metrics.json` |
| `rme diagnose` | Run diagnostics → `diagnostics.json` |
| `rme benchmark --count N` | Production benchmark → `ga_benchmark.json` |

### Global flags

- `--verbose` — enable DEBUG logging
- `--json` — emit machine-readable JSON
- `--profile {default,development,production}` — configuration profile

### Examples

```bash
# Health check, JSON output, production profile
python rme.py --profile production --json health

# Generate and analyze
python rme.py generate "Roshamuul raid 400"
python rme.py analyze

# Benchmark with 200 worlds
python rme.py benchmark --count 200 --output benchmark_200.json

# Run a full production GA benchmark
python ga_benchmark.py --count 500 --output ga_benchmark.json
```

---

## Documentation

- [INSTALL.md](INSTALL.md) — installation, dependencies, troubleshooting
- [USER_GUIDE.md](USER_GUIDE.md) — common workflows, examples
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — extending the agent
- [ARCHITECTURE.md](ARCHITECTURE.md) — system architecture
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — common issues
- [CHANGELOG.md](CHANGELOG.md) — release history
- [GA_REPORT.md](GA_REPORT.md) — GA certification report
- [GA_RELEASE_NOTES.md](GA_RELEASE_NOTES.md) — GA release notes

---

## What's in v1.0.0 GA

- ✅ Hardened release (warnings, dead code, legacy imports removed)
- ✅ Cross-platform installer (Windows / Linux / macOS)
- ✅ Configuration management with hot-reload (`ConfigManager`)
- ✅ Observability layer (logger, metrics, health, diagnostics)
- ✅ Health-check system (`rme health`) → `health_report.json`
- ✅ Crash recovery (checkpointing, atomic exports, rollback) → `recovery_report.json`
- ✅ Production benchmark (500 worlds) → `ga_benchmark.json`
- ✅ CLI production mode (`--verbose`, `--json`, `--profile`)
- ✅ Documentation suite
- ✅ 99%+ benchmark success rate achieved (currently 100%)

---

## Project layout

```
agente_rme/
├── installer/          # Cross-platform installers
├── config/             # default.yaml, development.yaml, production.yaml
├── core/
│   ├── observability/  # logger.py, metrics.py, health.py, diagnostics.py
│   ├── recovery.py     # checkpointing, safe exports, rollback
│   ├── config_manager.py
│   ├── generators/
│   ├── exporters/
│   ├── otbm/
│   ├── knowledge/
│   ├── critic/
│   ├── blueprint_intelligence/
│   ├── autonomous/
│   └── ...
├── tests/              # test_*.py
├── docs/               # INSTALL.md, USER_GUIDE.md, ...
├── rme.py              # v1.0.0 GA CLI entry point
├── cli.py              # legacy CLI
├── ga_benchmark.py     # production benchmark
├── requirements.txt
└── requirements-lock.txt
```

---

## License

MIT — see [pyproject.toml](pyproject.toml).
