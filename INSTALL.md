# Agente RME v1.0.0 GA — Installation Guide

This guide walks you through installing Agente RME v1.0.0 GA on Windows, Linux, or macOS. Installation typically completes in **under 5 minutes**.

## Requirements

| Requirement | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.11 or 3.12 |
| RAM | 4 GB | 8 GB |
| Disk | 2 GB free | 5 GB free |
| OS | Win 10 / Ubuntu 20.04 / macOS 12 | latest |
| Ollama (optional) | 0.1.9+ | latest, with `qwen3:8b` model |

> Ollama is **optional** for v1.0.0 GA — the agent runs the full generation pipeline locally without it. Ollama is only used to enrich prompts when an LLM is available.

## Quick install

### Linux

```bash
git clone <repo>
cd agente_rme
chmod +x installer/install_linux.sh
./installer/install_linux.sh
```

### macOS

```bash
git clone <repo>
cd agente_rme
chmod +x installer/install_macos.sh
./installer/install_macos.sh
```

If Python is missing, the installer will attempt `brew install python@3.12`.

### Windows (PowerShell)

```powershell
git clone <repo>
cd agente_rme
powershell -ExecutionPolicy Bypass -File installer/install_windows.ps1
```

## What the installer does

1. Verifies Python 3.10+ is on `PATH`.
2. Creates a `.venv` virtual environment.
3. Installs all dependencies from `requirements-lock.txt`.
4. Verifies every required module imports cleanly.
5. Creates the standard project directory structure:
   - `output/`, `cache/`, `config/`, `data/`, `logs/`, `exports/`, `release/`, `.checkpoint/`, `.backups/`.
6. Probes Ollama at `localhost:11434` (warns if not running).
7. Confirms `config/production.yaml` is present.

## Manual install (fallback)

If the installer does not work in your environment:

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows
.\.venv\Scripts\Activate.ps1
pip install -r requirements-lock.txt
```

## Verifying the install

```bash
python rme.py --version
python rme.py health
```

A healthy install reports:

```
Overall: HEALTHY
Healthy:  11
Degraded: 0
Unhealthy:0
```

## Optional: install Ollama

Ollama is optional. To install it:

```bash
# Linux
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3:8b
ollama serve

# macOS
brew install ollama
ollama pull qwen3:8b

# Windows: download from https://ollama.com/download
```

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

Common issues:

- **Python not found** — install Python 3.10+ and ensure it is on `PATH`.
- **`No module named yaml`** — `pip install -r requirements-lock.txt`.
- **OTBM export is slow** — lower `generation.max_tiles` in `config/production.yaml`.
- **Tests fail on Windows** — run from PowerShell, not `cmd.exe`.
