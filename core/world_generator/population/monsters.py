from __future__ import annotations

from typing import Any, Dict, Mapping

from .ecosystem import plan_ecosystems


def plan_monster_ecosystem(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    return plan_ecosystems(inputs)
