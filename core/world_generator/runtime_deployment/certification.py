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
        "artifact": "CERTIFIED_RUNTIME_DEPLOYMENT",
        "decision": "CERTIFIED" if certified else "REJECTED",
        "certification": "WGL12_RUNTIME_DEPLOYMENT_ACTIVE" if certified else None,
        "ep01_status": "EP01_WORLD_GENERATION_2_0_CERTIFIED" if certified else None,
        "mission": "WGL-12 Runtime Validation & Deployment Layer",
        "validation_only": True,
        "fingerprint": fingerprint,
        "metrics": dict(metrics),
        "quality_gates": dict(quality_gates),
        "generated_artifacts": list(generated_artifacts),
        "next_program": "EP-02 Advanced World Intelligence",
    }
