from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from core.world_engine import WorldEngine


class ExpansionWorldBuilder:
    def __init__(self, knowledge_graph: Any = None, architecture_graph: Any = None):
        self.engine = WorldEngine(knowledge_graph, architecture_graph)

    def build_plan(self, campaign_blueprint: Dict[str, object]) -> Dict[str, object]:
        return {
            "cities": campaign_blueprint.get("cities", []),
            "dungeons": campaign_blueprint.get("dungeons", []),
            "roads": campaign_blueprint.get("roads", []),
            "hunting_zones": campaign_blueprint.get("hunts", []),
            "boss_zones": campaign_blueprint.get("boss_zones", []),
            "quest_zones": campaign_blueprint.get("quest_zones", []),
        }

    def build_model(self, campaign_blueprint: Dict[str, object]) -> Any:
        world_plan = self.build_plan(campaign_blueprint)
        return self.engine.build(world_plan)

    def export_lua(self, world_model: Any) -> str:
        return self.engine.export(world_model)

    def export_otbm(self, world_model: Any, destination: str | Path) -> Path:
        return self.engine.export_otbm(world_model, destination)
