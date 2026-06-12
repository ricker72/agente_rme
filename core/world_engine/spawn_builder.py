from __future__ import annotations

from typing import Dict, Optional

from core.planner.difficulty_planner import DifficultyPlanner
from core.planner.biome_planner import BiomePlanner
from core.knowledge.knowledge_base import KnowledgeGraph


class SpawnBuilder:
    def __init__(self, knowledge_graph: Optional[KnowledgeGraph] = None):
        self.knowledge_graph = knowledge_graph
        self.difficulty_planner = DifficultyPlanner()
        self.biome_planner = BiomePlanner()

    def build(self, zone_plan: Dict[str, object]) -> Dict[str, object]:
        difficulty = zone_plan.get("difficulty", "normal")
        spawn_type = zone_plan.get("zone_type", "HuntingZone")
        biome = self.biome_planner.place_biome(
            zone_plan.get("name", ""), region="outer"
        )
        monster = self._pick_monster(difficulty, biome.get("biome", "generic"))
        return {
            "zone": zone_plan.get("name"),
            "difficulty": difficulty,
            "monster": monster,
            "area": {
                "x": zone_plan.get("x"),
                "y": zone_plan.get("y"),
                "width": zone_plan.get("width"),
                "height": zone_plan.get("height"),
            },
            "type": spawn_type,
        }

    def _pick_monster(self, difficulty: str, biome: str) -> str:
        if self.knowledge_graph:
            return self.knowledge_graph.find_monster("orc") and "orc" or "rat"
        if difficulty in ("easy", "medium"):
            return "rat"
        return "demon"
