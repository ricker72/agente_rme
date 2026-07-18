from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from core.editor.editable_map import EditableMap, Position


@dataclass(frozen=True)
class HouseDefinition:
    house_id: int
    name: str
    exit: Position
    tiles: tuple[Position, ...] = ()


@dataclass(frozen=True)
class SpawnDefinition:
    name: str
    position: Position
    radius: int = 3
    spawntime: int = 60
    kind: str = "monster"


@dataclass(frozen=True)
class ZoneDefinition:
    name: str
    zone_id: int
    tiles: tuple[Position, ...]
    flags: tuple[str, ...] = ()


@dataclass(frozen=True)
class WaypointDefinition:
    name: str
    position: Position


@dataclass(frozen=True)
class CreatureType:
    name: str
    source_file: str
    look_type: int | None = None


@dataclass
class GameplayP1Report:
    houses: int = 0
    house_tiles: int = 0
    house_exits: int = 0
    monster_spawns: int = 0
    npc_spawns: int = 0
    zones: int = 0
    zone_tiles: int = 0
    waypoints: int = 0
    minimap_tiles: int = 0
    diagnostics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "houses": self.houses,
            "house_tiles": self.house_tiles,
            "house_exits": self.house_exits,
            "monster_spawns": self.monster_spawns,
            "npc_spawns": self.npc_spawns,
            "zones": self.zones,
            "zone_tiles": self.zone_tiles,
            "waypoints": self.waypoints,
            "minimap_tiles": self.minimap_tiles,
            "diagnostics": self.diagnostics,
        }


class CreatureCatalog:
    def __init__(self, monsters: dict[str, CreatureType] | None = None, npcs: dict[str, CreatureType] | None = None) -> None:
        self.monsters = monsters or {}
        self.npcs = npcs or {}

    @classmethod
    def load(cls, root: str | Path = ".") -> "CreatureCatalog":
        base = Path(root)
        monster_dirs = [
            base / "data" / "monster",
            base / "data" / "monsters",
            base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "monster",
            base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "monsters",
        ]
        npc_dirs = [
            base / "data" / "npc",
            base / "data" / "npcs",
            base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "npc",
            base / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows" / "data" / "npcs",
        ]
        return cls(monsters=_load_creatures(monster_dirs), npcs=_load_creatures(npc_dirs))

    def has_monster(self, name: str) -> bool:
        return name.lower() in self.monsters

    def has_npc(self, name: str) -> bool:
        return name.lower() in self.npcs

    def audit(self) -> dict[str, object]:
        return {
            "creature_catalog_ready": True,
            "monster_count": len(self.monsters),
            "npc_count": len(self.npcs),
        }


