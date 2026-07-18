from __future__ import annotations

from typing import Any, Dict, Mapping


def optimize_export(manifest: Mapping[str, Any], validation: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact": "WORLD_EXPORT_OPTIMIZATION",
        "package_size": "deterministic_zip_deflate",
        "metadata_deduplication": "manifest_checksums",
        "xml_ordering": "stable",
        "serialization_consistency": "stable",
        "valid": bool(validation["valid"]) and bool(manifest.get("files")),
    }
