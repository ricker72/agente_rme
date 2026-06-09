from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from core.architecture import ArchitectureGraph
from core.knowledge.knowledge_base import KnowledgeGraph
from core.otbm import OtbmWriter
from .export_pipeline import ExportPipeline


@dataclass
class Tile:
    x: int
    y: int
    z: int
    ground: str = "floor"
    items: List[Dict[str, object]] = field(default_factory=list)
    decorations: List[str] = field(default_factory=list)
    spawn: Optional[Dict[str, object]] = None
    creature: Optional[Dict[str, object]] = None
    flags: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "ground": self.ground,
            "items": self.items,
            "decorations": self.decorations,
            "spawn": self.spawn,
            "creature": self.creature,
        }


@dataclass
class Chunk:
    x_index: int
    y_index: int
    size: int
    tiles: List[Tile] = field(default_factory=list)

    def add_tile(self, tile: Tile) -> None:
        self.tiles.append(tile)

    def tile_count(self) -> int:
        return len(self.tiles)


@dataclass
class WorldModel:
    tiles: Dict[str, Tile] = field(default_factory=dict)
    cities: List[Dict[str, object]] = field(default_factory=list)
    roads: List[Dict[str, object]] = field(default_factory=list)
    dungeons: List[Dict[str, object]] = field(default_factory=list)
    quests: List[Dict[str, object]] = field(default_factory=list)
    bosses: List[Dict[str, object]] = field(default_factory=list)
    spawns: List[Dict[str, object]] = field(default_factory=list)
    waypoints: List[Dict[str, object]] = field(default_factory=list)
    chunks: List[Chunk] = field(default_factory=list)

    def add_tile(self, tile: Tile) -> None:
        key = f"{tile.x}:{tile.y}:{tile.z}"
        self.tiles[key] = tile

    def add_city(self, city: Dict[str, object]) -> None:
        self.cities.append(city)

    def add_road(self, road: Dict[str, object]) -> None:
        self.roads.append(road)

    def add_dungeon(self, dungeon: Dict[str, object]) -> None:
        self.dungeons.append(dungeon)

    def add_quest(self, quest: Dict[str, object]) -> None:
        self.quests.append(quest)

    def add_boss(self, boss: Dict[str, object]) -> None:
        self.bosses.append(boss)

    def add_spawn(self, spawn: Dict[str, object]) -> None:
        self.spawns.append(spawn)

    def to_dict(self) -> Dict[str, object]:
        return {
            "tiles": [tile.to_dict() for tile in self.tiles.values()],
            "cities": self.cities,
            "roads": self.roads,
            "dungeons": self.dungeons,
            "quests": self.quests,
            "bosses": self.bosses,
            "spawns": self.spawns,
            "chunks": [{"x_index": c.x_index, "y_index": c.y_index, "size": c.size, "tile_count": c.tile_count()} for c in self.chunks],
        }


class TileFactory:
    def create_tile(self, x: int, y: int, z: int, ground: str = "floor") -> Tile:
        return Tile(x=x, y=y, z=z, ground=ground)


class BiomeApplicator:
    def apply(self, world_model: WorldModel, biome: str) -> None:
        for tile in world_model.tiles.values():
            if biome == "desert" and tile.ground == "floor":
                tile.ground = "sand"
            if biome == "shadow_land" and tile.ground == "floor":
                tile.ground = "shadow_floor"


class StructurePlacer:
    def place(self, world_model: WorldModel, x: int, y: int, z: int, width: int, height: int, ground: str = "floor") -> None:
        for iy in range(height):
            for ix in range(width):
                tile = Tile(x=x + ix, y=y + iy, z=z, ground=ground)
                world_model.add_tile(tile)


class CollisionEngine:
    def validate(self, world_model: WorldModel, x: int, y: int, z: int, width: int, height: int) -> bool:
        for iy in range(height):
            for ix in range(width):
                key = f"{x + ix}:{y + iy}:{z}"
                if key in world_model.tiles:
                    return False
        return True


class GenerationProfiler:
    def __init__(self):
        self.metrics = {
            "time_ms": 0,
            "tiles": 0,
            "structures": 0,
            "memory": 0,
        }

    def inc_tiles(self, count: int) -> None:
        self.metrics["tiles"] += count

    def inc_structures(self, count: int = 1) -> None:
        self.metrics["structures"] += count

    def get_metrics(self) -> Dict[str, object]:
        return self.metrics.copy()


class WorldEngine:
    def __init__(
        self,
        knowledge_graph: Optional[KnowledgeGraph] = None,
        architecture_graph: Optional[ArchitectureGraph] = None,
    ):
        from .world_builder import WorldBuilder

        self.knowledge_graph = knowledge_graph
        self.architecture_graph = architecture_graph
        self.builder = WorldBuilder(knowledge_graph, architecture_graph)
        self.export_pipeline = ExportPipeline()
        self.profiler = GenerationProfiler()

    def build(self, world_plan: WorldPlan) -> WorldModel:
        world_model = self.builder.build(world_plan)
        self.profiler.inc_tiles(len(world_model.tiles))
        self.profiler.inc_structures(len(world_model.cities) + len(world_model.dungeons) + len(world_model.roads))
        return world_model

    def export(self, world_model: WorldModel) -> str:
        self.export_pipeline.validate_quality(world_model)
        return self.export_pipeline.convert(world_model)

    def export_otbm(self, world_model: WorldModel, destination: str | Path) -> Path:
        self.export_pipeline.validate_quality(world_model)
        writer = OtbmWriter()
        return writer.write(world_model, destination, generate_templates=True)

    def get_profile(self) -> Dict[str, object]:
        return self.profiler.get_metrics()
