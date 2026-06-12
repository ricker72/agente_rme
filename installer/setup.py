"""
RME Map AI Agent v2.0 — Production Installer

This script handles:
- Dependency installation
- Configuration verification
- Directory structure creation
- Data asset verification
- System health checks

Usage:
    python installer/setup.py
    python installer/setup.py --check-only
    python installer/setup.py --install-deps
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_PYTHON = (3, 9)
REQUIRED_PACKAGES = [
    ("customtkinter", ">=5.2.1", "GUI framework"),
    ("ollama", ">=0.1.9", "AI model integration"),
    ("requests", ">=2.31.0", "HTTP client"),
    ("Pillow", ">=10.1.0", "Image rendering"),
    ("lxml", ">=4.9.3", "XML parsing"),
    ("numpy", ">=1.26.0", "Numerical operations"),
    ("pyyaml", ">=6.0", "YAML config"),
]

OPTIONAL_PACKAGES = [
    ("sentence_transformers", ">=2.2.2", "RAG embeddings"),
]

DIRECTORY_STRUCTURE = [
    "output",
    "cache",
    "config",
    "data",
    "data/blueprints",
    "data/demo_blueprints",
    "logs",
    "exports",
    "release",
    "release/issavi_roshamuul_v1",
]


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")


def print_ok(text: str):
    print(f"  {Colors.GREEN}[OK]{Colors.END} {text}")


def print_err(text: str):
    print(f"  {Colors.RED}[--]{Colors.END} {text}")


def print_warn(text: str):
    print(f"  {Colors.YELLOW}[!!]{Colors.END} {text}")


def check_python_version() -> Tuple[bool, str]:
    major, minor = sys.version_info[:2]
    if major >= REQUIRED_PYTHON[0] and minor >= REQUIRED_PYTHON[1]:
        return True, f"Python {major}.{minor}.{sys.version_info[2]}"
    return (
        False,
        f"Python {major}.{minor} (requires >= {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]})",
    )


def check_packages(packages: list) -> List[Tuple[bool, str, str]]:
    results = []
    for pkg_name, version, desc in packages:
        try:
            mod = __import__(pkg_name)
            ver = getattr(mod, "__version__", "unknown")
            results.append((True, pkg_name, f"{ver} — {desc}"))
        except ImportError:
            results.append((False, pkg_name, f"NOT INSTALLED — {desc}"))
    return results


def install_packages(packages: list) -> bool:
    pkg_names = [pkg[0] for pkg in packages]
    # Map import names to pip names
    pip_names = {
        "customtkinter": "customtkinter",
        "ollama": "ollama",
        "requests": "requests",
        "Pillow": "Pillow",
        "lxml": "lxml",
        "numpy": "numpy",
        "pyyaml": "PyYAML",
        "sentence_transformers": "sentence-transformers",
    }
    pip_list = [pip_names.get(n, n) for n in pkg_names]

    print(f"\nInstalling: {', '.join(pip_list)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install"] + pip_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return True
    except subprocess.CalledProcessError as e:
        print_err(f"pip install failed: {e}")
        return False


def create_directories():
    for d in DIRECTORY_STRUCTURE:
        path = PROJECT_ROOT / d
        path.mkdir(parents=True, exist_ok=True)


def check_ollama() -> Tuple[bool, str]:
    try:
        import requests

        r = requests.get("http://localhost:11434/api/tags", timeout=3)
        if r.status_code == 200:
            models = r.json().get("models", [])
            names = [m.get("name", "unknown") for m in models[:5]]
            return True, f"Running — {len(models)} models: {', '.join(names)}"
        return False, f"Not responding (status {r.status_code})"
    except Exception:
        return False, "Not available at localhost:11434"


def check_config() -> Tuple[bool, str]:
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        return False, "config.json not found"
    try:
        with open(config_path) as f:
            config = json.load(f)
        if config.get("configured"):
            return True, "Configured"
        return False, "Not configured (run GUI setup wizard)"
    except Exception as e:
        return False, f"Error reading config: {e}"


def check_data_assets() -> List[Tuple[bool, str]]:
    results = []
    assets = [
        ("cache/items.json", "Item cache"),
        ("cache/monsters.json", "Monster cache"),
        ("cache/npcs.json", "NPC cache"),
        ("config/production.yaml", "Production config"),
        ("config/development.yaml", "Development config"),
    ]
    for path, desc in assets:
        full = PROJECT_ROOT / path
        if full.exists():
            size = full.stat().st_size
            results.append((True, f"{desc}: {path} ({size:,} bytes)"))
        else:
            results.append((False, f"{desc}: {path} NOT FOUND"))
    return results


def run(check_only=False, install_deps=False):
    print_header("RME Map AI Agent v2.0 — Installer")

    # Python version
    print(f"\n{Colors.BOLD}Python Version:{Colors.END}")
    ok, msg = check_python_version()
    if ok:
        print_ok(msg)
    else:
        print_err(msg)
        if not check_only:
            sys.exit(1)

    # Packages
    print(f"\n{Colors.BOLD}Required Packages:{Colors.END}")
    results = check_packages(REQUIRED_PACKAGES)
    all_ok = True
    missing = []
    for ok, name, msg in results:
        if ok:
            print_ok(msg)
        else:
            print_err(msg)
            all_ok = False
            missing.append(name)

    # Optional packages
    print(f"\n{Colors.BOLD}Optional Packages:{Colors.END}")
    for ok, name, msg in check_packages(OPTIONAL_PACKAGES):
        if ok:
            print_ok(msg)
        else:
            print_warn(msg)

    # Install if requested
    if install_deps and missing:
        print(f"\n{Colors.BOLD}Installing missing packages...{Colors.END}")
        missing_pkgs = [(n, v, d) for n, v, d in REQUIRED_PACKAGES if n in missing]
        if install_packages(missing_pkgs):
            print_ok("Installation complete")
        else:
            print_err("Installation failed")

    # Directory structure
    print(f"\n{Colors.BOLD}Directory Structure:{Colors.END}")
    create_directories()
    print_ok(f"Created {len(DIRECTORY_STRUCTURE)} directories")

    # Ollama
    print(f"\n{Colors.BOLD}Ollama Server:{Colors.END}")
    ok, msg = check_ollama()
    if ok:
        print_ok(msg)
    else:
        print_warn(msg)

    # Config
    print(f"\n{Colors.BOLD}Configuration:{Colors.END}")
    ok, msg = check_config()
    if ok:
        print_ok(msg)
    else:
        print_warn(msg)

    # Data assets
    print(f"\n{Colors.BOLD}Data Assets:{Colors.END}")
    for ok, msg in check_data_assets():
        if ok:
            print_ok(msg)
        else:
            print_warn(msg)

    # Summary
    print_header("Installation Summary")
    if all_ok:
        print_ok("All required packages installed")
    else:
        print_err(f"{len(missing)} packages missing: {', '.join(missing)}")
        print_warn("Run: python installer/setup.py --install-deps")

    print_ok(f"Project root: {PROJECT_ROOT}")
    print_ok(f"Output directory: {PROJECT_ROOT / 'output'}")
    print()
    print("  Next steps:")
    print("    1. Run 'python main.py' to start the GUI")
    print("    2. Run 'python cli.py info' for system info")
    print("    3. Run 'python cli.py generate \"Generate Issavi hunt level 300\"'")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RME Agent Installer")
    parser.add_argument(
        "--check-only", action="store_true", help="Only check, don't install"
    )
    parser.add_argument(
        "--install-deps", action="store_true", help="Install missing dependencies"
    )
    args = parser.parse_args()
    run(check_only=args.check_only, install_deps=args.install_deps)
