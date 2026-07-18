from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Mapping

EXPECTED_ROOTS = {"towns.xml": "towns", "houses.xml": "houses", "spawns.xml": "spawns", "waypoints.xml": "waypoints"}


def validate_xml_runtime(root: Path, gameplay: Mapping[str, Any]) -> Dict[str, Any]:
    errors = []
    files = {}
    for name, expected_root in EXPECTED_ROOTS.items():
        path = root / name
        info = {"exists": path.exists(), "valid": False, "root": None, "count": 0}
        if not path.exists():
            errors.append(f"{name} missing")
        else:
            try:
                tree = ET.parse(path)
                element = tree.getroot()
                info["root"] = element.tag
                info["count"] = len(list(element))
                info["valid"] = element.tag == expected_root
                if element.tag != expected_root:
                    errors.append(f"{name} invalid root")
                _validate_required_attrs(name, element, errors)
            except ET.ParseError as exc:
                errors.append(f"{name} parse error: {exc}")
        files[name] = info
    expected_towns = len(gameplay.get("models", {}).get("towns", {}).get("towns", []))
    if files.get("towns.xml", {}).get("count", 0) != expected_towns:
        errors.append("towns.xml count does not match certified gameplay metadata")
    return {"artifact": "XML_RUNTIME_VALIDATION", "valid": not errors, "files": files, "errors": errors}


def _validate_required_attrs(name: str, root: ET.Element, errors: list[str]) -> None:
    required = {
        "towns.xml": ("id", "name", "settlement"),
        "houses.xml": ("houseid", "name", "entryx", "entryy", "entryz", "rent", "townid"),
        "spawns.xml": ("id", "monstersPlaced"),
        "waypoints.xml": ("id",),
    }[name]
    for child in root:
        if child.tag == "edge":
            continue
        for attr in required:
            if attr not in child.attrib:
                errors.append(f"{name} {child.tag} missing {attr}")
