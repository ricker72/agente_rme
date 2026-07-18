"""Block Git objects that are too large for a normal GitHub repository."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_LIMIT_MIB = 95


def _git(root: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.decode("utf-8", errors="replace").strip())
    return completed.stdout


def _paths(output: bytes) -> list[str]:
    return [entry.decode("utf-8", errors="surrogateescape") for entry in output.split(b"\0") if entry]


def _is_lfs(root: Path, path: str) -> bool:
    output = _git(root, "check-attr", "filter", "--", path).decode("utf-8", errors="replace")
    return output.rstrip().endswith(": lfs")


def _working_tree_violations(root: Path, paths: list[str], limit: int) -> list[tuple[int, str, str]]:
    violations: list[tuple[int, str, str]] = []
    for relative in paths:
        candidate = root / relative
        if not candidate.is_file():
            continue
        size = candidate.stat().st_size
        if size >= limit and not _is_lfs(root, relative):
            violations.append((size, relative, "working-tree"))
    return violations


def _history_violations(root: Path, limit: int) -> list[tuple[int, str, str]]:
    objects = _git(root, "rev-list", "--objects", "--all")
    if not objects.strip():
        return []
    checked = _git(
        root,
        "cat-file",
        "--batch-check=%(objectname) %(objecttype) %(objectsize) %(rest)",
        input_bytes=objects,
    )
    violations: list[tuple[int, str, str]] = []
    for raw_line in checked.splitlines():
        parts = raw_line.decode("utf-8", errors="replace").split(" ", 3)
        if len(parts) < 3 or parts[1] != "blob":
            continue
        size = int(parts[2])
        if size >= limit:
            violations.append((size, parts[3] if len(parts) == 4 else parts[0], "history"))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--limit-mib", type=float, default=DEFAULT_LIMIT_MIB)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--tracked", action="store_true")
    parser.add_argument("--history", action="store_true")
    args = parser.parse_args()

    root = args.root.resolve()
    limit = int(args.limit_mib * 1024 * 1024)
    if not any((args.staged, args.tracked, args.history)):
        args.tracked = args.history = True

    violations: list[tuple[int, str, str]] = []
    checked: list[str] = []
    if args.staged:
        staged = _paths(_git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"))
        violations.extend(_working_tree_violations(root, staged, limit))
        checked.append(f"staged:{len(staged)}")
    if args.tracked:
        tracked = _paths(_git(root, "ls-files", "-z"))
        violations.extend(_working_tree_violations(root, tracked, limit))
        checked.append(f"tracked:{len(tracked)}")
    if args.history:
        violations.extend(_history_violations(root, limit))
        checked.append("history:all")

    unique = sorted(set(violations), reverse=True)
    if unique:
        print(f"BLOCKED: GitHub size safety limit is {args.limit_mib} MiB.", file=sys.stderr)
        for size, path, source in unique:
            print(f"  {size / 1024 / 1024:.2f} MiB [{source}] {path}", file=sys.stderr)
        print("Use a GitHub Release, regenerate locally, or configure Git LFS deliberately.", file=sys.stderr)
        return 2

    print(f"PASS: no Git objects reach {args.limit_mib} MiB ({', '.join(checked)}).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(3) from exc
