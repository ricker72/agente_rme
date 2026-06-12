"""
All-in-one import validator. Writes its own module list, tests imports,
and saves results to dependency_import_report.json.
"""

import importlib
import json
import sys
from pathlib import Path
from io import StringIO

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Find all project modules
AUDIT_DIRS = ["core", "agents", "ui", "config", "installer", "tools"]
SKIP = {"audit_dependency_consistency.py", "setup_init.py", "audit_run_imports.py"}


def find_py():
    files = []
    for d in AUDIT_DIRS:
        p = ROOT / d
        if p.exists():
            for f in p.rglob("*.py"):
                if any(p2 in ("__pycache__",) or p2.startswith(".") for p2 in f.parts):
                    continue
                if f.name == "setup_init.py":
                    continue
                files.append(f)
    for f in ROOT.glob("*.py"):
        if f.name.startswith("_") and f.name != "__init__.py":
            continue
        if f.name in SKIP:
            continue
        if "-" in f.name or f.name == "nul)":
            continue
        files.append(f)
    return sorted(set(files))


def to_mod(path):
    rel = path.relative_to(ROOT)
    parts = list(rel.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = parts[-1].replace(".py", "")
    return ".".join(parts)


py_files = find_py()
module_names = [to_mod(f) for f in py_files]

results = []
for mod in module_names:
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = StringIO(), StringIO()
    try:
        importlib.import_module(mod)
        results.append({"module": mod, "status": "PASS", "error": None})
    except Exception as e:
        results.append({"module": mod, "status": "FAIL", "error": str(e)[:200]})
    finally:
        sys.stdout, sys.stderr = old_out, old_err

with open(ROOT / "dependency_import_report.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

passed = sum(1 for r in results if r["status"] == "PASS")
print(f"IMPORT_CHECK DONE {len(module_names)} {passed} {len(module_names) - passed}")
