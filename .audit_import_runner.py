"""
Import validation runner - checks if project modules can be imported.
Results are written to .audit_import_results.json
Captures stdout to avoid side effects.
"""

import importlib
import json
import os
import sys
from io import StringIO

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

modules_file = os.path.join(ROOT, ".audit_module_list.txt")
results_file = os.path.join(ROOT, ".audit_import_results.json")

with open(modules_file, "r") as f:
    module_names = [line.strip() for line in f if line.strip()]

results = []
for mod in module_names:
    # Capture stdout to prevent side effects from module imports
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StringIO()
    sys.stderr = StringIO()
    try:
        importlib.import_module(mod)
        results.append({"module": mod, "status": "PASS", "error": None})
    except Exception as e:
        err = str(e)[:200]
        results.append({"module": mod, "status": "FAIL", "error": err})
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

with open(results_file, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

n_pass = sum(1 for r in results if r["status"] == "PASS")
n_fail = sum(1 for r in results if r["status"] == "FAIL")
print(
    f"CHECKED {len(module_names)} PASS {n_pass} FAIL {n_fail}"
)
