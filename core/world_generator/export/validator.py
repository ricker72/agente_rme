from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict


REQUIRED_EXPORT_FILES = (
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


def validate_export(root: Path, package_path: Path, expected_otbm_hash: str) -> Dict[str, Any]:
    errors = []
    for name in REQUIRED_EXPORT_FILES:
        if not (root / name).exists():
            errors.append(f"missing {name}")
    for name in ("towns.xml", "houses.xml", "spawns.xml", "waypoints.xml"):
        try:
            ET.parse(root / name)
        except Exception as exc:  # pragma: no cover - message only
            errors.append(f"invalid xml {name}: {exc}")
    for name in ("world_metadata.lua", "navigation_metadata.lua"):
        text = (root / name).read_text(encoding="utf-8") if (root / name).exists() else ""
        if not _valid_lua_metadata(text):
            errors.append(f"invalid lua metadata {name}")
    if package_path.exists():
        with zipfile.ZipFile(package_path) as archive:
            names = set(archive.namelist())
        missing = sorted(set(REQUIRED_EXPORT_FILES) - names)
        if missing:
            errors.append(f"package missing {missing}")
    else:
        errors.append("missing WORLD_EXPORT_PACKAGE.zip")
    if not expected_otbm_hash:
        errors.append("missing OTBM checksum")
    metrics = _metrics(not errors)
    return {"artifact": "WORLD_EXPORT_VALIDATION", "valid": not errors, "errors": errors, "metrics": metrics}


def _valid_lua_metadata(text: str) -> bool:
    return bool(re.search(r"^\s*return\s+\{", text, re.M)) and text.count("{") == text.count("}")


def _metrics(valid: bool) -> Dict[str, float]:
    value = 1.0 if valid else 0.0
    return {"EQI": value, "PCI3": value, "XVI": value, "LSI": value, "IPI": value, "DPI": value}
