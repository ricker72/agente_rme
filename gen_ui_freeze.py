#!/usr/bin/env python3
"""
UI Freeze Certification Script
Generates baseline/ui-freeze/ artifacts for Agente RME v1.0.0 GA
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def run(cmd, cwd=None):
    """Run a shell command and return stdout."""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd or BASE)
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except Exception as e:
        return "", str(e), -1


def count_files_recursive(directory):
    """Count all .py files recursively excluding __pycache__."""
    count = 0
    for f in BASE.joinpath(directory).rglob("*.py"):
        if "__pycache__" not in str(f):
            count += 1
    return count


def check_imports(file_path, forbidden):
    """Check if a file contains any forbidden imports."""
    violations = []
    try:
        with open(file_path) as f:
            content = f.read()
        for imp in forbidden:
            if f"import {imp}" in content or f"from {imp}" in content:
                violations.append((str(file_path.relative_to(BASE)), imp))
    except Exception:
        pass
    return violations


def main():
    # === COLLECT METRICS ===
    total_ui_files = count_files_recursive("ui")
    total_ui_tests = count_files_recursive("tests/ui")

    # Pages count (minus __init__)
    pages_files = sorted(BASE.joinpath("ui/pages").glob("*.py"))
    pages_count = len([p for p in pages_files if p.name != "__init__.py"])

    widgets_files = sorted(BASE.joinpath("ui/widgets").glob("*.py"))
    widgets_count = len([p for p in widgets_files if p.name != "__init__.py"])

    services_files = sorted(BASE.joinpath("ui/services").glob("*.py"))
    services_count = len([p for p in services_files if p.name != "__init__.py"])

    adapters_files = sorted(BASE.joinpath("ui/adapters").glob("*.py"))
    adapters_count = len([p for p in adapters_files if p.name not in ("__init__.py", "_helpers.py")])

    models_files = sorted(BASE.joinpath("ui/models").glob("*.py"))
    models_dto_count = len([p for p in models_files if p.name != "__init__.py"])

    plugins_files = sorted(BASE.joinpath("ui/plugins").glob("*.py"))
    plugins_count = len([p for p in plugins_files if p.name != "__init__.py"])

    root_ui_files = sorted(BASE.joinpath("ui").glob("*.py"))
    root_ui_count = len([p for p in root_ui_files if p.name != "__init__.py"])

    # Events
    events_count = 0
    events_dir = BASE / "ui" / "events"
    if events_dir.exists():
        events_count = len([p for p in events_dir.glob("*.py") if p.name != "__init__.py"])

    # === RUN QUALITY GATES ===
    print("=" * 60)
    print("UI FREEZE CERTIFICATION - QUALITY GATES")
    print("=" * 60)

    # ruff
    print("\n--- python -m ruff check ui tests/ui ---")
    ruff_out, ruff_err, ruff_rc = run("python -m ruff check ui tests/ui 2>&1")
    if ruff_out:
        print(ruff_out[:2000])
    if ruff_err:
        print(ruff_err[:500])
    ruff_issues = ruff_rc  # ruff exit code is number of issues

    # flake8
    print("\n--- python -m flake8 ui tests/ui ---")
    flake8_out, flake8_err, flake8_rc = run("python -m flake8 ui tests/ui 2>&1")
    if flake8_out:
        print(flake8_out[:2000])
    if flake8_err:
        print(flake8_err[:500])
    flake8_issues = len([l for l in flake8_out.split("\n") if l.strip()]) if flake8_out else 0

    # mypy
    print("\n--- python -m mypy ui tests/ui ---")
    mypy_out, mypy_err, mypy_rc = run("python -m mypy ui tests/ui 2>&1")
    if mypy_out:
        print(mypy_out[:2000])
    if mypy_err:
        print(mypy_err[:500])
    # Count error lines (excluding header/footer)
    mypy_lines = [l for l in mypy_out.split("\n") if l.strip() and not l.startswith("Success") and not l.startswith("Found")]
    mypy_issues = len(mypy_lines)

    # pytest
    print("\n--- python -m pytest tests/ui -v ---")
    pytest_out, pytest_err, pytest_rc = run("python -m pytest tests/ui -v 2>&1")
    if pytest_out:
        print(pytest_out[:4000])
    if pytest_err:
        print(pytest_err[:500])

    # Parse pytest summary
    passed = 0
    failed = 0
    skipped = 0
    warnings = 0
    error_lines = pytest_out.split("\n")
    for line in error_lines:
        line = line.strip()
        if "passed" in line and "failed" in line and "=" not in line:
            import re
            m = re.search(r'(\d+)\s+passed', line)
            if m:
                passed = int(m.group(1))
            m = re.search(r'(\d+)\s+failed', line)
            if m:
                failed = int(m.group(1))
            m = re.search(r'(\d+)\s+skipped', line)
            if m:
                skipped = int(m.group(1))
            m = re.search(r'(\d+)\s+warnings', line)
            if m:
                warnings = int(m.group(1))

    # coverage
    print("\n--- python -m pytest tests/ui --cov=ui --cov-report= ---")
    cov_out, cov_err, cov_rc = run("python -m pytest tests/ui --cov=ui --cov-report= 2>&1")
    if cov_out:
        print(cov_out[:1500])
    coverage_pct = 0.0
    for line in cov_out.split("\n"):
        if "TOTAL" in line:
            parts = line.split()
            for p in parts:
                if "%" in p:
                    try:
                        coverage_pct = float(p.replace("%", ""))
                    except ValueError:
                        pass

    # === BOUNDARY SCAN ===
    print("\n" + "=" * 60)
    print("BOUNDARY SCAN - FORBIDDEN IMPORTS CHECK")
    print("=" * 60)

    forbidden_imports = ["core.", "agents."]
    violations = []

    # Check pages
    for f in BASE.joinpath("ui/pages").rglob("*.py"):
        violations.extend(check_imports(f, forbidden_imports))

    # Check widgets
    for f in BASE.joinpath("ui/widgets").rglob("*.py"):
        violations.extend(check_imports(f, forbidden_imports))

    # Check services
    for f in BASE.joinpath("ui/services").rglob("*.py"):
        violations.extend(check_imports(f, forbidden_imports))

    # Check models
    for f in BASE.joinpath("ui/models").rglob("*.py"):
        violations.extend(check_imports(f, forbidden_imports))

    # Check root UI files
    for f in BASE.joinpath("ui").glob("*.py"):
        violations.extend(check_imports(f, forbidden_imports))

    if violations:
        print("FORBIDDEN IMPORTS FOUND:")
        for file, imp in violations:
            print(f"  {file} -> {imp}")
    else:
        print("PASS: No forbidden imports in pages, widgets, services, or models.")

    # Verify adapters have core references (allowed)
    adapter_core_refs = []
    for f in BASE.joinpath("ui/adapters").rglob("*.py"):
        v = check_imports(f, forbidden_imports)
        if v:
            adapter_core_refs.extend(v)

    print(f"\nAdapters with core references (allowed): {len(adapter_core_refs)}")
    for file, imp in adapter_core_refs:
        print(f"  {file} -> {imp}")

    # === CREATE BASELINE DIRECTORY ===
    baseline_dir = BASE / "baseline" / "ui-freeze"
    baseline_dir.mkdir(parents=True, exist_ok=True)

    utc_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # === 1. UI_FREEZE_MANIFEST.json ===
    manifest = {
        "ui_version": "1.0.0",
        "status": "FROZEN",
        "freeze_date": utc_now,
        "branch": "release/ui-v1",
        "tag": "ui-freeze",
        "certified_modules": [
            "UI-1",
            "UI-2",
            "UI-3",
            "UI-3.1",
            "UI-4",
            "UI-5",
            "UI-6",
            "UI-7",
            "UI-8",
            "UI-9"
        ]
    }

    with open(baseline_dir / "UI_FREEZE_MANIFEST.json", "w") as f:
        json.dump(manifest, f, indent=2)
    print("[OK] Created baseline/ui-freeze/UI_FREEZE_MANIFEST.json")

    # === 2. UI_METRICS.json ===
    metrics = {
        "version": "1.0.0",
        "freeze_date": utc_now,
        "total_ui_files": total_ui_files,
        "total_ui_tests": total_ui_tests,
        "coverage_pct": coverage_pct,
        "ruff_issues": ruff_issues if ruff_rc != 0 else 0,
        "ruff_status": "PASS" if ruff_rc == 0 else "FAIL",
        "flake8_issues": flake8_issues,
        "flake8_status": "PASS" if flake8_rc == 0 else "FAIL",
        "mypy_issues": mypy_issues,
        "mypy_status": "PASS" if mypy_rc == 0 else "FAIL",
        "pytest_passed": passed,
        "pytest_failed": failed,
        "pytest_skipped": skipped,
        "pytest_warnings": warnings,
        "pytest_status": "PASS" if failed == 0 else "FAIL",
        "total_violations": len(violations),
        "boundary_status": "PASS" if not violations else "FAIL",
        "adapter_core_references": len(adapter_core_refs)
    }

    with open(baseline_dir / "UI_METRICS.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print("[OK] Created baseline/ui-freeze/UI_METRICS.json")

    # === 3. UI_COMPONENT_INVENTORY.json ===
    inventory = {
        "version": "1.0.0",
        "freeze_date": utc_now,
        "categories": {
            "Pages": {
                "count": pages_count,
                "files": sorted([f"ui/pages/{p.name}" for p in pages_files if p.name != "__init__.py"])
            },
            "Widgets": {
                "count": widgets_count,
                "files": sorted([f"ui/widgets/{p.name}" for p in widgets_files if p.name != "__init__.py"])
            },
            "Services": {
                "count": services_count,
                "files": sorted([f"ui/services/{p.name}" for p in services_files if p.name != "__init__.py"])
            },
            "Adapters": {
                "count": adapters_count,
                "files": sorted([f"ui/adapters/{p.name}" for p in adapters_files if p.name not in ("__init__.py", "_helpers.py")])
            },
            "DTOs": {
                "count": models_dto_count,
                "files": sorted([f"ui/models/{p.name}" for p in models_files if p.name != "__init__.py"])
            },
            "Events": {
                "count": events_count,
                "files": []
            },
            "RootUI": {
                "count": root_ui_count,
                "files": sorted([f"ui/{p.name}" for p in root_ui_files if p.name != "__init__.py"])
            },
            "Plugins": {
                "count": plugins_count,
                "files": sorted([f"ui/plugins/{p.name}" for p in plugins_files if p.name != "__init__.py"])
            }
        }
    }

    with open(baseline_dir / "UI_COMPONENT_INVENTORY.json", "w") as f:
        json.dump(inventory, f, indent=2)
    print("[OK] Created baseline/ui-freeze/UI_COMPONENT_INVENTORY.json")

    # === 4. UI_ARCHITECTURE_SNAPSHOT.md ===
    arch_content = f"""# UI Architecture Snapshot (Frozen)

