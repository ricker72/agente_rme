"""Application path resolution for user-editable RME AI Studio data."""

from __future__ import annotations

import os
import sys
from pathlib import Path


class InvalidProjectRootError(RuntimeError):
    """Raised when a user project path resolves inside application internals."""


def is_packaged_runtime() -> bool:
    return bool(getattr(sys, "frozen", False))


def documents_root() -> Path:
    override = os.environ.get("RME_AI_DOCUMENTS_ROOT")
    if override:
        return Path(override).expanduser().resolve()
    profile = os.environ.get("USERPROFILE")
    if profile:
        return (Path(profile) / "Documents").resolve()
    return (Path.home() / "Documents").resolve()


def get_user_projects_root(workspace_root: str | Path | None = None) -> Path:
    """Return the canonical projects directory for source or packaged runtime."""

    override = os.environ.get("RME_AI_PROJECTS_ROOT")
    if override:
        return validate_project_root(Path(override).expanduser().resolve())

    if is_packaged_runtime():
        return validate_project_root(documents_root() / "RME AI Studio" / "projects")

    base = Path(workspace_root).resolve() if workspace_root is not None else Path.cwd().resolve()
    return validate_project_root(base / "projects")


def validate_project_root(path: str | Path) -> Path:
    resolved = Path(path).expanduser().resolve()
    parts = {part.lower() for part in resolved.parts}
    if "_internal" in parts or "dist" in parts:
        raise InvalidProjectRootError(f"INVALID_PROJECT_ROOT: {resolved}")

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        meipass_path = Path(meipass).resolve()
        try:
            resolved.relative_to(meipass_path)
        except ValueError:
            pass
        else:
            raise InvalidProjectRootError(f"INVALID_PROJECT_ROOT: {resolved}")
    return resolved


def validate_user_project_path(path: str | Path) -> Path:
    return validate_project_root(path)
