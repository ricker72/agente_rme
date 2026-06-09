# Agente RME v1.0.0 GA — Troubleshooting

This page lists the most common issues and how to fix them.

## 1. Installation issues

### `python: command not found`

- Install Python 3.10+ from <https://python.org>.
- Make sure Python is on `PATH` (Windows: re-check the installer checkbox).
- On Linux/macOS, you may need to use `python3` instead of `python`.

### `pip install` fails on Windows

- Run PowerShell as Administrator.
- Upgrade pip: `python -m pip install --upgrade pip`.

### `No module named yaml`

```bash
pip install -r requirements-lock.txt
```

### `No module named customtkinter`

The GUI dependency is required for `main.py` but optional for the CLI. Install it:

```bash
pip install customtkinter
```

## 2. CLI issues

### `rme: command not found`

Use `python rme.py <command>` directly, or install in editable mode:

```bash
pip install -e .
```

### `rme health` reports unhealthy

- Read the `health_report.json` for the failing check.
- Common cause: missing knowledge dataset. Run:
  ```bash
  python rme.py knowledge build --dir data --output output/knowledge_dataset.json
  ```

### `rme benchmark` is too slow

The `rme benchmark` command uses the **autonomous** designer, which runs up to 20 optimization iterations per world. For raw speed, use the dedicated GA benchmark instead:

```bash
python ga_benchmark.py --count 500
```

## 3. Generation issues

### Empty world (`tile_count() == 0`)

- Verify the prompt — try `"Issavi hunt level 300"` directly.
- Check `logs/agent_YYYYMMDD.log` for the most recent errors.

### OTBM export is slow

Lower the generation cap:

```yaml
# config/production.yaml
generation:
  max_tiles: 50000
```

### Lua export fails validation

```bash
python cli.py validate --input output/generated.otbm
```

Or run the validator programmatically:

```python
from core.exporters import LuaValidator
v = LuaValidator()
print(v.validate(open("output/generated.lua").read()))
```

## 4. Observability issues

### `metrics.json` is empty

`MetricsCollector` is per-process. Run a generation after the metrics command for a non-trivial snapshot:

```bash
python rme.py generate "Issavi hunt level 300" && python rme.py metrics
```

### No `events.jsonl`

Events are emitted when you call `get_observability_logger().event(...)`. The CLI commands emit a small set of events automatically. To see a steady stream, run a benchmark:

```bash
python ga_benchmark.py --count 100
ls -lh logs/
```

## 5. Recovery

### Restoring a corrupted OTBM

```python
from core.recovery import RecoveryManager
rm = RecoveryManager()
restored = rm.rollback("output/generated.otbm")
print("Restored from:", restored)
```

### Listing available backups

```python
for b in RecoveryManager().list_backups():
    print(b)
```

## 6. Performance tuning

- Use the `production` profile: `python rme.py --profile production …`
- Lower `generation.max_tiles` for faster runs.
- Disable Ollama when not needed (it is purely optional).
- Set `RME_PROFILE=production` in the environment to avoid passing `--profile` every time.

## 7. Where to get help

- Run `python rme.py diagnose` and attach `diagnostics.json` to the issue.
- Check `logs/agent_YYYYMMDD.log` for the most recent error.
- Open a ticket with: Python version, OS, output of `python rme.py --version`, and `diagnostics.json`.
