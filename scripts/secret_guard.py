#!/usr/bin/env python3
"""Reject credentials from staged files, the tracked tree, or Git history."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Iterator


SECRET_PATTERNS = (
    ("OpenRouter/API token", re.compile(rb"\bsk-(?:or-v1|paxsenix|proj)-[A-Za-z0-9_-]{20,}\b")),
    ("generic secret key", re.compile(rb"\bsk-[A-Za-z0-9_-]{32,}\b")),
    ("GitHub token", re.compile(rb"\b(?:ghp|gho|ghu|ghs|github_pat)_[A-Za-z0-9_]{20,}\b")),
    ("AWS access key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("cloud token", re.compile(rb"\b[a-f0-9]{32}\.[A-Za-z0-9_-]{16,}\b", re.IGNORECASE)),
    (
        "private key",
        re.compile(
            rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            rb"\s+[A-Za-z0-9+/=\r\n]{80,}\s+"
            rb"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
)


def git(*args: str, input_data: bytes | None = None) -> bytes:
    result = subprocess.run(
        ("git", *args),
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(message or f"git {' '.join(args)} failed")
    return result.stdout


def nul_paths(raw: bytes) -> Iterator[str]:
    for value in raw.split(b"\0"):
        if value:
            yield value.decode("utf-8", "surrogateescape")


def staged_files() -> Iterator[tuple[str, bytes]]:
    raw = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    for path in nul_paths(raw):
        try:
            yield f"staged:{path}", git("show", f":{path}")
        except RuntimeError:
            continue


def tracked_files() -> Iterator[tuple[str, bytes]]:
    root = Path(git("rev-parse", "--show-toplevel").decode().strip())
    for path in nul_paths(git("ls-files", "-z")):
        candidate = root / path
        try:
            yield f"tracked:{path}", candidate.read_bytes()
        except OSError:
            continue


def path_files(root: Path) -> Iterator[tuple[str, bytes]]:
    root = root.resolve()
    ignored_directories = {".git", "node_modules", "__pycache__", ".venv", "venv"}
    non_config_suffixes = {
        ".dat", ".ilk", ".jpg", ".jpeg", ".mp3", ".mp4", ".otbm", ".pak",
        ".pdb", ".png", ".spr", ".wav", ".webp",
    }
    for candidate in root.rglob("*"):
        if not candidate.is_file() or candidate.is_symlink():
            continue
        try:
            relative = candidate.relative_to(root)
        except ValueError:
            continue
        if any(part in ignored_directories for part in relative.parts):
            continue
        if candidate.suffix.lower() in non_config_suffixes:
            continue
        if candidate.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(candidate) as archive:
                    for member in archive.infolist():
                        member_path = Path(member.filename)
                        if member.is_dir() or member_path.suffix.lower() in non_config_suffixes:
                            continue
                        yield (
                            f"path:{root.name}/{relative.as_posix()}!{member.filename}",
                            archive.read(member),
                        )
            except (OSError, zipfile.BadZipFile, RuntimeError):
                pass
            continue
        try:
            yield f"path:{root.name}/{relative.as_posix()}", candidate.read_bytes()
        except OSError:
            continue


def reachable_objects() -> list[str]:
    objects: list[str] = []
    for line in git("rev-list", "--objects", "--all").splitlines():
        if line:
            objects.append(line.split(maxsplit=1)[0].decode("ascii"))
    return objects


def history_blobs() -> Iterator[tuple[str, bytes]]:
    objects = reachable_objects()
    if not objects:
        return

    process = subprocess.Popen(
        ("git", "cat-file", "--batch"),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    for object_id in objects:
        process.stdin.write(object_id.encode("ascii") + b"\n")
        process.stdin.flush()
        header = process.stdout.readline().rstrip(b"\n")
        parts = header.split()
        if len(parts) != 3 or parts[1] == b"missing":
            continue
        size = int(parts[2])
        data = process.stdout.read(size)
        process.stdout.read(1)
        if parts[1] == b"blob":
            yield f"history:{object_id}", data

    process.stdin.close()
    process.stdout.close()
    process.wait()


def scan(items: Iterable[tuple[str, bytes]]) -> list[tuple[str, str]]:
    violations: list[tuple[str, str]] = []
    for label, data in items:
        for description, pattern in SECRET_PATTERNS:
            if pattern.search(data):
                violations.append((label, description))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--tracked", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument(
        "--path",
        action="append",
        type=Path,
        default=[],
        help="scan a filesystem tree, including builds and ignored files",
    )
    args = parser.parse_args()

    if not (args.staged or args.tracked or args.history or args.path):
        args.tracked = True
        args.history = True

    sources: list[Iterable[tuple[str, bytes]]] = []
    labels: list[str] = []
    if args.staged:
        sources.append(staged_files())
        labels.append("staged")
    if args.tracked:
        sources.append(tracked_files())
        labels.append("tracked")
    if args.history:
        sources.append(history_blobs())
        labels.append("history")
    for path in args.path:
        sources.append(path_files(path))
        labels.append(f"path:{path.resolve()}")

    try:
        violations: list[tuple[str, str]] = []
        for source in sources:
            violations.extend(scan(source))
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"ERROR: secret guard could not complete: {exc}", file=sys.stderr)
        return 1

    if violations:
        print("BLOCKED: possible credentials detected. Values are intentionally hidden.")
        for location, description in violations:
            print(f" - {location}: {description}")
        print("Remove the credential, rotate it, and use an environment variable or OS secret store.")
        return 2

    print(f"PASS: no credential values detected ({', '.join(labels)}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
