# Agente RME v1.0.0 GA — Developer Guide

This guide is for contributors extending the agent.

## Project layout

```
agente_rme/
├── core/
│   ├── observability/   # logger, metrics, health, diagnostics
│   ├── recovery.py
│   ├── config_manager.py
│   ├── generators/
│   ├── exporters/       # Lua exporter + validator
│   ├── otbm/            # OTBM read/write/validate
│   ├── preview/         # PNG preview generator
│   ├── knowledge/       # RAG layer
│   ├── critic/
│   ├── blueprint_intelligence/
│   ├── autonomous/      # Autonomous World Designer
│   ├── agents/          # multi-agent orchestrator
│   └── ...
├── tests/
├── installer/
├── config/
├── docs/
├── rme.py               # v1.0.0 GA entry point
├── cli.py               # legacy CLI
└── ga_benchmark.py
```

## Adding a new CLI command

1. Implement `cmd_<name>(args)` in `rme.py`.
2. Register a sub-parser inside `main()`:

```python
p = sub.add_parser("mycommand", help="...")
p.add_argument("--foo", default="bar")
p.set_defaults(func=cmd_mycommand)
```

3. Optional: support `--json` by emitting `json.dumps(payload, indent=2)` when `getattr(args, "json", False)` is true.

## Adding a new health check

Append a check function to `core/observability/health.py` and register it in `HealthChecker._checks`:

```python
def _check_my_thing() -> CheckResult:
    return CheckResult(name="mything", category="custom",
                       status=HealthStatus.HEALTHY, message="ok",
                       timestamp=_utc_iso())

class HealthChecker:
    def __init__(self):
        self._checks = [
            _check_system,
            _check_my_thing,   # <-- add here
            ...
        ]
```

## Adding a new metric

`core/observability/metrics.py` exposes a thread-safe `MetricsCollector`:

```python
from core.observability.metrics import MetricsCollector
mc = MetricsCollector()
mc.start_agent("my-agent")
# ... do work ...
mc.end_agent("my-agent", success=True)
mc.record_generation(duration_ms=120.0, tiles=4200)
mc.record_otbm(tiles=4200, items=128, spawns=12, duration_ms=80.0)
mc.export("metrics.json")
```

## Adding a new config key

1. Add the key to `config/default.yaml` (and any profile that should override it).
2. Add the key + expected type to `_SCHEMA_KEYS` in `core/config_manager.py`.
3. Read it via `ConfigManager.instance().get("my.key")`.

## Adding a new exporter

Exporters implement two methods: `export(world, **kwargs) -> str/bytes` and (optionally) a validator.

```python
from core.exporters import BaseExporter

class TxtExporter(BaseExporter):
    def export(self, world, **kwargs) -> str:
        # ... serialize world to text ...
        return text
```

## Adding a new recovery strategy

`RecoveryManager` already covers checkpointing + atomic write + rollback. To add a new strategy, subclass `RecoveryManager` and add a method that uses the same `safe_write_bytes` helper.

## Style and tooling

- Black (line length 100) for formatting
- Mypy for type checks
- Pytest for tests (in `tests/`)
- Ruff for linting

## Logging conventions

- Use `core.logging.logger.Logger.get_logger(__name__)` for non-observability code.
- Use `core.observability.logger.get_observability_logger()` for structured events.

## Testing

```bash
pytest tests/ -v
pytest tests/integration/test_autonomous_50world_benchmark.py -v
```

## Pull request checklist

- [ ] Tests pass
- [ ] New CLI commands have `--json` support
- [ ] New health checks are registered in `HealthChecker`
- [ ] New metrics are added to `MetricsCollector` and exported in `metrics.json`
- [ ] No new top-level dependencies; if unavoidable, update `requirements-lock.txt`