## Architecture

```
UI Pages
  |
  v
Services
  |
  v
Adapters
  |
  v
Frozen Core
```

## Page Modules

| Page | File | Status |
|------|------|--------|
| Dashboard | `ui/pages/dashboard_page.py` | FROZEN |
| World Studio | `ui/pages/world_page.py` | FROZEN |
| Critic Studio | `ui/pages/critic_page.py` | FROZEN |
| Knowledge Explorer | `ui/pages/knowledge_page.py` | FROZEN |
| Autonomous Designer Workspace | `ui/pages/autonomous_page.py` | FROZEN |
| Settings | `ui/pages/settings_page.py` | FROZEN |
| Campaign | `ui/pages/campaign_page.py` | FROZEN |
| OTBM | `ui/pages/otbm_page.py` | FROZEN |
| Architect | `ui/pages/architect_page.py` | FROZEN |

## Service Layer

| Service | File |
|---------|------|
| Base Service | `ui/services/base_service.py` |
| Dashboard Service | `ui/services/dashboard_service.py` |
| World Service | `ui/services/world_service.py` |
| Critic Service | `ui/services/critic_service.py` |
| Knowledge Service | `ui/services/knowledge_service.py` |
| Autonomous Service | `ui/services/autonomous_service.py` |
| Campaign Service | `ui/services/campaign_service.py` |
| OTBM Service | `ui/services/otbm_service.py` |
| Service Container | `ui/services/service_container.py` |
| Service Registry | `ui/services/service_registry.py` |
| Null Services | `ui/services/null_services.py` |
| Service Exceptions | `ui/services/service_exceptions.py` |
| Dashboard Data Provider | `ui/services/dashboard_data_provider.py` |

