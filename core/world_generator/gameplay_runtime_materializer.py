from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from core.world_generator.otbm_world.model import OtbmItem, OtbmTile, OtbmWorldModel


@dataclass(frozen=True)
class RuntimeHouse:
    house_id: int
    name: str
    exit: tuple[int, int, int]
    tiles: tuple[tuple[int, int, int], ...]
    town_id: int = 1


@dataclass(frozen=True)
class RuntimeSpawn:
    name: str
    position: tuple[int, int, int]
    radius: int
    spawntime: int
    kind: str


@dataclass(frozen=True)
class RuntimeZone:
    zone_id: int
    name: str
    tiles: tuple[tuple[int, int, int], ...] = ()
    tile_flags: int = 0


@dataclass(frozen=True)
class GameplayRuntimeResult:
    model: OtbmWorldModel
    houses_xml: str
    monsters_xml: str
    npcs_xml: str
    zones_xml: str
    report: dict[str, Any]

    def write_sidecars(self, root: str | Path, stem: str = "") -> None:
        base = Path(root)
        prefix = f"{stem}-" if stem else ""
        _write(base / f"{prefix}house.xml", self.houses_xml)
        _write(base / f"{prefix}monster.xml", self.monsters_xml)
        _write(base / f"{prefix}npc.xml", self.npcs_xml)
        _write(base / f"{prefix}zones.xml", self.zones_xml)


class GameplayRuntimeMaterializer:
    def materialize(
        self,
        model: OtbmWorldModel,
        *,
        houses: Iterable[RuntimeHouse] = (),
        spawns: Iterable[RuntimeSpawn] = (),
        zones: Iterable[RuntimeZone] = (),
        connection_routes: Iterable[Iterable[tuple[int, int, int]]] = (),
        route_ground_id: int = 7756,
    ) -> GameplayRuntimeResult:
        houses = tuple(houses)
        spawns = tuple(spawns)
        zones = tuple(zones)
        model, repaired_route_tiles = _carve_runtime_routes(
            model,
            tuple(tuple(route) for route in connection_routes),
            tuple(spawn.position for spawn in spawns if spawn.kind == "monster"),
            route_ground_id,
        )
        house_by_position = {
            position: house.house_id
            for house in houses
            for position in house.tiles
        }
        zone_flags = {
            position: _combined_zone_flags(position, zones)
            for zone in zones
            for position in zone.tiles
        }
        runtime_tiles: list[OtbmTile] = []
        for tile in model.tiles:
            position = (tile.x, tile.y, tile.z)
            attributes = dict(tile.attributes)
            if zone_flags.get(position):
                attributes["tile_flags"] = int(attributes.get("tile_flags", 0)) | zone_flags[position]
            runtime_tiles.append(
                OtbmTile(
                    tile.x,
                    tile.y,
                    tile.z,
                    tile.items,
                    attributes,
                    house_by_position.get(position),
                )
            )
        tiles = tuple(runtime_tiles)
        tile_positions = {(tile.x, tile.y, tile.z) for tile in tiles}
        diagnostics: list[str] = []
        for house in houses:
            if not house.tiles:
                diagnostics.append(f"house {house.house_id} has no tiles")
            if house.exit not in tile_positions:
                diagnostics.append(f"house {house.house_id} exit has no map tile")
        for spawn in spawns:
            if spawn.position not in tile_positions:
                diagnostics.append(f"{spawn.kind} spawn {spawn.name} has no map tile")
            if spawn.radius < 1:
                diagnostics.append(f"{spawn.kind} spawn {spawn.name} has invalid radius")
            if not spawn.name.strip():
                diagnostics.append(f"{spawn.kind} spawn has empty creature name")

        runtime_metadata = {**model.metadata, "gameplay_runtime_materialized": not diagnostics}
        if any(spawn.kind == "monster" for spawn in spawns):
            runtime_metadata.setdefault("spawn_monster_file", "spawns.xml")
        if any(spawn.kind == "npc" for spawn in spawns):
            runtime_metadata.setdefault("spawn_npc_file", "npc.xml")
        if houses:
            runtime_metadata.setdefault("house_file", "houses.xml")
        if zones:
            runtime_metadata.setdefault("zone_file", "zones.xml")
        runtime_model = OtbmWorldModel(
            width=model.width,
            height=model.height,
            tiles=tiles,
            metadata=runtime_metadata,
            towns=model.towns,
            waypoints=model.waypoints,
        )
        house_tile_count = sum(tile.house_id is not None for tile in tiles)
        report = {
            "stage": "Canary Gameplay Runtime Materialization",
            "status": "PASS" if not diagnostics else "BLOCKED",
            "houses": len(houses),
            "house_tiles": house_tile_count,
            "monster_spawns": sum(spawn.kind == "monster" for spawn in spawns),
            "npc_spawns": sum(spawn.kind == "npc" for spawn in spawns),
            "zones": len(zones),
            "zone_tiles": sum(bool(tile.attributes.get("tile_flags")) for tile in tiles),
            "runtime_route_tiles": repaired_route_tiles,
            "diagnostics": diagnostics,
        }
        return GameplayRuntimeResult(
            runtime_model,
            _houses_xml(houses),
            _spawns_xml(spawns, "monster"),
            _spawns_xml(spawns, "npc"),
            _zones_xml(zones),
            report,
        )


