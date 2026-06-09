# Agente RME v1.0.0 GA — Architecture

This document describes the high-level architecture of Agente RME v1.0.0 GA.

## 1. Goals

- **Production-grade stability** for OTBM map generation.
- **Observability** — every agent, exporter, and OTBM operation is logged.
- **Recoverability** — pipeline failures do not corrupt output.
- **Configurability** — hot-reloadable profiles for dev / production.
- **Installability** — under five minutes on Windows, Linux, macOS.

## 2. Top-level components

```
┌─────────────────────────────────────────────────────────────┐
│                       rme.py (CLI)                          │
│   generate | analyze | critic | health | metrics | …        │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼─────────────────────┐
        │                    │                     │
        ▼                    ▼                     ▼
   core.generators    core.exporters       core.otbm
   (WorldGenerator)   (Lua, PNG)           (Exporter, Validator, Importer)
        │                    │                     │
        └──────────┬─────────┴─────────┬───────────┘
                   ▼                   ▼
              WorldModel           *.lua, *.otbm
                   │
        ┌──────────┴───────────┐
        ▼                      ▼
  core.knowledge        core.critic
  (RAG layer)           (quality scoring)
        │                      │
        └──────────┬───────────┘
                   ▼
          core.blueprint_intelligence
          (embeddings, evolution, fusion)
                   │
                   ▼
            core.autonomous
            (AutonomousWorldDesigner)
```

## 3. Side systems (GA additions)

```
   config_manager.py  ───►  config/{default,development,production}.yaml
   core/observability/logger.py     ──► logs/agent_YYYYMMDD.log + events.jsonl
   core/observability/metrics.py    ──► metrics.json
   core/observability/health.py     ──► health_report.json
   core/observability/diagnostics.py──► diagnostics.json
   core/recovery.py                 ──► recovery_report.json, .backups/, .checkpoint/
```

These run alongside the main pipeline. They are observable (emit JSON), recoverable (no state is hidden in memory), and configurable (driven by `ConfigManager`).

## 4. Data flow

1. **CLI** receives a prompt and optional flags.
2. **ConfigManager** loads the active profile (`default`, `development`, or `production`).
3. **Generator** produces a `WorldModel`.
4. **Exporter** writes Lua, OTBM, and XML sidecars.
5. **RecoveryManager** checkpoints and atomically writes the outputs, backing up any existing files.
6. **Observability** records each step and exports a snapshot.
7. **HealthChecker** runs periodically (or on demand) and exports a health report.

## 5. Persistence

| Path | Purpose |
|---|---|
| `output/` | Generated worlds (Lua, OTBM, PNG) |
| `cache/` | Knowledge embeddings, parsed items |
| `data/` | Source knowledge files |
| `logs/` | Rotating text logs + structured JSONL |
| `release/` | Released map packages |
| `exports/` | Cross-server exports |
| `.checkpoint/` | Recovery checkpoints (capped) |
| `.backups/` | Automatic `.bak` files |

## 6. CLI surface (v1.0.0)

- `generate`, `analyze`, `critic`, `health`, `metrics`, `diagnose`, `benchmark`
- `knowledge {build,search,similar,stats}`
- `blueprint {build,similar,cluster,evolve,fuse,recommend,rank,generate}`
- `autonomous {generate,optimize,benchmark,report}`
- `export`, `import`, `preview`, `validate`, `info`

Global flags: `--verbose`, `--json`, `--profile`, `--version`.

## 7. Cross-cutting concerns

- **Thread safety** — `ConfigManager`, `MetricsCollector`, `RecoveryManager`, and `ObservabilityLogger` use internal locks.
- **Determinism** — the generator is seeded; the benchmark uses deterministic seeds.
- **Atomicity** — exports go through a temp file + `os.replace()` to avoid partial writes.
- **Backups** — any existing target is moved to `.backups/<name>.<ts>.bak` before overwrite.

## 8. Future-proofing

- The agent layer is intentionally decoupled from the RME-specific code so a future `agent` or `studio` interface can be added without touching the pipeline.
- The observability layer is generic; it can be reused by any Python project.
- The CLI is split into a unified `rme.py` entry point and the legacy `cli.py`, so the legacy surface remains stable while new GA commands are added in `rme.py`.
