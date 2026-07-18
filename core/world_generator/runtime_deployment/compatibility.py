from __future__ import annotations

from typing import Any, Dict, Mapping

TARGETS = ("Remere's Map Editor", "OpenTibiaBR", "Canary", "The Forgotten Server", "OTServBR", "OTClient")


def build_engine_compatibility_matrix(validations: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    base_valid = all(item.get("valid") for item in validations.values())
    checks = []
    for target in TARGETS:
        checks.append(
            {
                "target": target,
                "mode": "offline_static",
                "otbm": validations["otbm"].get("valid", False),
                "xml": validations["xml"].get("valid", False),
                "lua_metadata": validations["lua"].get("valid", False),
                "package": validations["package"].get("valid", False),
                "compatible": base_valid,
            }
        )
    return {"artifact": "ENGINE_COMPATIBILITY_MATRIX", "mode": "offline_static", "valid": base_valid, "targets": checks}