## Adapters (Only layer allowed to reference core)

| Adapter | File |
|---------|------|
| Dashboard Adapter | `ui/adapters/dashboard_adapter.py` |
| World Adapter | `ui/adapters/world_adapter.py` |
| Critic Adapter | `ui/adapters/critic_adapter.py` |
| Knowledge Adapter | `ui/adapters/knowledge_adapter.py` |
| Autonomous Adapter | `ui/adapters/autonomous_adapter.py` |
| Campaign Adapter | `ui/adapters/campaign_adapter.py` |
| OTBM Adapter | `ui/adapters/otbm_adapter.py` |
| Helpers | `ui/adapters/_helpers.py` |

## DTO Layer

| DTO | File |
|-----|------|
| Dashboard DTO | `ui/models/dashboard_dto.py` |
| World DTO | `ui/models/world_dto.py` |
| Critic DTO | `ui/models/critic_dto.py` |
| Knowledge DTO | `ui/models/knowledge_dto.py` |
| Autonomous DTO | `ui/models/autonomous_dto.py` |
| Campaign DTO | `ui/models/campaign_dto.py` |
| OTBM DTO | `ui/models/otbm_dto.py` |

## Certified Modules

- UI-1: Foundation
- UI-2: Application Shell
- UI-3: Dashboard
- UI-3.1: Dashboard Hardening
- UI-4: Service Layer
- UI-5: Core Adapters
- UI-6: World Generation Studio
- UI-7: Visual Critic Studio
- UI-8: Knowledge Explorer
- UI-9: Autonomous Designer Workspace

