from __future__ import annotations

from typing import Any, Dict, Iterable


def build_certification(
    *,
    fingerprint: str,
    metrics: Dict[str, float],
    quality_gates: Dict[str, bool],
    generated_artifacts: Iterable[str],
) -> Dict[str, Any]:
    certified = all(quality_gates.values()) and all(value >= 1.0 for value in metrics.values())
    return {
        "artifact": "CERTIFIED_OTBM_WORLD",
        "decision": "CERTIFIED" if certified else "REJECTED",
        "certification": "WGL08_OTBM_WORLD_SERIALIZATION_ACTIVE" if certified else None,
        "mission": "WGL-08 OTBM World Serialization Layer",
        "serialization_only": True,
        "forbidden_content_generated": False,
        "fingerprint": fingerprint,
        "metrics": metrics,
        "quality_gates": quality_gates,
        "generated_artifacts": list(generated_artifacts),
        "next_milestone": "WGL-09 Lua & Gameplay Metadata Layer",
    }
