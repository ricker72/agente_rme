from __future__ import annotations

from typing import Any, Dict, Mapping


def build_regression_baseline(runtime_model: Mapping[str, Any], validations: Mapping[str, Any], fingerprint: str) -> Dict[str, Any]:
    return {
        "artifact": "DEPLOYMENT_REGRESSION_BASELINE",
        "fingerprint": fingerprint,
        "deployment_ready": runtime_model["deployment_ready"],
        "validation_status": {key: value.get("valid", False) for key, value in sorted(validations.items())},
    }
