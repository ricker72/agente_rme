"""Conservative cleanup for generated Agente RME runtime artifacts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil


_GENERATED_ROOTS = ("logs", "reports", "output", "output_benchmark")
_TRANSIENT_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov")


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def cleanup_expired_artifacts(
    workspace_root: Path | str | None = None,
    *,
    retention: timedelta = timedelta(hours=24),
    now: datetime | None = None,
) -> tuple[Path, ...]:
    """Remove expired generated files without touching source, maps, or user assets."""

    root = Path(workspace_root) if workspace_root is not None else Path(__file__).resolve().parents[1]
    root = root.resolve()
    if not (root / "pyproject.toml").is_file():
        return ()

    current = now or datetime.now(timezone.utc)
    cutoff = current.timestamp() - retention.total_seconds()
    removed: list[Path] = []

    for name in _TRANSIENT_DIRS:
        for candidate in root.rglob(name):
            if candidate.is_dir() and _is_within(candidate, root):
                shutil.rmtree(candidate, ignore_errors=True)
                if not candidate.exists():
                    removed.append(candidate)

    for name in _GENERATED_ROOTS:
        generated_root = root / name
        if not generated_root.is_dir() or not _is_within(generated_root, root):
            continue
        for candidate in sorted(generated_root.rglob("*"), reverse=True):
            if not _is_within(candidate, generated_root):
                continue
            if candidate.is_file() and candidate.stat().st_mtime < cutoff:
                candidate.unlink(missing_ok=True)
                removed.append(candidate)
            elif candidate.is_dir():
                try:
                    candidate.rmdir()
                except OSError:
                    pass

    return tuple(removed)
