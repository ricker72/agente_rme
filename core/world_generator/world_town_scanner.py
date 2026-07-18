"""One-pass, cacheable semantic scanner for towns in the canonical world OTBM."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from core.otbm.otbm_importer import OTBMAttributeReader, OTBMNode, OTBMNodeReader
from core.world_generator.reference_map_corpus import ReferenceMapCorpusAnalyzer


SCANNER_VERSION = 2
FLOORS = tuple(range(16))
EXCLUDED_TOWNS = {"krailos"}


class WorldTownScanner:
    """Build prompt-ready town knowledge without retaining world geometry."""

    def __init__(self, root: str | Path = ".", *, radius: int = 64) -> None:
        self.root = Path(root).resolve()
        self.radius = max(16, int(radius))
        self.world_path = self.root / "projects" / "world" / "world.otbm"
        self.cache_path = self.root / "exports" / "planner_knowledge" / "WORLD_TOWN_SCAN_REPORT.json"
        self.reference = ReferenceMapCorpusAnalyzer(self.root)
        self.item_semantics = self._load_item_semantics()

    def scan_cached(self, *, force: bool = False) -> dict[str, Any]:
        source_sha256 = self._sha256(self.world_path)
        if not force and self.cache_path.is_file():
            try:
                cached = json.loads(self.cache_path.read_text(encoding="utf-8"))
                if (
                    cached.get("scanner_version") == SCANNER_VERSION
                    and cached.get("world_sha256") == source_sha256
                    and cached.get("radius") == self.radius
                    and cached.get("status") == "PASS"
                ):
                    changed = self._normalize_report(cached)
                    if changed:
                        temporary = self.cache_path.with_suffix(".json.tmp")
                        temporary.write_text(json.dumps(cached, indent=2, sort_keys=True), encoding="utf-8")
                        temporary.replace(self.cache_path)
                    return cached
            except (OSError, UnicodeError, json.JSONDecodeError):
                pass
        report = self.scan(source_sha256=source_sha256)
        if report["status"] == "PASS":
            self._normalize_report(report)
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.cache_path.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
            temporary.replace(self.cache_path)
        return report

    def scan(self, *, source_sha256: str | None = None) -> dict[str, Any]:
        anchors = self._anchors()
        states = {name: self._new_state(anchor) for name, anchor in anchors.items()}
        self._scan_otbm(anchors, states)
        houses = self._scan_houses(anchors)
        spawns = self._scan_monsters(anchors)
        npcs = self._scan_npcs(anchors)
        towns = {}
        for name, state in sorted(states.items()):
            towns[name] = self._finalize_town(
                name,
                state,
                houses.get(name, []),
                spawns.get(name, {}),
                npcs.get(name, {}),
            )
        return {
            "stage": "World Town Scanner",
            "status": "PASS" if towns else "BLOCKED",
            "scanner_version": SCANNER_VERSION,
            "world_sha256": source_sha256 or self._sha256(self.world_path),
            "world_bytes": self.world_path.stat().st_size,
            "radius": self.radius,
            "floors_examined": list(FLOORS),
            "excluded_towns": sorted(EXCLUDED_TOWNS),
            "town_count": len(towns),
            "towns": towns,
            "policy": {
                "scan_world_once_per_hash": True,
                "runtime_queries_use_sqlite": True,
                "coordinates_persisted": False,
                "tile_stacks_persisted": False,
                "exact_chunks_persisted": False,
                "structure_labels_require_evidence": True,
            },
        }

    @staticmethod
    def _normalize_report(report: dict[str, Any]) -> bool:
        changed = False
        for town in report.get("towns", {}).values():
            official_house_count = int(town.get("houses", {}).get("count", 0))
            counts = town.setdefault("structure_counts", {})
            if counts.get("house") != official_house_count:
                counts["house"] = official_house_count
                changed = True
        return changed

    def _scan_otbm(self, anchors: dict[str, dict[str, Any]], states: dict[str, dict[str, Any]]) -> None:
        bucket_size = max(32, self.radius * 2)
        buckets: dict[tuple[int, int], list[tuple[str, int, int]]] = defaultdict(list)
        for name, anchor in anchors.items():
            cx, cy = int(anchor["x"]), int(anchor["y"])
            for bx in range((cx - self.radius) // bucket_size, (cx + self.radius) // bucket_size + 1):
                for by in range((cy - self.radius) // bucket_size, (cy + self.radius) // bucket_size + 1):
                    buckets[(bx, by)].append((name, cx, cy))

        area: tuple[int, int, int] | None = None
        current: dict[str, Any] | None = None
        tile_depth = -1

        def finish() -> None:
            nonlocal current
            if current is not None:
                self._consume_tile(states[current["town"]], current)
                current = None

        with OTBMNodeReader(self.world_path) as reader:
            def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
                nonlocal area, current, tile_depth
                if node.node_type == 0x04:
                    finish()
                    area = OTBMAttributeReader.parse_tile_area(node.attrs)
                elif node.node_type in (0x05, 0x0E) and area is not None:
                    finish()
                    tile = OTBMAttributeReader.parse_tile(node.attrs, *area)
                    z = int(tile["z"])
                    if z not in FLOORS:
                        return
                    town = self._nearest_from_bucket(
                        int(tile["x"]), int(tile["y"]), buckets, bucket_size, self.radius
                    )
                    if town is None:
                        return
                    current = {
                        "town": town,
                        "x": int(tile["x"]),
                        "y": int(tile["y"]),
                        "z": z,
                        "items": self._inline_items(node.attrs, house=node.node_type == 0x0E),
                        "house_id": (
                            int.from_bytes(node.attrs[2:6], "little")
                            if node.node_type == 0x0E and len(node.attrs) >= 6 else None
                        ),
                    }
                    tile_depth = node.depth
                elif node.node_type == 0x06 and current is not None and node.depth == tile_depth + 1:
                    if len(node.attrs) >= 2:
                        current["items"].append(int.from_bytes(node.attrs[:2], "little"))

            reader.traverse(on_node, max_nodes=None, max_bytes=None)
        finish()

    def _consume_tile(self, state: dict[str, Any], tile: dict[str, Any]) -> None:
        floor = state["floors"][tile["z"]]
        floor["tile_count"] += 1
        floor["stack_sizes"][len(tile["items"])] += 1
        floor["item_counts"].update(tile["items"])
        if tile["house_id"] is not None:
            floor["house_ids"].add(tile["house_id"])
            state["house_footprints"][tile["house_id"]][tile["z"]].add((tile["x"], tile["y"]))
        roles: set[str] = set()
        names: list[str] = []
        for item_id in tile["items"]:
            semantics = self.item_semantics.get(item_id, {})
            roles.update(str(role).upper() for role in semantics.get("roles", ()))
            names.append(str(semantics.get("name", "")).lower())
        floor["role_counts"].update(roles)
        position = (tile["x"], tile["y"])
        features = self._semantic_features(roles, names)
        for feature in features:
            floor["feature_positions"][feature].add(position)

        ground = next(
            (item_id for item_id in tile["items"] if self.reference._is_ground(item_id)),
            None,
        )
        border_ids = {
            item_id for item_id in tile["items"]
            if "border" in {kind for kind, _ in self.reference.brush_by_item.get(item_id, ())}
            or "border" in self.reference.category_by_item.get(item_id, ())
        }
        if ground is not None:
            floor["ground_positions"][position] = ground
            for neighbor in ((position[0] - 1, position[1]), (position[0], position[1] - 1)):
                for border_id in floor["border_positions"].get(neighbor, ()):
                    floor["border_mixes"][(ground, border_id)] += 1
        if border_ids:
            floor["border_positions"][position].update(border_ids)
            neighbor_grounds = {
                value for neighbor in (
                    position, (position[0] - 1, position[1]), (position[0], position[1] - 1)
                ) if (value := floor["ground_positions"].get(neighbor)) is not None
            }
            for ground_id in neighbor_grounds:
                for border_id in border_ids:
                    floor["border_mixes"][(ground_id, border_id)] += 1

    def _finalize_town(
        self,
        name: str,
        state: dict[str, Any],
        houses: list[dict[str, Any]],
        spawn_data: dict[str, Any],
        npc_data: dict[str, Any],
    ) -> dict[str, Any]:
        floors = {}
        structures = []
        for z in FLOORS:
            floor = state["floors"][z]
            usage = self.reference._material_rows(
                floor["item_counts"], floor["tile_count"], len(floor["item_counts"])
            )
            feature_summary = {}
            for kind, positions in floor["feature_positions"].items():
                clusters = self._cluster_dimensions(positions, distance=2)
                feature_summary[kind] = {
                    "evidence_tiles": len(positions),
                    "room_candidates": clusters,
                }
                structures.extend(
                    {
                        "kind": kind,
                        "min_floor": z,
                        "max_floor": z,
                        **cluster,
                        "confidence": self._feature_confidence(kind, cluster["evidence_count"]),
                        "evidence": "official item roles/names or OTBM house tile",
                    }
                    for cluster in clusters
                )
            floors[str(z)] = {
                "floor": z,
                "tile_count": floor["tile_count"],
                "material_count": len(usage),
                "materials": usage,
                "grounds": self.reference._materials_by_role(usage, "ground"),
                "nature": self.reference._materials_by_role(usage, "nature"),
                "borders": self.reference._materials_by_role(usage, "border"),
                "walls": self.reference._materials_by_role(usage, "wall"),
                "doodads": self.reference._materials_by_role(usage, "doodad"),
                "role_counts": dict(sorted(floor["role_counts"].items())),
                "stack_size_histogram": {str(k): v for k, v in sorted(floor["stack_sizes"].items())},
                "house_tile_id_count": len(floor["house_ids"]),
                "semantic_features": feature_summary,
                "border_mixes": [
                    {"ground_id": ground, "border_id": border, "count": count}
                    for (ground, border), count in floor["border_mixes"].most_common()
                ],
            }
        house_profile = self._house_profile(houses, state["house_footprints"])
        structures.extend(house_profile["structures"])
        structures.extend(spawn_data.get("hunt_zones", ()))
        return {
            "town_id": state["anchor"]["id"],
            "town": name,
            "anchor_floor": state["anchor"]["z"],
            "floors_examined": list(FLOORS),
            "content_floors": [z for z in FLOORS if floors[str(z)]["tile_count"]],
            "floors": floors,
            "houses": house_profile,
            "spawns": spawn_data,
            "npcs": npc_data,
            "structures": structures,
            "structure_counts": {
                kind: Counter(row["kind"] for row in structures).get(kind, 0)
                for kind in ("house", "temple", "depot", "hunt", "quest_room", "boss_room", "reward_room")
            },
            "classification_policy": {
                "house": "OTBM house tiles + world-house.xml townid",
                "temple": "TEMPLE role or explicit temple/shrine item name",
                "depot": "DEPOT role or explicit depot/locker item name",
                "hunt": "world-monster.xml spawn clusters",
                "quest_room": "QUEST_OBJECT role or explicit quest item name",
                "boss_room": "explicit boss item/monster evidence only",
                "reward_room": "explicit reward chest/box/shrine evidence",
            },
        }

    def _scan_houses(self, anchors: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        by_id = {int(anchor["id"]): name for name, anchor in anchors.items()}
        result: dict[str, list[dict[str, Any]]] = defaultdict(list)
        path = self.root / "projects" / "world" / "world-house.xml"
        if not path.is_file():
            return result
        for element in ET.parse(path).getroot().iter("house"):
            town = by_id.get(self._integer(element.attrib.get("townid")))
            if town is None:
                continue
            result[town].append({
                "name": element.attrib.get("name", ""),
                "house_id": self._integer(element.attrib.get("houseid")),
                "entry_floor": self._integer(element.attrib.get("entryz")),
                "size": self._integer(element.attrib.get("size")),
                "beds": self._integer(element.attrib.get("beds")),
                "guildhall": element.attrib.get("guildhall", "false").lower() == "true",
            })
        return result

    def _scan_monsters(self, anchors: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"spawn_groups": 0, "monster_count": 0, "floors": Counter(), "monsters": Counter(),
                     "boss_evidence": Counter(), "hunt_cells": defaultdict(lambda: {
                         "groups": 0, "monsters": Counter(), "min_x": 65535, "max_x": 0,
                         "min_y": 65535, "max_y": 0, "floor": 0,
                     })}
        )
        path = self.root / "projects" / "world" / "world-monster.xml"
        if not path.is_file():
            return result
        for group in ET.parse(path).getroot().iter("monster"):
            if "centerx" not in group.attrib:
                continue
            x = self._integer(group.attrib.get("centerx"))
            y = self._integer(group.attrib.get("centery"))
            z = self._integer(group.attrib.get("centerz"))
            town = self._nearest_anchor(x, y, anchors, self.radius * 3)
            if town is None or z not in FLOORS:
                continue
            monsters = [child.attrib.get("name", "") for child in list(group) if child.tag == "monster"]
            entry = result[town]
            entry["spawn_groups"] += 1
            entry["monster_count"] += len(monsters)
            entry["floors"][z] += 1
            entry["monsters"].update(monsters)
            entry["boss_evidence"].update(name for name in monsters if "boss" in name.lower())
            cell = entry["hunt_cells"][(z, x // 32, y // 32)]
            cell["groups"] += 1
            cell["monsters"].update(monsters)
            cell["min_x"], cell["max_x"] = min(cell["min_x"], x), max(cell["max_x"], x)
            cell["min_y"], cell["max_y"] = min(cell["min_y"], y), max(cell["max_y"], y)
            cell["floor"] = z
        finalized = {}
        for town, entry in result.items():
            hunt_zones = self._merge_hunt_cells(entry.pop("hunt_cells"))
            finalized[town] = {
                "spawn_groups": entry["spawn_groups"],
                "monster_count": entry["monster_count"],
                "floors": {str(k): v for k, v in sorted(entry["floors"].items())},
                "monster_mix": dict(entry["monsters"].most_common(64)),
                "boss_evidence": dict(entry["boss_evidence"]),
                "hunt_zones": hunt_zones,
            }
        return finalized

    def _scan_npcs(self, anchors: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"spawn_groups": 0, "floors": Counter(), "names": Counter()}
        )
        path = self.root / "projects" / "world" / "world-npc.xml"
        if not path.is_file():
            return result
        for group in ET.parse(path).getroot().iter("npc"):
            if "centerx" not in group.attrib:
                continue
            x = self._integer(group.attrib.get("centerx"))
            y = self._integer(group.attrib.get("centery"))
            z = self._integer(group.attrib.get("centerz"))
            town = self._nearest_anchor(x, y, anchors, self.radius * 2)
            if town is None or z not in FLOORS:
                continue
            entry = result[town]
            entry["spawn_groups"] += 1
            entry["floors"][z] += 1
            entry["names"].update(
                child.attrib.get("name", "") for child in list(group) if child.tag == "npc"
            )
        return {
            town: {
                "spawn_groups": row["spawn_groups"],
                "floors": {str(k): v for k, v in sorted(row["floors"].items())},
                "names": dict(row["names"].most_common()),
            }
            for town, row in result.items()
        }

    def _anchors(self) -> dict[str, dict[str, Any]]:
        path = self.root / "exports" / "planner_visual_memory" / "WORLD_NAMED_ANCHORS.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return {
            str(row["name"]): {
                "id": int(row["id"]), "x": int(row["x"]), "y": int(row["y"]), "z": int(row["z"]),
            }
            for row in payload.get("towns", ())
            if str(row.get("name", "")).lower() not in EXCLUDED_TOWNS
        }

    def _load_item_semantics(self) -> dict[int, dict[str, Any]]:
        path = self.root / "APPEARANCE_ITEM_CATALOG.json"
        payload = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
        return {
            int(raw_id): {"name": row.get("name", ""), "roles": row.get("roles", ())}
            for raw_id, row in payload.items()
            if str(raw_id).isdigit() and isinstance(row, dict)
        }

    @staticmethod
    def _semantic_features(roles: set[str], names: list[str]) -> set[str]:
        joined = " ".join(names)
        features = set()
        if "TEMPLE" in roles or any(word in joined for word in ("temple", "shrine")):
            features.add("temple")
        if "DEPOT" in roles or any(word in joined for word in ("depot", "locker")):
            features.add("depot")
        if "QUEST_OBJECT" in roles or "quest " in joined:
            features.add("quest_room")
        if any(word in joined for word in ("reward chest", "reward box", "reward shrine", "reward container")):
            features.add("reward_room")
        if "boss" in joined:
            features.add("boss_room")
        return features

    @staticmethod
    def _new_state(anchor: dict[str, Any]) -> dict[str, Any]:
        return {
            "anchor": anchor,
            "house_footprints": defaultdict(lambda: defaultdict(set)),
            "floors": {
                z: {
                    "tile_count": 0,
                    "item_counts": Counter(),
                    "stack_sizes": Counter(),
                    "role_counts": Counter(),
                    "house_ids": set(),
                    "feature_positions": defaultdict(set),
                    "ground_positions": {},
                    "border_positions": defaultdict(set),
                    "border_mixes": Counter(),
                }
                for z in FLOORS
            },
        }

    @staticmethod
    def _house_profile(
        houses: list[dict[str, Any]],
        footprints: dict[int, dict[int, set[tuple[int, int]]]],
    ) -> dict[str, Any]:
        sizes = [row["size"] for row in houses if row["size"] > 0]
        floors = Counter(row["entry_floor"] for row in houses)
        metadata = {row["house_id"]: row for row in houses}
        structures = []
        for house_id, by_floor in footprints.items():
            positions = [position for values in by_floor.values() for position in values]
            if not positions:
                continue
            row = metadata.get(house_id, {})
            structures.append({
                "kind": "house",
                "min_floor": min(by_floor),
                "max_floor": max(by_floor),
                "floor_count": len(by_floor),
                "width": max(x for x, _ in positions) - min(x for x, _ in positions) + 1,
                "height": max(y for _, y in positions) - min(y for _, y in positions) + 1,
                "evidence_count": len(positions),
                "confidence": 1.0,
                "house_id": house_id,
                "name": row.get("name", ""),
                "declared_size": row.get("size", 0),
                "beds": row.get("beds", 0),
                "evidence": "OTBM HOUSETILE house_id + world-house.xml townid",
            })
        return {
            "count": len(houses),
            "guildhalls": sum(row["guildhall"] for row in houses),
            "total_tiles": sum(sizes),
            "min_size": min(sizes) if sizes else 0,
            "max_size": max(sizes) if sizes else 0,
            "average_size": round(sum(sizes) / len(sizes), 3) if sizes else 0.0,
            "entry_floor_counts": {str(k): v for k, v in sorted(floors.items())},
            "structures": structures,
        }

    @staticmethod
    def _cluster_dimensions(positions: set[tuple[int, int]], *, distance: int) -> list[dict[str, int]]:
        if not positions:
            return []
        remaining = set(positions)
        components = []
        while remaining:
            start = remaining.pop()
            component = {start}
            queue = [start]
            while queue:
                x, y = queue.pop()
                for dx in range(-distance, distance + 1):
                    for dy in range(-distance, distance + 1):
                        neighbor = (x + dx, y + dy)
                        if neighbor in remaining:
                            remaining.remove(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
            components.append(component)
        return [
            {
                "width": max(x for x, _ in points) - min(x for x, _ in points) + 1,
                "height": max(y for _, y in points) - min(y for _, y in points) + 1,
                "evidence_count": len(points),
            }
            for points in components
        ]

    @staticmethod
    def _merge_hunt_cells(cells: dict[tuple[int, int, int], dict[str, Any]]) -> list[dict[str, Any]]:
        remaining = set(cells)
        components = []
        while remaining:
            start = remaining.pop()
            component = {start}
            queue = [start]
            while queue:
                z, bx, by = queue.pop()
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        neighbor = (z, bx + dx, by + dy)
                        if neighbor in remaining:
                            remaining.remove(neighbor)
                            component.add(neighbor)
                            queue.append(neighbor)
            components.append(component)
        result = []
        for component in components:
            rows = [cells[key] for key in component]
            monsters = Counter()
            for row in rows:
                monsters.update(row["monsters"])
            groups = sum(row["groups"] for row in rows)
            floor = rows[0]["floor"]
            result.append({
                "kind": "hunt",
                "min_floor": floor,
                "max_floor": floor,
                "width": max(row["max_x"] for row in rows) - min(row["min_x"] for row in rows) + 1,
                "height": max(row["max_y"] for row in rows) - min(row["min_y"] for row in rows) + 1,
                "evidence_count": groups,
                "confidence": min(0.98, 0.65 + groups / 50),
                "monster_mix": dict(monsters.most_common(24)),
                "evidence": "connected world-monster.xml spawn cells",
            })
        return result

    @staticmethod
    def _feature_confidence(kind: str, count: int) -> float:
        base = {"house": 0.9, "depot": 0.9, "temple": 0.82, "quest_room": 0.78,
                "reward_room": 0.9, "boss_room": 0.72}.get(kind, 0.65)
        return round(min(0.99, base + min(count, 20) / 200), 3)

    @staticmethod
    def _nearest_anchor(
        x: int, y: int, anchors: dict[str, dict[str, Any]], radius: int
    ) -> str | None:
        candidates = [
            (abs(x - int(anchor["x"])) + abs(y - int(anchor["y"])), name)
            for name, anchor in anchors.items()
            if abs(x - int(anchor["x"])) <= radius and abs(y - int(anchor["y"])) <= radius
        ]
        return min(candidates)[1] if candidates else None

    @staticmethod
    def _nearest_from_bucket(
        x: int,
        y: int,
        buckets: dict[tuple[int, int], list[tuple[str, int, int]]],
        bucket_size: int,
        radius: int,
    ) -> str | None:
        candidates = [
            (abs(x - cx) + abs(y - cy), name)
            for name, cx, cy in buckets.get((x // bucket_size, y // bucket_size), ())
            if abs(x - cx) <= radius and abs(y - cy) <= radius
        ]
        return min(candidates)[1] if candidates else None

    @staticmethod
    def _inline_items(attrs: bytes, *, house: bool) -> list[int]:
        offset = 6 if house else 2
        result = []
        while offset < len(attrs):
            attribute = attrs[offset]
            offset += 1
            if attribute == 0x03 and offset + 4 <= len(attrs):
                offset += 4
            elif attribute == 0x09 and offset + 2 <= len(attrs):
                result.append(int.from_bytes(attrs[offset : offset + 2], "little"))
                offset += 2
            else:
                break
        return result

    @staticmethod
    def _integer(value: str | None) -> int:
        try:
            return int(value or 0)
        except ValueError:
            return 0

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


__all__ = ["WorldTownScanner", "SCANNER_VERSION", "FLOORS", "EXCLUDED_TOWNS"]