def runtime_definitions_from_necro(
    footprints: Mapping[str, list[list[int]]],
    entity_plan: Mapping[str, Any],
    hunt_blueprint: Mapping[str, Any],
    *,
    floor: int = 7,
) -> tuple[tuple[RuntimeHouse, ...], tuple[RuntimeSpawn, ...], tuple[RuntimeZone, ...]]:
    houses: list[RuntimeHouse] = []
    names = ("house_nw_1", "house_nw_2", "house_ne_1", "house_e_1", "house_s_1", "house_sw_1")
    for house_id, name in enumerate(names, start=1):
        tiles = tuple((int(x), int(y), floor) for x, y in footprints.get(name, []))
        if not tiles:
            continue
        exit_position = min(tiles, key=lambda position: (abs(position[0] - 1000) + abs(position[1] - 1000), position))
        houses.append(RuntimeHouse(house_id, name, exit_position, tiles))

    spawns: list[RuntimeSpawn] = []
    for npc in entity_plan.get("npcs", []):
        spawns.append(RuntimeSpawn(str(npc["name"]), _position(npc["position"]), 1, 60, "npc"))
    for spawn in entity_plan.get("spawns", []):
        spawns.append(RuntimeSpawn(str(spawn["monster"]), _position(spawn["position"]), int(spawn.get("radius") or 3), int(spawn.get("spawntime") or 60), "monster"))
    boss = entity_plan.get("boss") or {}
    if boss.get("position"):
        spawns.append(RuntimeSpawn(str(boss.get("monster") or "Necro Pattern Warden"), _position(boss["position"]), 5, 900, "monster"))

    pz_tiles = tuple(
        (int(x), int(y), floor)
        for name in ("temple", "central_plaza")
        for x, y in footprints.get(name, [])
    )
    zones = [RuntimeZone(1, "Protection Zone", pz_tiles, 0x0001)]
    zones.extend(RuntimeZone(index, str(zone["name"])) for index, zone in enumerate(hunt_blueprint.get("zones", []), start=2))
    return tuple(houses), tuple(spawns), tuple(zones)


def _houses_xml(houses: tuple[RuntimeHouse, ...]) -> str:
    root = ET.Element("houses")
    for house in houses:
        x, y, z = house.exit
        ET.SubElement(root, "house", {"name": house.name, "houseid": str(house.house_id), "entryx": str(x), "entryy": str(y), "entryz": str(z), "rent": "0", "townid": str(house.town_id), "size": str(len(house.tiles)), "clientid": "0", "beds": "0"})
    return _xml(root)


