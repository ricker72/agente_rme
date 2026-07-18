"""Crash-resistant helpers for small application state and JSON artifacts."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any


class SafeIOError(RuntimeError):
    """A bounded or atomic persistence operation could not be completed."""


def atomic_write_text(
    path: str | Path,
    content: str,
    *,
    encoding: str = "utf-8",
    backup: bool = True,
) -> None:
    """Write text in the destination directory and atomically replace the target."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding=encoding,
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
            newline="",
        ) as handle:
            temporary = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if backup and target.is_file():
            shutil.copy2(target, target.with_suffix(target.suffix + ".bak"))
        os.replace(temporary, target)
        temporary = None
    except (OSError, UnicodeError) as exc:
        raise SafeIOError(f"Atomic write failed for {target}: {exc}") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def atomic_write_json(
    path: str | Path,
    payload: Any,
    *,
    indent: int = 2,
    sort_keys: bool = False,
    backup: bool = True,
) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, indent=indent, sort_keys=sort_keys),
        backup=backup,
    )


def read_json_bounded(
    path: str | Path,
    *,
    default: Any = None,
    max_bytes: int = 64 * 1024 * 1024,
    use_backup: bool = True,
) -> Any:
    """Read bounded JSON, falling back to the last atomic-write backup."""
    target = Path(path)
    candidates = [target]
    if use_backup:
        candidates.append(target.with_suffix(target.suffix + ".bak"))
    errors: list[str] = []
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            size = candidate.stat().st_size
            if size > max_bytes:
                raise SafeIOError(
                    f"JSON exceeds {max_bytes} bytes ({size}): {candidate}"
                )
            return json.loads(candidate.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError, SafeIOError) as exc:
            errors.append(f"{candidate}: {exc}")
    if default is not None:
        return default
    detail = "; ".join(errors) if errors else "file and backup are missing"
    raise SafeIOError(f"JSON read failed for {target}: {detail}")
