from __future__ import annotations

from typing import Any, Dict, Mapping


def build_deployment_report(runtime_model: Mapping[str, Any], compatibility: Mapping[str, Any], validations: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "artifact": "DEPLOYMENT_REPORT",
        "summary": "CERTIFIED" if runtime_model["deployment_ready"] else "BLOCKED",
        "deployment_ready": runtime_model["deployment_ready"],
        "compatibility": {item["target"]: item["compatible"] for item in compatibility.get("targets", [])},
        "diagnostics": {key: value.get("errors", []) for key, value in sorted(validations.items())},
    }
