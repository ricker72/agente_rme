from __future__ import annotations

from typing import Optional

from core.architecture import ArchitectureGraph
from core.knowledge.knowledge_base import KnowledgeGraph
from .world_engine import WorldModel, TileFactory, BiomeApplicator, StructurePlacer, CollisionEngine
from .city_builder import CityBuilder
from .dungeon_builder import DungeonBuilder
from .road_builder import RoadBuilder
from .spawn_builder import SpawnBuilder
from .quest_builder import QuestBuilder
from .boss_builder import BossBuilder


class WorldBuilder:
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        architecture_graph: Optional[ArchitectureGraph] = None,
    ):
        self.knowledge_graph = knowledge_graph
        self.architecture_graph = architecture_graph
        self.city_builder = CityBuilder()
        self.dungeon_builder = DungeonBuilder()
        self.road_builder = RoadBuilder()
        self.spawn_builder = SpawnBuilder(knowledge_graph)
        self.quest_builder = QuestBuilder()
        self.boss_builder = BossBuilder()
        self.tile_factory = TileFactory()
        self.biome_applicator = BiomeApplicator()
        self.structurer = StructurePlacer()
        self.collision = CollisionEngine()

    def _entries(self, world_plan: object, key: str):
        value = getattr(world_plan, key, None) if not isinstance(world_plan, dict) else world_plan.get(key)
        return value or []

    def _default_style(self) -> str:
        if not self.knowledge_graph:
            return "issavi"
        context = self.knowledge_graph.build_context("", [], [], None)
        styles = context.get("city_styles") or ["issavi"]
        return styles[0] if styles else "issavi"

    def build(self, world_plan: object) -> WorldModel:
        world_model = WorldModel()

        for city in self._entries(world_plan, "cities"):
            city_model = self.city_builder.build(city)
            world_model.add_city(city_model)
            self._place_city_tiles(world_model, city)

        for dungeon in self._entries(world_plan, "dungeons"):
            dungeon_model = self.dungeon_builder.build(dungeon)
            world_model.add_dungeon(dungeon_model)
            self._place_dungeon_tiles(world_model, dungeon)

        for road in self._entries(world_plan, "roads"):
            road_model = self.road_builder.build(road)
            world_model.add_road(road_model)
            self._place_road_tiles(world_model, road)

        for spawn in self._entries(world_plan, "hunting_zones") + self._entries(world_plan, "boss_zones") + self._entries(world_plan, "quest_zones"):
            spawn_model = self.spawn_builder.build(spawn)
            world_model.add_spawn(spawn_model)

        for quest in self._entries(world_plan, "quest_zones"):
            quest_model = self.quest_builder.build(quest)
            world_model.add_quest(quest_model)

        for boss in self._entries(world_plan, "boss_zones"):
            boss_model = self.boss_builder.build(boss)
            world_model.add_boss(boss_model)

        self.biome_applicator.apply(world_model, self._default_style())

        return world_model

    def _place_city_tiles(self, world_model: WorldModel, city: dict) -> None:
        x = 10
        y = 10
        width = city.get("population", 500) // 12
        height = city.get("population", 500) // 14
        if self.collision.validate(world_model, x, y, 12, 10):
            self.structurer.place(world_model, x, y, 7, width, height, ground="floor")

    def _place_dungeon_tiles(self, world_model: WorldModel, dungeon: dict) -> None:
        x = 80
        y = 80
        width = dungeon.get("floors", 1) * 12
        height = 18
        if self.collision.validate(world_model, x, y, 8, 8):
            self.structurer.place(world_model, x, y, 7, width, height, ground="stone_floor")

    def _place_road_tiles(self, world_model: WorldModel, road: dict) -> None:
        segments = road.get("path", [])
        for idx, segment in enumerate(segments):
            tile = self.tile_factory.create_tile(segment.get("x", 0), segment.get("y", 0), 7, ground="road")
            world_model.add_tile(tile)
