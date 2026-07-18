from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

from .serializer import fingerprint_bytes


def validate_otbm_runtime(root: Path, certified_otbm: Mapping[str, Any], certified_export: Mapping[str, Any]) -> Dict[str, Any]:
    path = root / "generated.otbm"
    errors = []
    otbm_hash = ""
    size = 0
    if not path.exists():
        errors.append("generated.otbm missing")
    else:
        data = path.read_bytes()
        size = len(data)
        otbm_hash = fingerprint_bytes(data)
        if size <= 0:
            errors.append("generated.otbm empty")
    expected = {certified_otbm.get("fingerprint"), certified_export.get("quality_gates", {}).get("generated.otbm preserved") and otbm_hash}
    if certified_otbm.get("fingerprint") and otbm_hash != certified_otbm.get("fingerprint"):
        errors.append("OTBM checksum does not match WGL-08 certification")
    roundtrip_path = root / "OTBM_ROUNDTRIP_VALIDATION.json"
    roundtrip_present = roundtrip_path.exists()
    tile_count = item_count = 0
    if roundtrip_present:
        import json

        roundtrip = json.loads(roundtrip_path.read_text(encoding="utf-8"))
        tile_count = int(roundtrip.get("tile_count", 0))
        item_count = int(roundtrip.get("item_count", 0))
        if tile_count <= 0:
            errors.append("invalid roundtrip tile count")
        if item_count <= 0:
            errors.append("invalid roundtrip item count")
    else:
        errors.append("OTBM roundtrip metadata missing")
    return {
        "artifact": "OTBM_RUNTIME_VALIDATION",
        "valid": not errors,
        "exists": path.exists(),
        "size": size,
        "fingerprint": otbm_hash,
        "expected_records": sorted(str(item) for item in expected if item),
        "roundtrip_metadata_present": roundtrip_present,
        "tile_count": tile_count,
        "item_count": item_count,
        "errors": errors,
    }
