from __future__ import annotations

from typing import Any, Dict, Mapping


def build_runtime_deployment_model(validations: Mapping[str, Any], compatibility: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact": "RUNTIME_DEPLOYMENT_MODEL",
        "validation_only": True,
        "deployment_ready": all(item.get("valid", False) for item in validations.values()) and compatibility.get("valid", False),
        "validated_components": sorted(validations),
        "compatibility_targets": [item["target"] for item in compatibility.get("targets", [])],
    }
