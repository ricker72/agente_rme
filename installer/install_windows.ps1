#!/usr/bin/env pwsh
# installer/install_windows.ps1
# Agente RME v1.0.0 GA — Windows Installer
# Installs Python dependencies, verifies environment, configures agent.

[CmdletBinding()]
param(
    [switch]$CheckOnly,
    [switch]$SkipOllama,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $ProjectRoot

function Write-Step($msg) { Write-Host "[STEP] $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "  [OK]  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  [!!]  $msg" -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "  [--]  $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "  Agente RME v1.0.0 GA — Windows Installer" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""

# 1. Python
Write-Step "Verifying Python..."
$py = $null
foreach ($cand in @("python", "python3", "py")) {
    $found = Get-Command $cand -ErrorAction SilentlyContinue
    if ($found) { $py = $found.Source; break }
}
if (-not $py) {
    Write-Fail "Python not found in PATH. Install Python 3.10+ from python.org"
    if (-not $CheckOnly) { exit 1 }
} else {
    $ver = & $py -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    $major = [int]($ver.Split('.')[0])
    $minor = [int]($ver.Split('.')[1])
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
        Write-Fail "Python $ver found; need 3.10+"
        if (-not $CheckOnly) { exit 1 }
    } else {
        Write-OK "Python $ver ($py)"
    }
}

# 2. Virtual env
$venvDir = Join-Path $ProjectRoot ".venv"
$venvPy = Join-Path $venvDir "Scripts/python.exe"
if (-not (Test-Path $venvPy) -and -not $CheckOnly) {
    Write-Step "Creating virtual environment..."
    & $py -m venv $venvDir
    Write-OK "Created $venvDir"
} elseif (Test-Path $venvPy) {
    Write-OK "Virtual env present: $venvDir"
}

# 3. Install dependencies
if (-not $CheckOnly) {
    Write-Step "Installing dependencies from requirements-lock.txt..."
    $pip = if (Test-Path $venvPy) { Join-Path $venvDir "Scripts/pip.exe" } else { "pip" }
    & $pip install --upgrade pip --quiet
    & $pip install -r (Join-Path $ProjectRoot "requirements-lock.txt") --quiet
    if ($LASTEXITCODE -eq 0) {
        Write-OK "Dependencies installed"
    } else {
        Write-Fail "pip install failed (exit $LASTEXITCODE)"
        exit 1
    }
}

# 4. Verify imports
Write-Step "Verifying Python imports..."
$verifyScript = @"
import importlib
required = [
    'customtkinter', 'ollama', 'requests', 'PIL', 'lxml', 'numpy', 'yaml', 'psutil',
]
ok = True
for m in required:
    try:
        importlib.import_module(m)
        print(f'  [OK] {m}')
    except Exception as e:
        print(f'  [--] {m}: {e}')
        ok = False
print('IMPORT_STATUS=' + ('OK' if ok else 'FAIL'))
"@
$verifyOut = & $py -c $verifyScript 2>&1
$verifyOut | ForEach-Object { Write-Host $_ }
if ($verifyOut -notmatch "IMPORT_STATUS=OK") {
    Write-Fail "One or more required modules failed to import"
    if (-not $CheckOnly) { exit 1 }
}

# 5. Project structure
Write-Step "Verifying project structure..."
$dirs = @("output", "cache", "config", "data", "logs", "exports", "release", ".checkpoint", ".backups")
foreach ($d in $dirs) {
    $p = Join-Path $ProjectRoot $d
    if (-not (Test-Path $p)) {
        New-Item -ItemType Directory -Path $p -Force | Out-Null
    }
}
Write-OK "Project structure ready"

# 6. Ollama (optional)
if (-not $SkipOllama) {
    Write-Step "Checking Ollama..."
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:11434/api/tags" -TimeoutSec 3 -UseBasicParsing
        if ($r.StatusCode -eq 200) {
            Write-OK "Ollama reachable"
        } else {
            Write-Warn "Ollama status $($r.StatusCode)"
        }
    } catch {
        Write-Warn "Ollama not available at localhost:11434 (optional)"
    }
}

# 7. Config init
Write-Step "Initializing configuration..."
$cfgFile = Join-Path $ProjectRoot "config/production.yaml"
if (-not (Test-Path $cfgFile)) {
    Write-Warn "config/production.yaml missing"
} else {
    Write-OK "Production config present"
}

# 8. Summary
Write-Host ""
Write-Host "============================================================" -ForegroundColor Blue
Write-Host "  Installation complete" -ForegroundColor Blue
Write-Host "============================================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. python -m rme health      # run health check"
Write-Host "  2. python cli.py info        # system info"
Write-Host "  3. python cli.py generate 'Issavi hunt level 300'"
Write-Host ""
