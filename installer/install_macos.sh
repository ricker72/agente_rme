#!/usr/bin/env bash
# installer/install_macos.sh
# Agente RME v1.0.0 GA — macOS Installer
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

CHECK_ONLY=0
SKIP_OLLAMA=0
for arg in "$@"; do
    case "$arg" in
        --check-only) CHECK_ONLY=1 ;;
        --skip-ollama) SKIP_OLLAMA=1 ;;
        --force) FORCE=1 ;;
    esac
done

C_GREEN='\033[0;32m'; C_YELLOW='\033[0;33m'; C_RED='\033[0;31m'
C_BLUE='\033[0;34m'; C_BOLD='\033[1m'; C_END='\033[0m'

step() { echo -e "${C_BOLD}${C_BLUE}[STEP]${C_END} $1"; }
ok()   { echo -e "  ${C_GREEN}[OK]${C_END}  $1"; }
warn() { echo -e "  ${C_YELLOW}[!!]${C_END}  $1"; }
fail() { echo -e "  ${C_RED}[--]${C_END}  $1"; }

echo ""
echo -e "${C_BOLD}${C_BLUE}============================================================${C_END}"
echo -e "${C_BOLD}${C_BLUE}  Agente RME v1.0.0 GA — macOS Installer${C_END}"
echo -e "${C_BOLD}${C_BLUE}============================================================${C_END}"
echo ""

# 1. Python
step "Verifying Python..."
PY=""
for cand in python3 python py; do
    if command -v "$cand" >/dev/null 2>&1; then
        PY="$(command -v "$cand")"
        break
    fi
done
if [ -z "$PY" ]; then
    if command -v brew >/dev/null 2>&1; then
        warn "Python not found. Attempting 'brew install python@3.12'..."
        if [ "$CHECK_ONLY" -eq 0 ]; then
            brew install python@3.12 || true
        fi
    fi
    for cand in python3 python py; do
        if command -v "$cand" >/dev/null 2>&1; then
            PY="$(command -v "$cand")"
            break
        fi
    done
fi
if [ -z "$PY" ]; then
    fail "Python not found. Install with: brew install python@3.12"
    [ "$CHECK_ONLY" -eq 0 ] && exit 1
else
    VER="$("$PY" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
    MAJOR="${VER%%.*}"
    MINOR="${VER##*.}"
    if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
        fail "Python $VER found; need 3.10+"
        [ "$CHECK_ONLY" -eq 0 ] && exit 1
    else
        ok "Python $VER ($PY)"
    fi
fi

# 2. Virtual env
VENV_DIR="$PROJECT_ROOT/.venv"
VENV_PY="$VENV_DIR/bin/python"
if [ ! -x "$VENV_PY" ] && [ "$CHECK_ONLY" -eq 0 ]; then
    step "Creating virtual environment..."
    "$PY" -m venv "$VENV_DIR"
    ok "Created $VENV_DIR"
elif [ -x "$VENV_PY" ]; then
    ok "Virtual env present: $VENV_DIR"
fi

# 3. Install dependencies
if [ "$CHECK_ONLY" -eq 0 ]; then
    step "Installing dependencies from requirements-lock.txt..."
    if [ -x "$VENV_PY" ]; then
        "$VENV_DIR/bin/pip" install --upgrade pip --quiet
        "$VENV_DIR/bin/pip" install -r "$PROJECT_ROOT/requirements-lock.txt" --quiet
    else
        "$PY" -m pip install --upgrade pip --quiet
        "$PY" -m pip install -r "$PROJECT_ROOT/requirements-lock.txt" --quiet
    fi
    if [ $? -eq 0 ]; then
        ok "Dependencies installed"
    else
        fail "pip install failed"
        exit 1
    fi
fi

# 4. Verify imports
step "Verifying Python imports..."
VERIFY_OUT="$("$PY" -c "
import importlib
required = ['customtkinter', 'ollama', 'requests', 'PIL', 'lxml', 'numpy', 'yaml', 'psutil']
ok = True
for m in required:
    try:
        importlib.import_module(m)
        print(f'  [OK] {m}')
    except Exception as e:
        print(f'  [--] {m}: {e}')
        ok = False
print('IMPORT_STATUS=' + ('OK' if ok else 'FAIL'))
" 2>&1)"
echo "$VERIFY_OUT"
if ! echo "$VERIFY_OUT" | grep -q "IMPORT_STATUS=OK"; then
    fail "One or more required modules failed to import"
    [ "$CHECK_ONLY" -eq 0 ] && exit 1
fi

# 5. Project structure
step "Verifying project structure..."
for d in output cache config data logs exports release .checkpoint .backups; do
    mkdir -p "$PROJECT_ROOT/$d"
done
ok "Project structure ready"

# 6. Ollama (optional)
if [ "$SKIP_OLLAMA" -eq 0 ]; then
    step "Checking Ollama..."
    if command -v curl >/dev/null 2>&1; then
        HTTP_CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 http://localhost:11434/api/tags || echo '000')"
        if [ "$HTTP_CODE" = "200" ]; then
            ok "Ollama reachable"
        else
            warn "Ollama not available at localhost:11434 (optional)"
        fi
    else
        warn "curl not available; skipping Ollama check"
    fi
fi

# 7. Config init
step "Initializing configuration..."
if [ -f "$PROJECT_ROOT/config/production.yaml" ]; then
    ok "Production config present"
else
    warn "config/production.yaml missing"
fi

# 8. Summary
echo ""
echo -e "${C_BOLD}${C_BLUE}============================================================${C_END}"
echo -e "${C_BOLD}${C_BLUE}  Installation complete${C_END}"
echo -e "${C_BOLD}${C_BLUE}============================================================${C_END}"
echo ""
echo "Next steps:"
echo "  1. python -m rme health      # run health check"
echo "  2. python cli.py info        # system info"
echo "  3. python cli.py generate 'Issavi hunt level 300'"
echo ""