## Application Shell Components

| Component | File |
|-----------|------|
| Main Window | `ui/main_window.py` |
| Sidebar | `ui/sidebar.py` |
| Status Bar | `ui/statusbar.py` |
| Title Bar | `ui/titlebar.py` |
| Navigation | `ui/navigation.py` |
| Page Registry | `ui/page_registry.py` |
| Event Bus | `ui/event_bus.py` |
| Theme | `ui/theme.py` |
| Console | `ui/console.py` |

## Frozen Files

Total UI Python files: **{total_ui_files}**
Total UI tests: **{total_ui_tests}**
"""

    with open(baseline_dir / "UI_ARCHITECTURE_SNAPSHOT.md", "w") as f:
        f.write(arch_content)
    print("[OK] Created baseline/ui-freeze/UI_ARCHITECTURE_SNAPSHOT.md")

    # Determine status string
    all_gates_pass = (failed == 0 and not violations and ruff_rc == 0 and flake8_rc == 0 and mypy_rc == 0)
    freeze_status_str = "CERTIFIED" if all_gates_pass else "NOT CERTIFIED"

    # === 5. UI_FREEZE_REPORT.md ===
    report = f"""# UI Freeze Report

## Summary

- **Project:** Agente RME v1.0.0 GA
- **Freeze Status:** {freeze_status_str}
- **Freeze Date:** {utc_now}
- **Branch:** release/ui-v1
- **Tag:** ui-freeze

## Certified Modules

| Module | Description | Status |
|--------|-------------|--------|
| UI-1 | Foundation | FROZEN |
| UI-2 | Application Shell | FROZEN |
| UI-3 | Dashboard | FROZEN |
| UI-3.1 | Dashboard Hardening | FROZEN |
| UI-4 | Service Layer | FROZEN |
| UI-5 | Core Adapters | FROZEN |
| UI-6 | World Generation Studio | FROZEN |
| UI-7 | Visual Critic Studio | FROZEN |
| UI-8 | Knowledge Explorer | FROZEN |
| UI-9 | Autonomous Designer Workspace | FROZEN |

