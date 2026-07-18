from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping


def build_manifest(files: Iterable[Mapping[str, Any]], package_name: str, package_fingerprint: str) -> Dict[str, Any]:
    return {
        "artifact": "WORLD_EXPORT_MANIFEST",
        "package": package_name,
        "package_fingerprint": package_fingerprint,
        "files": sorted((dict(item) for item in files), key=lambda item: item["path"]),
    }
