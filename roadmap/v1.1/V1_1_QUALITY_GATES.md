# Agente RME v1.1 Quality Gates

## Snapshot Metadata

```json
{
  "status": "FROZEN",
  "release": "ui-v1.0",
  "support": "SUPPORTED"
}
```

## Baseline Rule

v1.1 must preserve the UI v1.0 production baseline while adding new capability on development branches only.

## Required Static Gates

```powershell
python -m ruff check ui tests/ui
python -m flake8 ui tests/ui
python -m mypy ui tests/ui
```

Required result: PASS with zero blocking issues.

## Required Test Gates

```powershell
python -m pytest tests/ui -v
```

Required result: PASS.

## Required Coverage Gates

- Overall UI coverage must remain >= 90%.
- No production UI file may fall below 70%.
- No production page, widget, service, or adapter may fall below 80% unless a documented exception is approved.

## Runtime Gates

- Startup PASS.
- Navigation PASS.
- Thread safety PASS.
- Memory profile PASS.
- Event bus runtime PASS.
- Shutdown PASS.

## Packaging Gates

- PyInstaller spec remains valid.
- Packaged executable launches.
- Required resources load.
- Package size remains PASS or WARNING.

## v1.1 Feature-Specific Gates

- World Generator 2.0 must include deterministic test fixtures for cities, hunts, dungeons, boss areas, and quest chains.
- Blueprint Intelligence 2.0 must include traceable learned-pattern fixtures for Issavi, Roshamuul, Soul War, Falcon Bastion, Library, and Ferumbras.
- Visual Critic 2.0 must score pathing, density, spawn quality, progression, and reward loops with regression fixtures.
- Autonomous Designer 2.0 must prove the Generate -> Critic -> Improve loop stops correctly at target score or iteration limit.

## Release Candidate Gates

Before v1.1 release certification, regenerate architecture, quality, runtime, packaging, production metrics, and release notes under a new v1.1 baseline folder.
