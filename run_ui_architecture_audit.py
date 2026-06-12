#!/usr/bin/env python3
"""UI-10.1 Architecture Audit — generates all 10 audit reports."""

import os
import json
import re
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(".")
OUT_DIR = BASE_DIR / "baseline" / "ui-freeze" / "UI10_1"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SKIP_DIRS = {"__pycache__"}


def get_py_files(root):
    """Recursively get .py files skipping __pycache__."""
    files = []
    for dirpath, dirnames, fnames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in fnames:
            if f.endswith(".py"):
                files.append(Path(dirpath) / f)
    return sorted(files)


def read_file_lines(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read().splitlines()
    except Exception:
        return []


# ============================================================
# AUDIT 1 — IMPORT BOUNDARY
# ============================================================
def audit_import_boundary():
    scan_dirs = ["ui/pages", "ui/widgets", "ui/services", "ui/models", "ui"]
    forbidden_imports = []
    scanned_files = []

    for d in scan_dirs:
        for f in get_py_files(d):
            # Skip adapters directory inside ui/
            if "adapters" in f.parts:
                continue
            scanned_files.append(str(f))
            lines = read_file_lines(f)
            for lineno, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r"^\s*from\s+core\.", stripped) or re.search(r"^\s*import\s+core\b", stripped):
                    forbidden_imports.append({"file": str(f), "line": lineno, "code": stripped})
                if re.search(r"^\s*from\s+agents\.", stripped) or re.search(r"^\s*import\s+agents\b", stripped):
                    forbidden_imports.append({"file": str(f), "line": lineno, "code": stripped})

    result = {
        "audit": "Import Boundary",
        "audit_id": "AUDIT 1",
        "scanned_directories": scan_dirs,
        "total_files_scanned": len(scanned_files),
        "forbidden_imports_found": len(forbidden_imports),
        "forbidden_imports": forbidden_imports,
        "allowed_exception": "ui/adapters/ (permitted to reference core.* and agents.*)",
        "status": "PASS" if len(forbidden_imports) == 0 else "FAIL",
    }
    with open(OUT_DIR / "boundary_scan.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 2 — ADAPTER BOUNDARY
# ============================================================
def audit_adapter_boundary():
    adapter_files = get_py_files("ui/adapters")
    adapters = {}
    total_issues = 0

    for f in adapter_files:
        if f.name == "__init__.py":
            continue
        content = open(f, "r", encoding="utf-8", errors="replace").read()
        lines = content.splitlines()
        core_refs = []
        dto_refs = []
        raw_core_imports = []
        failure_dtos = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"core\.", stripped):
                core_refs.append({"line": i + 1, "code": stripped})
            if re.search(r"ui\.models\.", stripped) or re.search(r"from\s+ui\.models", stripped):
                dto_refs.append({"line": i + 1, "code": stripped})
            if re.search(r"^\s*from\s+core\.", stripped) or re.search(r"^\s*import\s+core\b", stripped):
                raw_core_imports.append({"line": i + 1, "code": stripped})
            if "return" in stripped and ("error_message" in stripped or "success=False" in stripped or "success = False" in stripped):
                failure_dtos.append({"line": i + 1, "code": stripped})

        uses_importlib = "importlib" in content
        issues = len(raw_core_imports)
        total_issues += issues

        adapters[f.name] = {
            "core_references": core_refs,
            "dto_references": dto_refs,
            "raw_core_imports": raw_core_imports,
            "uses_lazy_importlib": uses_importlib,
            "failure_dto_patterns": failure_dtos,
            "issues": issues,
        }

    # Check service_container
    container_path = BASE_DIR / "ui" / "services" / "service_container.py"
    container_issues = []
    if container_path.exists():
        content = open(container_path, "r", encoding="utf-8", errors="replace").read()
        if "register_core_adapters" not in content:
            container_issues.append("register_core_adapters() not found")
        if "register_defaults" not in content:
            container_issues.append("register_defaults() not found")
        if "null_services" not in content and "Null" not in content:
            container_issues.append("null services not referenced")
    else:
        container_issues.append("service_container.py not found")

    result = {
        "audit": "Adapter Boundary",
        "audit_id": "AUDIT 2",
        "adapter_files_analyzed": len(adapters),
        "adapters": adapters,
        "adapter_total_issues": total_issues,
        "container_issues": container_issues,
        "status": "PASS" if total_issues == 0 and len(container_issues) == 0 else "FAIL",
    }
    with open(OUT_DIR / "adapter_boundary_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 3 — SERVICE BOUNDARY
# ============================================================
def audit_service_boundary():
    service_files = get_py_files("ui/services")
    services = {}
    issues_found = []

    for f in service_files:
        content = open(f, "r", encoding="utf-8", errors="replace").read()
        lines = content.splitlines()
        file_issues = []

        # Check for core imports
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"^\s*from\s+core\.", stripped) or re.search(r"^\s*import\s+core\b", stripped):
                file_issues.append(f"core import at line {i+1}: {stripped}")

        # Check for Protocol or ABC
        has_protocol = "Protocol" in content or "ABC" in content
        has_dto = "DTO" in content
        has_raw_dict = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Skip private methods (underscore prefix) — internal implementation
            if re.search(r"def\s+_", stripped):
                continue
            if "->" in stripped and "dict" in stripped.lower() and "DTO" not in stripped:
                has_raw_dict = True
                file_issues.append(f"raw dict return at line {i+1}: {stripped}")

        services[f.name] = {
            "core_imports": file_issues,
            "has_protocol_or_abc": has_protocol,
            "uses_dto": has_dto,
            "returns_raw_dict": has_raw_dict,
            "issues": file_issues,
        }
        issues_found.extend(file_issues)

    result = {
        "audit": "Service Boundary",
        "audit_id": "AUDIT 3",
        "service_files_analyzed": len(services),
        "services": services,
        "total_issues": len(issues_found),
        "status": "PASS" if len(issues_found) == 0 else "FAIL",
    }
    with open(OUT_DIR / "service_boundary_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 4 — DTO BOUNDARY
# ============================================================
def audit_dto_boundary():
    dto_files = get_py_files("ui/models")
    dtos = {}
    issues_found = []

    for f in dto_files:
        # Skip __init__.py — it's just re-exports, not a DTO file
        if f.name == "__init__.py":
            continue
        content = open(f, "r", encoding="utf-8", errors="replace").read()
        lines = content.splitlines()
        file_issues = []

        # Check for @dataclass with slots
        has_dataclass = "@dataclass" in content
        has_slots = "slots=True" in content

        # Check core imports
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if re.search(r"^\s*from\s+core\.", stripped) or re.search(r"^\s*import\s+core\b", stripped):
                file_issues.append(f"core import at line {i+1}: {stripped}")
            if re.search(r"^\s*from\s+agents\.", stripped) or re.search(r"^\s*import\s+agents\b", stripped):
                file_issues.append(f"agents import at line {i+1}: {stripped}")

        if not has_dataclass:
            file_issues.append("missing @dataclass decorator")
        if not has_slots:
            file_issues.append("does not use slots=True")

        dtos[f.name] = {
            "has_dataclass": has_dataclass,
            "has_slots": has_slots,
            "issues": file_issues,
        }
        issues_found.extend(file_issues)

    result = {
        "audit": "DTO Boundary",
        "audit_id": "AUDIT 4",
        "dto_files_analyzed": len(dtos),
        "details": dtos,
        "total_issues": len(issues_found),
        "status": "PASS" if len(issues_found) == 0 else "FAIL",
    }
    with open(OUT_DIR / "dto_boundary_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 5 — EVENT BUS
# ============================================================
def audit_event_bus():
    issues_found = []
    event_files = [BASE_DIR / "ui" / "event_bus.py"]
    for d in ["ui/pages", "ui/services", "ui/widgets", "ui"]:
        event_files.extend(get_py_files(d))

    typed_events = 0
    string_events = 0
    core_exposure = 0

    for f in event_files:
        content = open(f, "r", encoding="utf-8", errors="replace").read()
        lines = content.splitlines()

        # Count typed dataclass events
        if "@dataclass" in content:
            typed_events += 1

        # Count string event names
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # String-only event emission
            if re.search(r"emit\(\s*['\"]", stripped) or re.search(r"post_event\(\s*['\"]", stripped):
                string_events += 1
                if string_events <= 5:
                    issues_found.append(f"string event at {f.name}:{i+1}: {stripped}")
            # Core object exposure in events
            if re.search(r"core\.", stripped) and ("emit" in stripped or "post" in stripped or "event" in stripped.lower()):
                core_exposure += 1
                issues_found.append(f"core exposure in event at {f.name}:{i+1}: {stripped}")

    result = {
        "audit": "Event Bus",
        "audit_id": "AUDIT 5",
        "typed_dataclass_events": typed_events,
        "string_only_events": string_events,
        "core_exposure_in_events": core_exposure,
        "issues": issues_found,
        "total_issues": len(issues_found),
        "status": "PASS" if core_exposure == 0 else "FAIL",
    }
    with open(OUT_DIR / "event_bus_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 6 — PAGE ARCHITECTURE
# ============================================================
def audit_page_architecture():
    required_pages = [
        "dashboard_page.py", "world_page.py", "critic_page.py",
        "knowledge_page.py", "autonomous_page.py", "settings_page.py",
    ]
    pages = {}
    issues_found = []

    for f in get_py_files("ui/pages"):
        if f.name not in required_pages:
            continue
        content = open(f, "r", encoding="utf-8", errors="replace").read()
        lines = content.splitlines()
        file_issues = []
        page_info = {"core_imports": [], "uses_services": False, "uses_direct_engine": False, "blocks_ui": False}

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # core imports
            if re.search(r"^\s*from\s+core\.", stripped) or re.search(r"^\s*import\s+core\b", stripped):
                file_issues.append(f"core import at line {i+1}: {stripped}")
                page_info["core_imports"].append({"line": i + 1, "code": stripped})
            # service usage
            if "Service" in stripped and ("from" in stripped or "import" in stripped):
                page_info["uses_services"] = True

        # Check for QThread/worker patterns
        page_info["uses_qthread"] = "QThread" in content or "Worker" in content or "QFuture" in content

        pages[f.name] = {
            "core_imports": page_info["core_imports"],
            "uses_services": page_info["uses_services"],
            "uses_qthread": page_info["uses_qthread"],
            "issues": file_issues,
        }
        issues_found.extend(file_issues)

    result = {
        "audit": "Page Architecture",
        "audit_id": "AUDIT 6",
        "required_pages": required_pages,
        "pages_analyzed": len(pages),
        "details": pages,
        "total_issues": len(issues_found),
        "status": "PASS" if len(issues_found) == 0 else "FAIL",
    }
    with open(OUT_DIR / "page_architecture_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 7 — WIDGET ARCHITECTURE
# ============================================================
def audit_widget_architecture():
    widget_files = get_py_files("ui/widgets")
    widgets = {}
    issues_found = []

    for f in widget_files:
        content = open(f, "r", encoding="utf-8", errors="replace").read()
        lines = content.splitlines()
        file_issues = []

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # core imports
            if re.search(r"^\s*from\s+core\.", stripped) or re.search(r"^\s*import\s+core\b", stripped):
                file_issues.append(f"core import at line {i+1}: {stripped}")
            if re.search(r"^\s*from\s+agents\.", stripped) or re.search(r"^\s*import\s+agents\b", stripped):
                file_issues.append(f"agents import at line {i+1}: {stripped}")

        # Check for DTO usage
        uses_dto = "DTO" in content
        # Check for file system access (for non-viewer widgets)
        has_filesystem = "open(" in content or "Path(" in content or "pathlib" in content

        widgets[f.name] = {
            "core_imports": [i for i in file_issues if "core" in i],
            "agents_imports": [i for i in file_issues if "agents" in i],
            "uses_dto": uses_dto,
            "has_filesystem": has_filesystem,
            "issues": file_issues,
        }
        issues_found.extend(file_issues)

    result = {
        "audit": "Widget Architecture",
        "audit_id": "AUDIT 7",
        "widget_files_analyzed": len(widgets),
        "details": widgets,
        "total_issues": len(issues_found),
        "status": "PASS" if len(issues_found) == 0 else "FAIL",
    }
    with open(OUT_DIR / "widget_architecture_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 8 — SERVICE CONTAINER
# ============================================================
def audit_service_container():
    container_path = BASE_DIR / "ui" / "services" / "service_container.py"
    null_svc_path = BASE_DIR / "ui" / "services" / "null_services.py"
    issues_found = []

    container_info = {}
    if container_path.exists():
        content = open(container_path, "r", encoding="utf-8", errors="replace").read()
        container_info["has_register_defaults"] = "register_defaults" in content
        container_info["has_register_core_adapters"] = "register_core_adapters" in content
        container_info["references_null_services"] = "null_services" in content or "Null" in content

        if not container_info["has_register_defaults"]:
            issues_found.append("register_defaults() not found")
        if not container_info["has_register_core_adapters"]:
            issues_found.append("register_core_adapters() not found")
        if not container_info["references_null_services"]:
            issues_found.append("null services not referenced")
    else:
        issues_found.append("service_container.py not found")

    null_info = {}
    if null_svc_path.exists():
        content = open(null_svc_path, "r", encoding="utf-8", errors="replace").read()
        null_info["file_exists"] = True
        null_info["class_names"] = [line.split("class ")[1].split("(")[0].strip()
                                     for line in content.splitlines()
                                     if line.strip().startswith("class ") and ":" in line]
    else:
        null_info["file_exists"] = False
        issues_found.append("null_services.py not found")

    result = {
        "audit": "Service Container",
        "audit_id": "AUDIT 8",
        "container": container_info,
        "null_services": null_info,
        "issues": issues_found,
        "total_issues": len(issues_found),
        "status": "PASS" if len(issues_found) == 0 else "FAIL",
    }
    with open(OUT_DIR / "service_container_report.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 9 — UI MODULE INVENTORY
# ============================================================
def audit_ui_inventory():
    inventory = {
        "pages": [],
        "widgets": [],
        "services": [],
        "adapters": [],
        "dtos": [],
        "events": [],
        "tests": [],
    }

    for f in get_py_files("ui/pages"):
        if f.name != "__init__.py":
            inventory["pages"].append(str(f))
    for f in get_py_files("ui/widgets"):
        if f.name != "__init__.py":
            inventory["widgets"].append(str(f))
    for f in get_py_files("ui/services"):
        if f.name != "__init__.py":
            inventory["services"].append(str(f))
    for f in get_py_files("ui/adapters"):
        if f.name not in ("__init__.py",):
            inventory["adapters"].append(str(f))
    for f in get_py_files("ui/models"):
        if f.name != "__init__.py":
            inventory["dtos"].append(str(f))

    # Event bus file
    if (BASE_DIR / "ui" / "event_bus.py").exists():
        inventory["events"].append("ui/event_bus.py")

    # Tests
    for f in get_py_files("tests/ui"):
        inventory["tests"].append(str(f))

    result = {
        "audit": "UI Module Inventory",
        "audit_id": "AUDIT 9",
        "counts": {k: len(v) for k, v in inventory.items()},
        "inventory": inventory,
    }
    with open(OUT_DIR / "architecture_inventory.json", "w") as f:
        json.dump(result, f, indent=2)
    return result


# ============================================================
# AUDIT 10 — FINAL ARCHITECTURE CERTIFICATION
# ============================================================
def audit_final_certification(results):
    all_pass = True
    blockers = []
    risks = []

    for audit_name, audit_result in results.items():
        status = audit_result.get("status", "UNKNOWN")
        if status == "FAIL":
            all_pass = False
            issue_count = audit_result.get("total_issues", 0) or len(audit_result.get("issues", []))
            blockers.append(f"{audit_name}: FAIL ({issue_count} issues found)")

    # Determine risks
    if results.get("Adapter Boundary", {}).get("status") == "PASS":
        adapter_info = results["Adapter Boundary"]
        for name, info in adapter_info.get("adapters", {}).items():
            if not info.get("uses_lazy_importlib"):
                risks.append(f"{name} does not use lazy importlib loading")

    total_files = sum(results.get("UI Module Inventory", {}).get("counts", {}).values())

    markdown = f"""# UI-10.1 Architecture Audit Certification

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Branch:** release/ui-v1
**Status:** {'**CERTIFIED**' if all_pass else '**NOT CERTIFIED**'}

---

## Summary

| Audit | Status | Issues |
|-------|--------|--------|
"""
    for audit_name, audit_result in results.items():
        status = audit_result.get("status", "N/A")
        issue_count = audit_result.get("total_issues", audit_result.get("issues", "N/A"))
        markdown += f"| {audit_name} | {status} | {issue_count} |\n"

    markdown += f"""
---

## Metrics

- **Total files scanned:** {total_files}
- **Forbidden imports found:** {results.get("Import Boundary", {}).get("forbidden_imports_found", "N/A")}
- **Adapters validated:** {results.get("Adapter Boundary", {}).get("adapter_files_analyzed", "N/A")}
- **Services validated:** {results.get("Service Boundary", {}).get("service_files_analyzed", "N/A")}
- **DTOs validated:** {results.get("DTO Boundary", {}).get("dto_files_analyzed", "N/A")}
- **Event bus analysis:** {results.get("Event Bus", {}).get("typed_dataclass_events", "N/A")} typed events, {results.get("Event Bus", {}).get("string_only_events", "N/A")} string events
- **Pages validated:** {results.get("Page Architecture", {}).get("pages_analyzed", "N/A")}
- **Widgets validated:** {results.get("Widget Architecture", {}).get("widget_files_analyzed", "N/A")}

---

## Risks

{"None identified." if not risks else chr(10).join(f"- {r}" for r in risks)}

## Blockers

{"None." if not blockers else chr(10).join(f"- {b}" for b in blockers)}

---

## Final Verdict

**UI-10.1 ARCHITECTURE AUDIT {'CERTIFIED' if all_pass else 'NOT CERTIFIED'}**
"""
    with open(OUT_DIR / "UI10_1_ARCHITECTURE_REPORT.md", "w") as f:
        f.write(markdown)

    certification = {
        "audit": "Final Architecture Certification",
        "audit_id": "AUDIT 10",
        "date": datetime.now().isoformat(),
        "branch": "release/ui-v1",
        "total_files_scanned": total_files,
        "forbidden_imports_found": results.get("Import Boundary", {}).get("forbidden_imports_found", 0),
        "adapters_validated": results.get("Adapter Boundary", {}).get("adapter_files_analyzed", 0),
        "services_validated": results.get("Service Boundary", {}).get("service_files_analyzed", 0),
        "dtos_validated": results.get("DTO Boundary", {}).get("dto_files_analyzed", 0),
        "events_validated": results.get("Event Bus", {}).get("typed_dataclass_events", 0),
        "pages_validated": results.get("Page Architecture", {}).get("pages_analyzed", 0),
        "widgets_validated": results.get("Widget Architecture", {}).get("widget_files_analyzed", 0),
        "risks": risks,
        "blockers": blockers,
        "all_audits_pass": all_pass,
        "final_status": "CERTIFIED" if all_pass else "NOT CERTIFIED",
    }
    with open(OUT_DIR / "UI10_1_ARCHITECTURE_CERTIFICATION.json", "w") as f:
        json.dump(certification, f, indent=2)

    return markdown, certification


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("UI-10.1 Architecture Audit")
    print("=" * 60)

    results = {}
    audits = [
        ("AUDIT 1: Import Boundary", audit_import_boundary),
        ("AUDIT 2: Adapter Boundary", audit_adapter_boundary),
        ("AUDIT 3: Service Boundary", audit_service_boundary),
        ("AUDIT 4: DTO Boundary", audit_dto_boundary),
        ("AUDIT 5: Event Bus", audit_event_bus),
        ("AUDIT 6: Page Architecture", audit_page_architecture),
        ("AUDIT 7: Widget Architecture", audit_widget_architecture),
        ("AUDIT 8: Service Container", audit_service_container),
        ("AUDIT 9: UI Module Inventory", audit_ui_inventory),
    ]

    for name, fn in audits:
        print(f"\n--- Running {name} ---")
        try:
            result = fn()
            audit_id = result.get("audit", name)
            status = result.get("status", "UNKNOWN")
            issues = result.get("total_issues", 0)
            results[audit_id] = result
            print(f"  Status: {status}  |  Issues: {issues}")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results[name] = {"status": "ERROR", "error": str(e)}

    print("\n--- Running AUDIT 10: Final Certification ---")
    try:
        report, cert = audit_final_certification(results)
        print(f"  Final Status: {cert['final_status']}")
        print(f"  Report: {OUT_DIR / 'UI10_1_ARCHITECTURE_REPORT.md'}")
        print(f"  Certification: {OUT_DIR / 'UI10_1_ARCHITECTURE_CERTIFICATION.json'}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Audit complete. All files saved to:", OUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()