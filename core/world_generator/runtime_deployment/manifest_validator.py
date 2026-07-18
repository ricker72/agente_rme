from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .serializer import fingerprint_bytes


def validate_manifest(root: Path) -> Dict[str, Any]:
    path = root / "WORLD_EXPORT_MANIFEST.json"
    errors = []
    entries = []
    if not path.exists():
        errors.append("WORLD_EXPORT_MANIFEST.json missing")
    else:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        entries = manifest.get("files", [])
        for entry in entries:
            if entry["path"] == "WORLD_EXPORT_MANIFEST.json":
                continue
            file_path = root / entry["path"]
            if not file_path.exists():
                errors.append(f"manifest file missing: {entry['path']}")
                continue
            data = file_path.read_bytes()
            if len(data) != int(entry["bytes"]):
                errors.append(f"manifest size mismatch: {entry['path']}")
            if fingerprint_bytes(data) != entry["sha256"]:
                errors.append(f"manifest hash mismatch: {entry['path']}")
    return {"artifact": "DEPLOYMENT_MANIFEST_VALIDATION", "valid": not errors, "entry_count": len(entries), "errors": errors}
