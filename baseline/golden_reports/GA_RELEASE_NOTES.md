# Agente RME v1.0.0 GA — Release Notes

> **Release date:** 2026-06-08
> **Status:** GENERAL AVAILABILITY — PRODUCTION READY — SUPPORTED RELEASE
> **Previous:** v1.0.0-RC1.1

Welcome to **Agente RME v1.0.0 General Availability**. This is the first release we are fully committing to as a production-ready, supported product.

## Highlights

- **Hardened release** — warnings, dead code, and legacy imports cleaned up; 0 critical errors in `quality_report.json`.
- **Cross-platform installers** — Windows (PowerShell), Linux (bash), macOS (bash). Each installs in **under 5 minutes**.
- **Configuration management** — `ConfigManager` with hot-reload, validation, and three profiles (`default`, `development`, `production`).
- **Observability layer** — `core/observability/` provides logger, metrics, health, and diagnostics. Every command exports a JSON snapshot.
- **Health checks** — 11 system-wide checks (`rme health`) producing `health_report.json`. Exit code 0 = healthy.
- **Crash recovery** — `RecoveryManager` checkpoints, atomically writes outputs, and supports rollback. Exports `recovery_report.json`.
- **Production benchmark** — 500 worlds in ~2.2 seconds on a fast machine, **100% success rate**, 227+ worlds/s.
- **CLI production mode** — `--verbose`, `--json`, `--profile` global flags; new commands: `health`, `metrics`, `analyze`, `critic`, `diagnose`, `benchmark`.
- **Full documentation** — `README.md`, `INSTALL.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`, `ARCHITECTURE.md`, `TROUBLESHOOTING.md`, `CHANGELOG.md`, `GA_REPORT.md`, this file.

## New commands (v1.0.0)

```bash
rme health                        # 11 health checks -> health_report.json
rme metrics                       # runtime metrics -> metrics.json
rme diagnose                      # environment + log diagnostics -> diagnostics.json
rme analyze                       # analyze a world or OTBM file
rme critic --target 80            # run the critic
rme benchmark --count 50          # production benchmark (autonomous designer)
ga_benchmark.py --count 500       # fast 500-world GA benchmark
```

## Artifacts produced on a typical run

```
health_report.json        # overall_status, summary, per-check details
metrics.json              # CPU, memory, generations, OTBM, agents
diagnostics.json          # env, file counts, recent errors, config presence
quality_report.json       # ruff, flake8, mypy, bandit + heuristic scans
ga_benchmark.json         # 500-world benchmark result
GA_CERTIFICATION.json     # certification pass/fail
GA_METRICS.json           # aggregate GA metrics
GA_REPORT.md              # human-readable certification report
GA_RELEASE_NOTES.md       # this file
recovery_report.json      # checkpoints, backups, rollback history
```

## Upgrading from v1.0.0-RC1.1

1. Pull the latest tag:
   ```bash
   git fetch --tags
   git checkout v1.0.0
   ```
2. Re-run the installer for your platform (idempotent — it will not overwrite your `config.json`).
3. Verify:
   ```bash
   python rme.py --version    # Agente RME v1.0.0 GA
   python rme.py health       # Overall: HEALTHY
   ```

## Known limitations

- The `rme benchmark` command uses the autonomous designer and is intentionally slow (up to 20 iterations per world). For raw speed, use `ga_benchmark.py`.
- Ollama is fully optional. The agent generates, exports, and validates without an LLM. Ollama only enriches prompts when present.
- The CLI is split between `rme.py` (new GA commands) and `cli.py` (legacy). Both ship in the install. The unified GA surface is `rme.py`.

## Support

- Open an issue on the project repository and attach `diagnostics.json` plus `health_report.json`.
- For production incidents, also attach the relevant `logs/agent_YYYYMMDD.log` slice.

## Verification commands

```bash
# Show the version
python rme.py --version

# Run the full GA certification pipeline
python _quality_report.py
python ga_benchmark.py --count 500
python rme.py health --output health_report.json
python rme.py metrics --output metrics.json
python rme.py diagnose --output diagnostics.json
python ga_certify.py
```

## License

MIT.
