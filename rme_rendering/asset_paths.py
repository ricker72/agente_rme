"""Resolve the validated external Tibia asset directory for render consumers."""

from __future__ import annotations

import os
from pathlib import Path


def resolve_client_asset_root(workspace_root: str | Path | None = None) -> Path:
    """Prefer the startup-certified client path over repository metadata assets."""
    configured = os.environ.get("RME_AGENT_ASSET_PATH")
    if configured:
        return Path(configured).expanduser().resolve(strict=False)

    root = Path(workspace_root or Path.cwd()).expanduser().resolve(strict=False)
    if (root / "catalog-content.json").is_file():
        return root
    return root / "assets"

