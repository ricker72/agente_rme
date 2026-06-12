"""_quality_report.py — Generate quality_report.json for the GA release."""

import json
import re
import shlex
import subprocess
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _run(cmd):
    cmd_list = shlex.split(cmd) if isinstance(cmd, str) else cmd
    return subprocess.run(cmd_list, capture_output=True, text=True, shell=False)


def _try_tool(name, args):
    try:
        proc = _run(f"{name} {' '.join(args)}")
        return proc.returncode, proc.stdout, proc.stderr, True
    except Exception as e:
        return -1, "", str(e), False


def _scan_deprecated_apis(src: Path):
    deprecated = []
    _utc = "utcnow"
    patterns = {
        rf"\bdatetime\.{_utc}\(\)": f"datetime.{_utc}() — use datetime.now(timezone.utc)",
        r"\bos\.popen\b": "os.popen — use subprocess",
        r"\bimp\.find_module\b": "imp module — use importlib",
    }
    for py in src.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat, msg in patterns.items():
            for m in re.finditer(pat, text):
                line = text[: m.start()].count("\n") + 1
                deprecated.append({"file": str(py), "line": line, "issue": msg})
    return deprecated


def _scan_unused_imports(src: Path):
    issues = []
    for py in src.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in re.finditer(
            r"^\s*(?:from\s+([\w.]+)\s+import\s+([^\n]+)|import\s+([\w.]+))",
            text,
            re.MULTILINE,
        ):
            if m.group(1):
                names = [n.strip().split(" as ")[0] for n in m.group(2).split(",")]
                for n in names:
                    if n == "*":
                        continue
                    rest = text.replace(m.group(0), "", 1)
                    if re.search(rf"\b{re.escape(n)}\b", rest):
                        continue
                    issues.append(
                        {"file": str(py), "name": n, "kind": "possibly unused import"}
                    )
            elif m.group(3):
                n = m.group(3).split(".")[0]
                rest = text.replace(m.group(0), "", 1)
                if re.search(rf"\b{re.escape(n)}\b", rest):
                    continue
                issues.append(
                    {"file": str(py), "name": n, "kind": "possibly unused import"}
                )
    return issues[:50]


def _scan_legacy(src: Path):
    issues = []
    patterns = [r"\bTODO\b", r"\bFIXME\b", r"\bXXX\b", r"\bHACK\b"]
    for py in src.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for pat in patterns:
            for m in re.finditer(pat, text):
                line = text[: m.start()].count("\n") + 1
                issues.append({"file": str(py), "line": line, "marker": m.group(0)})
    return issues[:50]


def _scan_dead_code(src: Path):
    issues = []
    for py in src.rglob("*.py"):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if re.search(r"^\s*pass\s*$", text, re.MULTILINE) and py.name != "__init__.py":
            non_empty_lines = [
                l
                for l in text.splitlines()  # noqa: E741
                if l.strip() and not l.strip().startswith("#")
            ]
            if len(non_empty_lines) <= 1:
                issues.append({"file": str(py), "kind": "empty module"})
    return issues


def main():
    report = {
        "timestamp": _utc_iso(),
        "version": "Agente RME v1.0.0 GA",
        "scanners": {},
        "summary": {
            "critical_errors": 0,
            "warnings": 0,
            "deprecated_apis": 0,
            "unused_imports": 0,
            "legacy_markers": 0,
            "dead_code": 0,
        },
    }

    code, out, err, ok = _try_tool(
        "ruff",
        [
            "check",
            "core/",
            "cli.py",
            "rme.py",
            "ga_benchmark.py",
            "--statistics",
            "--quiet",
        ],
    )
    report["scanners"]["ruff"] = {
        "ran": ok,
        "exit_code": code,
        "summary": out.strip() if out else "",
    }

    code, out, err, ok = _try_tool(
        "flake8",
        [
            "--max-line-length=120",
            "core/",
            "cli.py",
            "rme.py",
            "ga_benchmark.py",
            "--count",
        ],
    )
    report["scanners"]["flake8"] = {
        "ran": ok,
        "exit_code": code,
        "summary": out.strip() if out else "",
    }

    code, out, err, ok = _try_tool(
        "mypy",
        [
            "--ignore-missing-imports",
            "core/",
            "cli.py",
            "rme.py",
            "ga_benchmark.py",
            "--no-error-summary",
        ],
    )
    report["scanners"]["mypy"] = {
        "ran": ok,
        "exit_code": code,
        "summary": out.strip()[:500] if out else "",
    }

    code, out, err, ok = _try_tool("bandit", ["-r", "core/", "-f", "json", "-q"])
    bandit_summary = ""
    bandit_issues = 0
    if ok and out.strip():
        try:
            bd = json.loads(out)
            bandit_issues = len(bd.get("results", []))
            bandit_summary = f"{bd.get('metrics', {}).get('_totals', {}).get('loc', 0)} LOC, {bandit_issues} issues"
        except Exception:
            bandit_summary = out[:200]
    report["scanners"]["bandit"] = {
        "ran": ok,
        "exit_code": code,
        "issues": bandit_issues,
        "summary": bandit_summary,
    }

    core_path = PROJECT_ROOT / "core"
    deprecated = _scan_deprecated_apis(core_path)
    unused = _scan_unused_imports(core_path)
    legacy = _scan_legacy(core_path)
    dead = _scan_dead_code(core_path)

    report["heuristic"] = {
        "deprecated_apis": deprecated,
        "unused_imports": unused,
        "legacy_markers": legacy,
        "dead_code": dead,
    }
    report["summary"]["deprecated_apis"] = len(deprecated)
    report["summary"]["unused_imports"] = len(unused)
    report["summary"]["legacy_markers"] = len(legacy)
    report["summary"]["dead_code"] = len(dead)

    critical = 0
    if ok and out.strip():
        try:
            bd = json.loads(out)
            critical = sum(
                1 for r in bd.get("results", []) if r.get("issue_severity") == "HIGH"
            )
        except Exception:
            pass
    report["summary"]["critical_errors"] = critical
    report["summary"]["warnings"] = (
        report["summary"]["unused_imports"]
        + report["summary"]["legacy_markers"]
        + report["summary"]["deprecated_apis"]
    )
    report["ga_pass"] = critical == 0

    out_path = PROJECT_ROOT / "quality_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False, default=str)
    print(f"Wrote {out_path}")
    print(f"  Critical errors: {critical}")
    print(f"  Deprecated APIs: {len(deprecated)}")
    print(f"  Unused imports (heuristic): {len(unused)}")
    print(f"  Legacy markers: {len(legacy)}")
    print(f"  GA pass: {report['ga_pass']}")


if __name__ == "__main__":
    main()
