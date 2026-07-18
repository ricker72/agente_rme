from __future__ import annotations

import zipfile
from pathlib import Path
from typing import Any, Dict, Mapping

from .serializer import fingerprint_bytes

REQUIRED_PACKAGE_FILES = (
    "generated.otbm",
    "towns.xml",
    "houses.xml",
    "spawns.xml",
    "waypoints.xml",
    "world_metadata.lua",
    "navigation_metadata.lua",
    "WORLD_EXPORT_MODEL.json",
    "WORLD_EXPORT_MANIFEST.json",
)


def validate_package(root: Path, certified_export: Mapping[str, Any]) -> Dict[str, Any]:
    package_path = root / "WORLD_EXPORT_PACKAGE.zip"
    errors = []
    package_hash = ""
    package_files = []
    if not package_path.exists():
        errors.append("WORLD_EXPORT_PACKAGE.zip missing")
    else:
        package_hash = fingerprint_bytes(package_path.read_bytes())
        try:
            with zipfile.ZipFile(package_path) as archive:
                package_files = sorted(archive.namelist())
                bad = archive.testzip()
                if bad:
                    errors.append(f"corrupt zip member: {bad}")
                for name in REQUIRED_PACKAGE_FILES:
                    if name not in package_files:
                        errors.append(f"package missing {name}")
        except zipfile.BadZipFile:
            errors.append("WORLD_EXPORT_PACKAGE.zip cannot be opened")
    if certified_export.get("fingerprint") and package_hash != certified_export.get("fingerprint"):
        errors.append("package checksum does not match certified export")
    return {
        "artifact": "PACKAGE_INTEGRITY_VALIDATION",
        "valid": not errors,
        "package_exists": package_path.exists(),
        "package_opens": package_path.exists() and not errors,
        "package_fingerprint": package_hash,
        "required_files": list(REQUIRED_PACKAGE_FILES),
        "package_files": package_files,
        "errors": errors,
    }
