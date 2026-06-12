from __future__ import annotations

from typing import Dict, List, Optional

from core.architecture import PatternLibrary, ArchitectureGraph
from core.game_design import ExpansionDesigner
from core.knowledge.knowledge_base import KnowledgeGraph
from .city_plan import CityPlan
from .dungeon_plan import DungeonPlan
from .expansion_plan import ExpansionPlanner
from .prompt_interpreter import PromptInterpreter
from .route_plan import RoutePlanner
from .world_plan import WorldPlan
from .zone_plan import ZonePlan
from .world_size_estimator import WorldSizeEstimator
from .world_validator import WorldValidator
from .biome_planner import BiomePlanner
from .difficulty_planner import DifficultyPlanner


class AIPlanner:
    def __init__(
        self,
        pattern_library: Optional[PatternLibrary] = None,
        architecture_graph: Optional[ArchitectureGraph] = None,
        knowledge_graph: Optional[KnowledgeGraph] = None,
    ):
        self.pattern_library = pattern_library or PatternLibrary()
        self.architecture_graph = architecture_graph or ArchitectureGraph()
        self.knowledge_graph = knowledge_graph
        self.interpreter = PromptInterpreter()
        self.route_planner = RoutePlanner()
        self.expansion_planner = ExpansionPlanner()
        self.expansion_designer = ExpansionDesigner()
        self.validator = WorldValidator()
        self.size_estimator = WorldSizeEstimator()
        self.biome_planner = BiomePlanner()
        self.difficulty_planner = DifficultyPlanner()

    def plan(self, prompt: str) -> Dict[str, object]:
        interpreted = self.interpreter.interpret(prompt)
        expansion = self.expansion_designer.design(prompt)
        world_plan = WorldPlan()

        city_name = expansion.theme or interpreted.get("city") or "issavi"
        dungeon_theme = expansion.theme or interpreted.get("dungeon") or "roshamuul"
        difficulty = self.difficulty_planner.plan(interpreted.get("difficulty_range"))
        biome = self.biome_planner.place_biome(city_name, region="central")

        district_blueprints = [
            {"type": "temple", "name": "Temple District"},
            {"type": "market", "name": "Market District"},
            {"type": "residential", "name": "Residential Quarter"},
        ]
        city_meta = (
            expansion.cities[0]
            if expansion.cities
            else {
                "name": f"New {city_name.capitalize()}",
                "districts": ["Market", "Temple"],
            }
        )
        city = CityPlan(
            name=city_meta.get("name", f"New {city_name.capitalize()}"),
            theme=city_name,
            population=city_meta.get("population", 1200),
            districts=city_meta.get(
                "districts", [d["name"] for d in district_blueprints]
            ),
            zones=[
                ZonePlan(
                    zone_type="ResidentialZone",
                    name=city_meta.get("name", "Barrio Principal"),
                    x=10,
                    y=10,
                    width=24,
                    height=18,
                    difficulty=difficulty,
                    purpose="housing",
                    features=["houses", "gardens"],
                )
            ],
        )

        dungeon = DungeonPlan(
            name=f"{dungeon_theme.capitalize()} Depths",
            theme=dungeon_theme,
            floors=4,
            difficulty=difficulty,
            bosses=[
                {
                    "name": boss.get("name", f"{dungeon_theme} Warlord"),
                    "theme": dungeon_theme,
                }
                for boss in expansion.bosses[:2]
            ],
            quests=[
                {
                    "name": quest.get("title", "Advance the story"),
                    "reward": quest.get("reward", "experience"),
                }
                for quest in expansion.quests[:2]
            ],
            connections=[
                {
                    "from": city.name,
                    "to": f"{dungeon_theme.capitalize()} Depths",
                    "type": "underpass",
                }
            ],
        )

        world_plan.cities.append(city)
        world_plan.dungeons.append(dungeon)
        world_plan.roads.append(
            {"from": city.name, "to": dungeon.name, "type": "main_road"}
        )
        world_plan.ports.append(
            {"name": f"{city_name.capitalize()} Harbor", "theme": city_name}
        )
        world_plan.teleports.append({"name": "Central Gate", "target": dungeon.name})

        for index, hunt in enumerate(expansion.hunts, start=1):
            world_plan.hunting_zones.append(
                self._build_zone(
                    "HuntingZone",
                    hunt.get("name", f"Hunt {index}"),
                    20 + index * 4,
                    30 + index * 2,
                    16,
                    12,
                    difficulty,
                )
            )

        for index, boss in enumerate(expansion.bosses[:3], start=1):
            world_plan.boss_zones.append(
                self._build_zone(
                    "BossZone",
                    boss.get("arena", f"Boss Arena {index}"),
                    40,
                    10 + index * 8,
                    18,
                    16,
                    difficulty,
                )
            )

        for index, quest in enumerate(expansion.quests[:2], start=1):
            world_plan.quest_zones.append(
                self._build_zone(
                    "QuestZone",
                    quest.get("title", f"Quest {index}"),
                    35,
                    5 + index * 4,
                    14,
                    10,
                    difficulty,
                )
            )

        self.architecture_graph.add_structure(
            city.theme, ["temple", "market", "residential"]
        )
        self.architecture_graph.add_structure(
            dungeon.theme, ["entrance", "boss_room", "treasure_hall"]
        )

        world_plan_data = world_plan.to_dict()
        world_plan_data["expansion"] = expansion.to_dict()

        return {
            "world_plan": world_plan_data,
            "biome": biome,
            "expansion": expansion.to_dict(),
            "size_estimate": self.size_estimator.estimate(world_plan.to_dict()),
            "plan_valid": self.validator.validate(world_plan.to_dict())[0],
            "validation": self.validator.validate(world_plan.to_dict())[1],
        }

    def _build_zone(
        self,
        zone_type: str,
        name: str,
        x: int,
        y: int,
        width: int,
        height: int,
        difficulty: str,
    ) -> ZonePlan:
        return ZonePlan(
            zone_type=zone_type,
            name=name,
            x=x,
            y=y,
            width=width,
            height=height,
            difficulty=difficulty,
            purpose=zone_type.lower(),
            features=[zone_type.lower()],
        )

    def render_to_lua(self, plan: Dict[str, object]) -> str:
        world_plan = plan.get("world_plan", {})
        lines: List[str] = [
            "-- WORLD PLAN GENERATED Lua",
            f"-- Cities: {len(world_plan.get('cities', []))}",
            f"-- Dungeons: {len(world_plan.get('dungeons', []))}",
            f"-- Roads: {len(world_plan.get('roads', []))}",
            "if not app.hasMap() then",
            "  return",
            "end",
            "\napp.transaction(function(map)",
        ]

        for city in world_plan.get("cities", []):
            lines.append(f"  -- City: {city.get('name')} ({city.get('theme')})")
            lines.append(f"  -- Population: {city.get('population')}")

        for dungeon in world_plan.get("dungeons", []):
            lines.append(
                f"  -- Dungeon: {dungeon.get('name')} difficulty: {dungeon.get('difficulty')}"
            )

        for road in world_plan.get("roads", []):
            lines.append(
                f"  -- Route {road.get('type')} connects {road.get('from')} to {road.get('to')}"
            )

        lines.append("end")
        return "\n".join(lines)
