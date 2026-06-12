"""Generate MyPy R2 triage JSON and MD from baseline output."""
import re
import json
from pathlib import Path

BASELINE = Path("output/certification/mypy_r2_baseline.txt")
TRIAGE_JSON = Path("output/certification/mypy_r2_triage.json")
TRIAGE_MD = Path("output/certification/mypy_r2_triage.md")

lines = BASELINE.read_text(encoding="utf-8").splitlines()

categories = {
    "missing_imports": [],
    "optional_none": [],
    "incompatible_assignment": [],
    "return_type_mismatch": [],
    "untyped_function": [],
    "any_leakage": [],
    "test_only": [],
    "generated_excluded": [],
}

error_count = 0
note_count = 0
summary_line = ""

# Error code -> category mapping
CODE_MAP = {
    "import-not-found": "missing_imports",
    "import-untyped": "missing_imports",
    "union-attr": "optional_none",
    "none-not-iterable": "optional_none",
    "assignment": "incompatible_assignment",
    "arg-type": "incompatible_assignment",
    "call-overload": "incompatible_assignment",
    "operator": "incompatible_assignment",
    "index": "incompatible_assignment",
    "list-item": "incompatible_assignment",
    "dict-item": "incompatible_assignment",
    "return-value": "return_type_mismatch",
    "var-annotated": "untyped_function",
    "annotation-unchecked": "untyped_function",
    "no-untyped-def": "untyped_function",
    "no-any-return": "any_leakage",
}

for line in lines:
    line = line.strip()
    if not line:
        continue
    if line.startswith("Found "):
        summary_line = line
        continue
    if ": note: " in line:
        note_count += 1
        continue
    if ": error: " not in line:
        continue

    error_count += 1

    # Get error code
    code_match = re.search(r"\[([a-z][a-z-]+)\]", line)
    code = code_match.group(1) if code_match else "unknown"

    # Determine location
    is_test = line.startswith("tests/") or line.startswith("tests\\")
    is_generated = any(
        x in line
        for x in [
            "output/",
            "output\\",
            "baseline/",
            "baseline\\",
            "htmlcov",
            "build/",
            "dist/",
            ".venv",
            "__pycache__",
        ]
    )

    if is_generated:
        cat = "generated_excluded"
    elif is_test:
        cat = "test_only"
    elif code in CODE_MAP:
        cat = CODE_MAP[code]
    else:
        # Fallback classification
        msg = line.split(": error: ")[1] if ": error: " in line else ""
        if any(w in msg.lower() for w in ["return", "got"]):
            cat = "return_type_mismatch"
        elif any(w in msg.lower() for w in ["argument", "incompatible", "no overload"]):
            cat = "incompatible_assignment"
        elif "any" in msg.lower():
            cat = "any_leakage"
        else:
            cat = "untyped_function"

    categories[cat].append({"line": line, "code": code})

# Build summary
triage_summary = {k: len(v) for k, v in categories.items()}
total_classified = sum(triage_summary.values())

# Write JSON
triage_json = {
    "baseline_file": str(BASELINE),
    "total_errors": error_count,
    "total_notes": note_count,
    "summary_line": summary_line,
    "categories": triage_summary,
    "details": categories,
}
TRIAGE_JSON.write_text(json.dumps(triage_json, indent=2, ensure_ascii=False), encoding="utf-8")

# Write MD
md_lines = [
    "# MyPy R2 Triage Report",
    "",
    f"**Baseline file:** `{BASELINE}`",
    f"**Total errors:** {error_count}",
    f"**Total notes:** {note_count}",
    f"**Summary:** {summary_line}",
    "",
    "## Category Breakdown",
    "",
    "| Category | Count | Description |",
    "|----------|-------|-------------|",
    f"| missing_imports | {triage_summary['missing_imports']} | Library stubs not installed or module not found |",
    f"| optional_none | {triage_summary['optional_none']} | Accessing attributes on Optional/None types |",
    f"| incompatible_assignment | {triage_summary['incompatible_assignment']} | Type mismatches in assignments, arguments, operators |",
    f"| return_type_mismatch | {triage_summary['return_type_mismatch']} | Incompatible return value types |",
    f"| untyped_function | {triage_summary['untyped_function']} | Missing type annotations |",
    f"| any_leakage | {triage_summary['any_leakage']} | Returning Any from typed functions |",
    f"| test_only | {triage_summary['test_only']} | Errors in test files (lower priority) |",
    f"| generated_excluded | {triage_summary['generated_excluded']} | Errors in generated/output artifacts |",
    "",
    "## Priority for Safe Fixes",
    "",
    "1. **UI errors** (ui/ and tests/ui/) — target: 0 errors",
    "2. **Critical core surface** (core/otbm, core/critic, core/knowledge, core/autonomous, core/blueprint_intelligence)",
    "3. **Missing imports** (install stubs where possible)",
    "4. **Untyped functions** (add annotations)",
    "5. **Any leakage** (narrow types)",
    "6. **Test-only errors** (add stubs for missing modules)",
    "",
]

# Add per-category error lists
for cat in [
    "test_only",
    "missing_imports",
    "optional_none",
    "incompatible_assignment",
    "return_type_mismatch",
    "untyped_function",
    "any_leakage",
    "generated_excluded",
]:
    items = categories[cat]
    md_lines.append(f"## {cat} ({len(items)} errors)")
    md_lines.append("")
    # Group by file
    files = {}
    for item in items:
        # Extract file path
        fp = item["line"].split(":")[0] if ":" in item["line"] else item["line"]
        files.setdefault(fp, []).append(item["line"])
    for fp, errs in sorted(files.items()):
        md_lines.append(f"### {fp}")
        md_lines.append("")
        for e in errs[:10]:  # limit per file
            md_lines.append(f"- `{e}`")
        if len(errs) > 10:
            md_lines.append(f"- ... and {len(errs) - 10} more")
        md_lines.append("")

TRIAGE_MD.write_text("\n".join(md_lines), encoding="utf-8")

# Print summary
print(f"Total errors: {error_count}")
print(f"Total notes: {note_count}")
print(f"Summary: {summary_line}")
print("Category breakdown:")
for k, v in triage_summary.items():
    print(f"  {k}: {v}")
print(f"\nJSON written to {TRIAGE_JSON}")
print(f"MD written to {TRIAGE_MD}")