def _spawns_xml(spawns: tuple[RuntimeSpawn, ...], kind: str) -> str:
    root = ET.Element("monsters" if kind == "monster" else "npcs")
    for spawn in (value for value in spawns if value.kind == kind):
        x, y, z = spawn.position
        outer = ET.SubElement(root, kind, {"centerx": str(x), "centery": str(y), "centerz": str(z), "radius": str(spawn.radius)})
        ET.SubElement(outer, kind, {"name": spawn.name, "x": "0", "y": "0", "z": str(z), "spawntime": str(spawn.spawntime), "direction": "0"})
    return _xml(root)


def _zones_xml(zones: tuple[RuntimeZone, ...]) -> str:
    root = ET.Element("zones")
    for zone in zones:
        ET.SubElement(root, "zone", {"name": zone.name, "zoneid": str(zone.zone_id)})
    return _xml(root)


def _position(value: Iterable[Any]) -> tuple[int, int, int]:
    x, y, z = value
    return int(x), int(y), int(z)


def _xml(root: ET.Element) -> str:
    ET.indent(root)
    return '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode") + "\n"


def _write(path: Path, value: str) -> None:
    path.write_text(value, encoding="utf-8")


def _combined_zone_flags(position: tuple[int, int, int], zones: tuple[RuntimeZone, ...]) -> int:
    flags = 0
    for zone in zones:
        if position in zone.tiles:
            flags |= int(zone.tile_flags)
    return flags


def _carve_runtime_routes(
    model: OtbmWorldModel,
    routes: tuple[tuple[tuple[int, int, int], ...], ...],
    targets: tuple[tuple[int, int, int], ...],
    ground_id: int,
) -> tuple[OtbmWorldModel, int]:
    if not routes:
        return model, 0
    network: set[tuple[int, int, int]] = set()
    for route in routes:
        for start, end in zip(route, route[1:]):
            network.update(_line(start, end))
    for target in targets:
        same_floor = [position for position in network if position[2] == target[2]]
        if same_floor:
            nearest = min(same_floor, key=lambda position: abs(position[0] - target[0]) + abs(position[1] - target[1]))
            network.update(_line(nearest, target))
    widened = {
        (x + dx, y + dy, z)
        for x, y, z in network
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
    }
    repaired = 0
    tiles: list[OtbmTile] = []
    existing_positions = {(tile.x, tile.y, tile.z) for tile in model.tiles}
    for tile in model.tiles:
        position = (tile.x, tile.y, tile.z)
        if position not in widened:
            tiles.append(tile)
            continue
        source = next((item for item in tile.items if item.layer == "ground"), tile.items[0] if tile.items else None)
        ground = OtbmItem(ground_id, "ground", f"runtime_route:{tile.x}:{tile.y}:{tile.z}")
        if source is not None and source.item_id == ground_id and len(tile.items) == 1:
            tiles.append(tile)
            continue
        tiles.append(OtbmTile(tile.x, tile.y, tile.z, (ground,), tile.attributes, tile.house_id))
        repaired += 1
    for x, y, z in sorted(widened - existing_positions):
        tiles.append(
            OtbmTile(
                x,
                y,
                z,
                (OtbmItem(ground_id, "ground", f"runtime_route:{x}:{y}:{z}"),),
            )
        )
        repaired += 1
    tiles.sort(key=lambda tile: (tile.z, tile.x, tile.y))
    return OtbmWorldModel(model.width, model.height, tuple(tiles), model.metadata, model.towns, model.waypoints), repaired


def _line(start: tuple[int, int, int], end: tuple[int, int, int]) -> set[tuple[int, int, int]]:
    x1, y1, z = start
    x2, y2, _ = end
    dx = abs(x2 - x1)
    dy = -abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    error = dx + dy
    points: set[tuple[int, int, int]] = set()
    while True:
        points.add((x1, y1, z))
        if x1 == x2 and y1 == y2:
            return points
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x1 += sx
        if doubled <= dx:
            error += dx
            y1 += sy
