from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable


def validate_e2e_chain(root: Path, markers: Iterable[str], artifact_names: Iterable[str]) -> Dict[str, Any]:
    missing_markers = [marker for marker in markers if not (root / marker).exists()]
    missing_artifacts = [name for name in artifact_names if not (root / name).exists()]
    return {
        "artifact": "E2E_RUNTIME_VALIDATION",
        "valid": not missing_markers and not missing_artifacts,
        "missing_markers": missing_markers,
        "missing_artifacts": missing_artifacts,
    }
