from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping


def build_certification(
    *,
    fingerprint: str,
    metrics: Mapping[str, float],
    quality_gates: Mapping[str, bool],
    generated_artifacts: Iterable[str],
) -> Dict[str, Any]:
    certified = all(quality_gates.values()) and all(value >= 1.0 for value in metrics.values())
    return {
        "artifact": "CERTIFIED_WORLD_EXPORT",
        "decision": "CERTIFIED" if certified else "REJECTED",
        "certification": "WGL11_WORLD_EXPORT_ACTIVE" if certified else None,
        "mission": "WGL-11 World Integration & Export Layer",
        "integration_export_only": True,
        "otbm_modified": False,
        "fingerprint": fingerprint,
        "metrics": dict(metrics),
        "quality_gates": dict(quality_gates),
        "generated_artifacts": list(generated_artifacts),
        "next_milestone": "WGL-12 Runtime Validation & Deployment Layer",
    }