## Files Counted

| Category | Count |
|----------|-------|
| Pages | {pages_count} |
| Widgets | {widgets_count} |
| Services | {services_count} |
| Adapters | {adapters_count} |
| DTOs (Models) | {models_dto_count} |
| Plugins | {plugins_count} |
| Root UI Shell | {root_ui_count} |
| **Total UI Files** | **{total_ui_files}** |

## Tests Counted

| Metric | Value |
|--------|-------|
| UI Test Files | {total_ui_tests} |
| Tests Passed | {passed} |
| Tests Failed | {failed} |
| Tests Skipped | {skipped} |

## Quality Gates

| Gate | Result |
|------|--------|
| ruff | {'PASS' if ruff_rc == 0 else f'FAIL ({ruff_issues} issues)'} |
| flake8 | {'PASS' if flake8_rc == 0 else f'FAIL ({flake8_issues} issues)'} |
| mypy | {'PASS' if mypy_rc == 0 else f'FAIL ({mypy_issues} issues)'} |
| pytest | {'PASS' if failed == 0 else f'FAIL ({failed} failures)'} |
| Boundary Scan | {'PASS' if not violations else f'FAIL ({len(violations)} violations)'} |
| Coverage | {coverage_pct:.1f}% |

## Architecture Summary

```
UI Pages --> Services --> Adapters --> Frozen Core
```

- **Pages layer** provides user-facing views
- **Services layer** orchestrates business logic
- **Adapters layer** is the ONLY layer allowed to reference `core.*` and `agents.*`
- **DTOs** transfer data between layers

## Freeze Scope

The following are locked under this freeze:

1. All 9 UI pages (Dashboard, World, Critic, Knowledge, Autonomous, Settings, Campaign, OTBM, Architect)
2. All widgets (critic, knowledge, autonomous, generation, dashboard widgets)
3. All services (dashboard, world, critic, knowledge, autonomous, campaign, otbm)
4. All adapters (dashboard, world, critic, knowledge, autonomous, campaign, otbm) - only core interface
5. All DTOs
6. Application shell (main window, sidebar, statusbar, navigation, event bus, theme)
7. Console

## Freeze Restrictions

### ALLOWED
- Crash fixes
- Security fixes
- Memory leak fixes
- UI-10 certification fixes

### NOT ALLOWED
- New widgets
- New pages
- New services
- New adapters
- Redesigns
- Architecture changes
"""

    with open(baseline_dir / "UI_FREEZE_REPORT.md", "w") as f:
        f.write(report)
    print("[OK] Created baseline/ui-freeze/UI_FREEZE_REPORT.md")

    # === SUMMARY ===
    print("\n" + "=" * 60)
    print("FREEZE CERTIFICATION SUMMARY")
    print("=" * 60)
    print(f"  Total UI files:     {total_ui_files}")
    print(f"  Total UI tests:     {total_ui_tests}")
    print(f"  Tests passed:       {passed}")
    print(f"  Tests failed:       {failed}")
    print(f"  Tests skipped:      {skipped}")
    print(f"  Coverage:           {coverage_pct:.1f}%")
    print(f"  ruff:               {'PASS' if ruff_rc == 0 else 'FAIL'} ({ruff_issues})")
    print(f"  flake8:             {'PASS' if flake8_rc == 0 else 'FAIL'} ({flake8_issues})")
    print(f"  mypy:               {'PASS' if mypy_rc == 0 else 'FAIL'} ({mypy_issues})")
    print(f"  pytest:             {'PASS' if failed == 0 else 'FAIL'}")
    print(f"  Boundary scan:      {'PASS' if not violations else 'FAIL'}")
    print(f"  Adapter core refs:  {len(adapter_core_refs)}")
    print("")
    print(f"  FREEZE STATUS: {freeze_status_str}")
    print("=" * 60)

    return 0 if all_gates_pass else 1


if __name__ == "__main__":
    sys.exit(main())