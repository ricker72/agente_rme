"""
check_utcnow.py — Pre-commit / CI lint rule

Fails if any production .py file contains ``datetime.utcnow()`` or the literal
``utcnow`` (with a few allowed exceptions for migration scripts and test files).

Exit codes:
    0 — no violations found
    1 — violations found

Usage:
    python check_utcnow.py                # check whole repo
    python check_utcnow.py path/to/file   # check single file
"""

import os
import sys

# Files allowed to mention "utcnow" (migration/diagnostic scripts)
ALLOWED_FILES = {
    "check_utcnow.py",
    "fix_utcnow.py",
    "test_utcnow.py",
    "validate_hito_26_1e.py",
    "_quality_report.py",
    "audit_dependency_consistency.py",
}

EXCLUDE_DIRS = {".venv", "__pycache__", ".git", "node_modules", "logs", "tests"}


def check_file(path: str) -> list:
    """Return list of (line_number, line_content) for lines containing 'utcnow'."""
    offenders = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh, 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if "utcnow" in line:
                    offenders.append((i, line.rstrip()))
    except Exception:
        pass
    return offenders


def walk_repo(root: str = ".") -> list:
    """Walk the repository and return (path, [(line, content), ...]) pairs."""
    results = []
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(r, f)
                basename = os.path.basename(path)
                if basename in ALLOWED_FILES:
                    continue
                offenders = check_file(path)
                if offenders:
                    results.append((path, offenders))
    return results


def main():
    if len(sys.argv) > 1:
        # Single file mode
        path = sys.argv[1]
        offenders = check_file(path)
        if offenders:
            for lineno, line in offenders:
                print(f"{path}:{lineno}: {line}")
            print(f"\nFAIL: {path} contains datetime.utcnow() references.")
            sys.exit(1)
        print(f"OK: {path} -- clean")
        sys.exit(0)

    # Full repo mode
    results = walk_repo()
    if results:
        for path, offenders in sorted(results):
            for lineno, line in offenders:
                print(f"{path}:{lineno}: {line}")
        total = sum(len(o) for _, o in results)
        print(
            f"\nFAIL: Found {total} datetime.utcnow() reference(s) in production code."
        )
        sys.exit(1)

    print("OK: No datetime.utcnow() found in production code.")
    sys.exit(0)


if __name__ == "__main__":
    main()
