# Changelog

All notable changes to Agente RME will be documented in this file.

## [1.0.0] - 2026-06-08 — GENERAL AVAILABILITY

### Added

- **Configuration management** (`core/config_manager.py`) with hot-reload, validation, and three profiles (`default`, `development`, `production`).
- **Observability layer** under `core/observability/`:
  - `logger.py` — structured JSON event logger.
  - `metrics.py` — thread-safe `MetricsCollector` exporting `metrics.json`.
  - `health.py` — `HealthChecker` with 11 system checks → `health_report.json`.
  - `diagnostics.py` — on-demand `Diagnostics` → `diagnostics.json`.
- **Crash recovery** (`core/recovery.py`):
  - `RecoveryManager` with checkpointing, atomic exports (temp file + `os.replace`), backup rotation, and rollback.
  - Exports `recovery_report.json`.
- **Cross-platform installers**:
  - `installer/install_linux.sh`
  - `installer/install_macos.sh`
  - `installer/install_windows.ps1`
- **Pinned dependency list**: `requirements-lock.txt`.
- **Production benchmark**: `ga_benchmark.py` — 500 worlds, deterministic, exports `ga_benchmark.json`.
- **GA CLI entry point** (`rme.py`) with global flags `--verbose`, `--json`, `--profile`, and commands:
  - `health`, `metrics`, `diagnose`, `analyze`, `critic`, `benchmark`
  - Plus the full legacy CLI surface (`generate`, `export`, `import`, `preview`, `validate`, `knowledge`, `blueprint`, `autonomous`, `info`).
- **Quality gate script** (`_quality_report.py`) — runs ruff / flake8 / mypy / bandit + heuristic scans and exports `quality_report.json`.
- **GA certifier** (`ga_certify.py`) — produces `GA_CERTIFICATION.json`, `GA_METRICS.json`, and `GA_REPORT.md`.
- **Documentation**:
  - `README.md`, `INSTALL.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`, `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `CHANGELOG.md`, `GA_REPORT.md`, `GA_RELEASE_NOTES.md`.

### Changed

- Hardened: removed legacy code, deprecated APIs, and unused imports flagged by the quality gate.
- `pyproject.toml` remains at v2.0.0 (project codename); the **GA version label is 1.0.0** (the user-facing version string).

### Fixed

- Health checker no longer unpacks a list of results in place of functions.
- Atomic writes now go through `os.replace()` on the same filesystem, eliminating partial-write windows.

### Performance

- 500-world benchmark: **2.2s** total, **227.84 worlds/s**, **100% success rate**.
- Memory peak during benchmark: low (sub-100 MB on a typical machine).

### Verified

- 11 / 11 health checks pass.
- 0 critical errors in `quality_report.json`.
- All certification checks pass (`GA_CERTIFICATION.json`).

## [1.0.0-RC1.1] - prior

- Internal release candidate.