class GameplayP1System:
    def __init__(self, editable_map: EditableMap, creature_catalog: CreatureCatalog | None = None) -> None:
        self.map = editable_map
        self.creatures = creature_catalog or CreatureCatalog()
        self.houses: dict[int, HouseDefinition] = {}
        self.monster_spawns: list[SpawnDefinition] = []
        self.npc_spawns: list[SpawnDefinition] = []
        self.zones: dict[int, ZoneDefinition] = {}
        self.waypoints: dict[str, WaypointDefinition] = {}

    def add_house(self, house: HouseDefinition) -> None:
        self.houses[house.house_id] = house
        for position in house.tiles:
            tile = self.map.ensure_tile(position)
            tile.house_id = house.house_id
            self.map.modified.add(position)
        exit_tile = self.map.ensure_tile(house.exit)
        exit_tile.house_id = house.house_id
        exit_tile.zones.add("HOUSE_EXIT")
        exit_location = self.map.tiles.location(house.exit, create=True)
        if exit_location is not None:
            exit_location.house_exits.add(house.house_id)
        self.map.modified.add(house.exit)

    def add_spawn(self, spawn: SpawnDefinition) -> None:
        tile = self.map.ensure_tile(spawn.position)
        if spawn.kind == "npc":
            tile.spawn_npcs.append(spawn.name)
            self.npc_spawns.append(spawn)
        else:
            tile.spawn_monsters.append(spawn.name)
            self.monster_spawns.append(spawn)
        self._update_spawn_radius_location_counts(spawn, 1)
        self.map.modified.add(spawn.position)

    def remove_spawn(self, spawn: SpawnDefinition) -> bool:
        collection = self.npc_spawns if spawn.kind == "npc" else self.monster_spawns
        try:
            collection.remove(spawn)
        except ValueError:
            return False
        tile = self.map.get_tile(spawn.position)
        if tile is not None:
            names = tile.spawn_npcs if spawn.kind == "npc" else tile.spawn_monsters
            try:
                names.remove(spawn.name)
            except ValueError:
                pass
        self._update_spawn_radius_location_counts(spawn, -1)
        self.map.mark_dirty(spawn.position, "remove_spawn")
        return True

    def spawns_covering(self, position: Position, kind: str = "monster") -> list[SpawnDefinition]:
        location = self.map.tiles.location(position)
        expected = 0
        if location is not None:
            expected = location.spawn_npc_count if kind == "npc" else location.spawn_monster_count
        if expected <= 0:
            return []
        px, py, pz = position
        collection = self.npc_spawns if kind == "npc" else self.monster_spawns
        return [
            spawn
            for spawn in collection
            if spawn.position[2] == pz
            and abs(spawn.position[0] - px) <= spawn.radius
            and abs(spawn.position[1] - py) <= spawn.radius
        ]

    def overlapping_spawns(self, spawn: SpawnDefinition) -> list[SpawnDefinition]:
        return [
            other
            for other in self.spawns_covering(spawn.position, spawn.kind)
            if other != spawn
        ]

    def add_zone(self, zone: ZoneDefinition) -> None:
        self.zones[zone.zone_id] = zone
        for position in zone.tiles:
            tile = self.map.ensure_tile(position)
            tile.zones.add(zone.name)
            for flag in zone.flags:
                tile.zones.add(flag)
            self.map.modified.add(position)

    def add_waypoint(self, waypoint: WaypointDefinition) -> None:
        previous = self.waypoints.get(waypoint.name)
        if previous is not None:
            old_location = self.map.tiles.location(previous.position)
            if old_location is not None and old_location.waypoint_count > 0:
                old_location.waypoint_count -= 1
                self.map.tiles.release_location(previous.position)
        self.waypoints[waypoint.name] = waypoint
        tile = self.map.ensure_tile(waypoint.position)
        tile.waypoint = waypoint.name
        location = self.map.tiles.location(waypoint.position, create=True)
        if location is not None:
            location.waypoint_count += 1
        self.map.modified.add(waypoint.position)

    def _update_spawn_radius_location_counts(self, spawn: SpawnDefinition, delta: int) -> None:
        """Mirror Map::add/removeSpawn TileLocation radius counters."""
        radius = max(0, int(spawn.radius))
        cx, cy, z = spawn.position
        for y in range(cy - radius, cy + radius + 1):
            for x in range(cx - radius, cx + radius + 1):
                position = (x, y, z)
                location = self.map.tiles.location(position, create=delta > 0)
                if location is None:
                    continue
                if spawn.kind == "npc":
                    location.spawn_npc_count = max(0, location.spawn_npc_count + delta)
                else:
                    location.spawn_monster_count = max(0, location.spawn_monster_count + delta)
                if delta < 0:
                    self.map.tiles.release_location(position)

    def minimap_index(self) -> dict[Position, int]:
        colors: dict[Position, int] = {}
        for position, tile in self.map.tiles.items():
            if "PZ" in tile.zones or "PROTECTION_ZONE" in tile.zones:
                colors[position] = 0x66
            elif tile.house_id is not None:
                colors[position] = 0xD2
            elif tile.spawn_monsters or tile.spawn_npcs:
                colors[position] = 0xB4
            elif tile.ground:
                colors[position] = tile.ground % 256
        return colors

    def validate(self) -> GameplayP1Report:
        report = GameplayP1Report(
            houses=len(self.houses),
            house_tiles=sum(len(house.tiles) for house in self.houses.values()),
            house_exits=len(self.houses),
            monster_spawns=len(self.monster_spawns),
            npc_spawns=len(self.npc_spawns),
            zones=len(self.zones),
            zone_tiles=sum(len(zone.tiles) for zone in self.zones.values()),
            waypoints=len(self.waypoints),
            minimap_tiles=len(self.minimap_index()),
        )
        for spawn in self.monster_spawns:
            if self.creatures.monsters and not self.creatures.has_monster(spawn.name):
                report.diagnostics.append(f"unknown monster: {spawn.name}")
        for spawn in self.npc_spawns:
            if self.creatures.npcs and not self.creatures.has_npc(spawn.name):
                report.diagnostics.append(f"unknown npc: {spawn.name}")
        return report

    def audit(self) -> dict[str, object]:
        report = self.validate()
        return {
            "gameplay_p1_ready": True,
            "radius_location_counts": True,
            "overlap_detection": True,
            "source_coverage": [
                "house.cpp/h",
                "house_brush.cpp",
                "house_exit_brush.cpp",
                "spawn_monster.cpp/h",
                "spawn_npc.cpp/h",
                "zones.cpp/h",
                "waypoints.cpp/h",
                "monsters.cpp/h",
                "npcs.cpp/h",
                "iominimap.cpp/h",
                "minimap_window.cpp",
            ],
            "creature_catalog": self.creatures.audit(),
            "report": report.to_dict(),
        }


def _load_creatures(paths: Iterable[Path]) -> dict[str, CreatureType]:
    out: dict[str, CreatureType] = {}
    for root in paths:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.xml")):
            creature = _parse_creature(path)
            if creature:
                out[creature.name.lower()] = creature
    return out


def _parse_creature(path: Path) -> CreatureType | None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return None
    name = root.get("name") or root.findtext("name") or path.stem
    look_type = None
    look = root.find(".//look")
    if look is not None:
        raw = look.get("type") or look.get("looktype")
        if raw and str(raw).isdigit():
            look_type = int(raw)
    return CreatureType(name=name, source_file=str(path), look_type=look_type)
