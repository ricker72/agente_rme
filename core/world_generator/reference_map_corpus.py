"""Abstract OTBM reference-corpus learning without retaining source layouts."""

from __future__ import annotations

import hashlib
import json
import math
import struct
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from core.opentibia.assets.appearance_dat_flags import AppearanceDatFlagExtractor
from core.otbm.otbm_importer import OTBMAttributeReader, OTBMNode, OTBMNodeReader
from core.world_generator.rme_brush_engine import RMEBrushEngine
from core.world_generator.rme_materials_necro_v5 import classify_items, load_material_catalog
from rme_rendering.rme_mapcolors import rme_minimap_color_to_rgb


class ReferenceMapCorpusAnalyzer:
    """Learn materials and compositional grammar, never reusable tile chunks."""

    def __init__(
        self,
        root: str | Path = ".",
        *,
        automap_colors: dict[int, int] | None = None,
    ) -> None:
        self.root = Path(root).resolve()
        self.corpus_root = self.root / "projects" / "Mapas Referencia"
        self.classification = classify_items(load_material_catalog(self.root))
        self.brush_engine = RMEBrushEngine.load(self.root, self.classification)
        self.category_by_item = self._category_index()
        self.brush_by_item = self._brush_index()
        self.family_members = self._family_members()
        self.vertical_connector_by_item = self._vertical_connector_index()
        self.automap_colors = automap_colors if automap_colors is not None else self._load_automap_colors()

    def reference_paths(self) -> list[Path]:
        return sorted(self.corpus_root.rglob("*.otbm"))

    def analyze_path(self, path: str | Path) -> dict[str, Any]:
        candidate = Path(path).resolve()
        if not candidate.is_relative_to(self.corpus_root):
            raise ValueError("Reference map must be inside projects/Mapas Referencia")
        if candidate.suffix.casefold() != ".otbm" or not candidate.is_file():
            raise ValueError(f"Reference OTBM does not exist: {candidate}")
        return self._analyze_map(candidate)

    def analyze(self) -> dict[str, Any]:
        profiles = []
        for path in self.reference_paths():
            try:
                profiles.append(self.analyze_path(path))
            except (OSError, UnicodeError, ValueError, struct.error) as exc:
                profiles.append({
                    "status": "BLOCKED",
                    "name": path.stem,
                    "source": str(path.relative_to(self.root)),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
        archetypes = self._archetypes(profiles)
        return {
            "stage": "Reference Map Corpus Analysis",
            "status": "PASS" if profiles and all(row["status"] == "PASS" for row in profiles) else "BLOCKED",
            "format": "rme-reference-corpus-abstract-v1",
            "policy": {
                "stores_source_screenshots": False,
                "stores_tile_coordinates": False,
                "stores_tile_stacks": False,
                "allows_exact_chunk_reuse": False,
                "learns": "aggregated materials, brush families, density, topology and normalized composition",
            },
            "corpus_root": str(self.corpus_root),
            "reference_count": len(profiles),
            "profiles": profiles,
            "archetypes": archetypes,
        }

    def write(self, output: str | Path | None = None) -> dict[str, Any]:
        report = self.analyze()
        target = Path(output) if output else (
            self.root / "exports" / "planner_knowledge" / "REFERENCE_MAP_CORPUS.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        return report

    def _analyze_map(self, path: Path) -> dict[str, Any]:
        tiles, towns = self._read_tiles(path)
        if not tiles:
            return {"status": "BLOCKED", "name": path.stem, "reason": "no tiles"}
        town = towns[0] if towns else {"name": path.stem, "x": 0, "y": 0, "z": 7}
        item_counts: Counter[int] = Counter()
        ground_counts: Counter[int] = Counter()
        category_counts: Counter[str] = Counter()
        brush_counts: Counter[tuple[str, str]] = Counter()
        stack_sizes: Counter[int] = Counter()
        minimap_colors: Counter[int] = Counter()
        minimap_color_materials: Counter[tuple[int, int, str]] = Counter()
        floors: dict[int, list[dict[str, Any]]] = defaultdict(list)
        ground_by_position: dict[tuple[int, int, int], int] = {}
        families_by_position: dict[tuple[int, int, int], set[tuple[str, str]]] = {}
        connectors_by_position: dict[tuple[int, int, int], set[str]] = {}
        for tile in tiles:
            floors[tile["z"]].append(tile)
            stack_sizes[len(tile["items"])] += 1
            for item_id in tile["items"]:
                item_counts[item_id] += 1
                categories = self.category_by_item.get(item_id, ())
                category_counts.update(categories or ("unclassified",))
                for brush in self.brush_by_item.get(item_id, ()):
                    brush_counts[brush] += 1
                    families_by_position.setdefault(
                        (tile["x"], tile["y"], tile["z"]), set()
                    ).add(brush)
                connector_families = self.vertical_connector_by_item.get(item_id, ())
                if connector_families:
                    connectors_by_position.setdefault(
                        (tile["x"], tile["y"], tile["z"]), set()
                    ).update(connector_families)
            ground = next((item_id for item_id in tile["items"] if self._is_ground(item_id)), None)
            if ground is not None:
                ground_counts[ground] += 1
                ground_by_position[(tile["x"], tile["y"], tile["z"])] = ground
            minimap = self._tile_minimap_color(tile)
            if minimap is not None:
                color, item_id, selection_role = minimap
                minimap_colors[color] += 1
                minimap_color_materials[(color, item_id, selection_role)] += 1

        xs = [tile["x"] for tile in tiles]
        ys = [tile["y"] for tile in tiles]
        floor_profiles = [
            self._floor_profile(floor, floor_tiles, ground_by_position)
            for floor, floor_tiles in sorted(floors.items())
        ]
        material_usage = self._material_rows(item_counts, len(tiles), len(item_counts))
        brush_usage = [
            {"kind": kind, "name": brush_name, "count": count}
            for (kind, brush_name), count in brush_counts.most_common()
        ]
        profile = {
            "status": "PASS",
            "name": path.stem,
            "archetype": path.stem.lower(),
            "source": str(path.relative_to(self.root)),
            "source_sha256": self._sha256(path),
            "bytes": path.stat().st_size,
            "town": town,
            "dimensions": {
                "width": max(xs) - min(xs) + 1,
                "height": max(ys) - min(ys) + 1,
                "floor_count": len(floors),
                "min_floor": min(floors),
                "max_floor": max(floors),
            },
            "tile_count": len(tiles),
            "ground_diversity": len(ground_counts),
            "material_diversity": len(item_counts),
            "stack_size_histogram": {str(key): value for key, value in sorted(stack_sizes.items())},
            "material_usage": material_usage,
            "top_materials": material_usage[:128],
            "brush_usage": brush_usage,
            "top_brushes": brush_usage[:64],
            "category_mix": self._ratios(category_counts),
            "floor_profiles": floor_profiles,
            "town_centered_composition": self._town_composition(tiles, town),
            "ground_transitions": self._ground_transitions(ground_by_position),
            "border_mixes": self._border_mixes(tiles, ground_by_position),
            "vertical_overlap": self._vertical_overlap(ground_by_position),
            "vertical_connectors": self._vertical_connectors(
                connectors_by_position,
                ground_by_position,
            ),
            "family_coverage": self._family_coverage(brush_counts, item_counts),
            "biome_family_mixes": self._biome_family_mixes(families_by_position),
            "minimap_color_profile": self._minimap_color_profile(
                minimap_colors,
                minimap_color_materials,
                len(tiles),
            ),
            "sidecars": self._sidecars(path),
            "generation_rules": self._generation_rules(path.stem.lower(), floor_profiles, category_counts),
        }
        # Raw positions and stacks exist only during this method.
        return profile

    def _read_tiles(self, path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        tiles: list[dict[str, Any]] = []
        towns: list[dict[str, Any]] = []
        area: tuple[int, int, int] | None = None
        current: dict[str, Any] | None = None
        tile_depth = -1

        def finish() -> None:
            nonlocal current
            if current is not None:
                tiles.append(current)
                current = None

        with OTBMNodeReader(path) as reader:
            def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
                nonlocal area, current, tile_depth
                if node.node_type == 0x04:
                    finish()
                    area = OTBMAttributeReader.parse_tile_area(node.attrs)
                elif node.node_type in (0x05, 0x0E) and area is not None:
                    finish()
                    current = OTBMAttributeReader.parse_tile(
                        node.attrs,
                        *area,
                        house=node.node_type == 0x0E,
                    )
                    if current["ground"] is not None:
                        current["items"].append(int(current["ground"]))
                    tile_depth = node.depth
                elif node.node_type == 0x06 and current is not None and node.depth == tile_depth + 1:
                    current["items"].append(int(OTBMAttributeReader.parse_item(node.attrs)["id"]))
                elif node.node_type == 0x0D:
                    finish()
                    towns.append(self._town(node.attrs))

            reader.traverse(on_node, max_nodes=None, max_bytes=None)
        finish()
        return tiles, towns

    @staticmethod
    def _town(attrs: bytes) -> dict[str, Any]:
        if len(attrs) < 11:
            raise ValueError("Truncated OTBM town node")
        town_id = struct.unpack_from("<I", attrs, 0)[0]
        length = struct.unpack_from("<H", attrs, 4)[0]
        if 6 + length + 5 > len(attrs):
            raise ValueError("Invalid OTBM town name length")
        name = attrs[6 : 6 + length].decode("utf-8", errors="replace")
        x, y, z = struct.unpack_from("<HHB", attrs, 6 + length)
        return {"id": town_id, "name": name, "x": x, "y": y, "z": z}

    def _floor_profile(
        self,
        floor: int,
        tiles: list[dict[str, Any]],
        grounds: dict[tuple[int, int, int], int],
    ) -> dict[str, Any]:
        items = [item for tile in tiles for item in tile["items"]]
        item_counts = Counter(items)
        material_usage = self._material_rows(item_counts, len(tiles), len(item_counts))
        categories = Counter(
            category
            for item in items
            for category in (self.category_by_item.get(item) or ("unclassified",))
        )
        xs, ys = [tile["x"] for tile in tiles], [tile["y"] for tile in tiles]
        minimap_colors: Counter[int] = Counter()
        minimap_color_materials: Counter[tuple[int, int, str]] = Counter()
        for tile in tiles:
            minimap = self._tile_minimap_color(tile)
            if minimap is not None:
                color, item_id, selection_role = minimap
                minimap_colors[color] += 1
                minimap_color_materials[(color, item_id, selection_role)] += 1
        return {
            "floor": floor,
            "tile_count": len(tiles),
            "width": max(xs) - min(xs) + 1,
            "height": max(ys) - min(ys) + 1,
            "item_density": round(len(items) / max(1, len(tiles)), 5),
            "ground_diversity": len({grounds[key] for key in grounds if key[2] == floor}),
            "ground_materials": self._materials_by_role(material_usage, "ground"),
            "nature_materials": self._materials_by_role(material_usage, "nature"),
            "border_materials": self._materials_by_role(material_usage, "border"),
            "wall_materials": self._materials_by_role(material_usage, "wall"),
            "doodad_materials": self._materials_by_role(material_usage, "doodad"),
            "material_usage": material_usage,
            "category_mix": self._ratios(categories),
            "minimap_color_profile": self._minimap_color_profile(
                minimap_colors,
                minimap_color_materials,
                len(tiles),
            ),
        }

    @staticmethod
    def _materials_by_role(materials: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
        nature_categories = {"nature", "vegetation", "tree", "trees", "plant", "plants"}
        rows = []
        for material in materials:
            categories = {str(value).lower() for value in material["categories"]}
            brush_kinds = {str(value["kind"]).lower() for value in material["brushes"]}
            matched = bool(categories.intersection(nature_categories)) if role == "nature" else (
                role in categories or role in brush_kinds
            )
            if matched:
                rows.append(material)
        return rows

    def _material_rows(self, counts: Counter[int], tile_count: int, limit: int) -> list[dict[str, Any]]:
        rows = []
        for item_id, count in counts.most_common(limit):
            brushes = self.brush_by_item.get(item_id, ())
            rows.append({
                "item_id": item_id,
                "count": count,
                "per_tile": round(count / max(1, tile_count), 6),
                "categories": list(self.category_by_item.get(item_id, ())),
                "brushes": [{"kind": kind, "name": name} for kind, name in brushes[:8]],
            })
        return rows

    def _town_composition(self, tiles: list[dict[str, Any]], town: dict[str, Any]) -> dict[str, Any]:
        rings: Counter[str] = Counter()
        sectors: Counter[str] = Counter()
        for tile in tiles:
            dx, dy = tile["x"] - town["x"], tile["y"] - town["y"]
            distance = math.hypot(dx, dy)
            ring = next((label for limit, label in ((8, "0-7"), (16, "8-15"), (32, "16-31"), (64, "32-63")) if distance < limit), "64+")
            rings[ring] += 1
            sectors[self._sector(dx, dy)] += 1
        total = max(1, len(tiles))
        return {
            "radial_tile_ratio": {key: round(value / total, 6) for key, value in sorted(rings.items())},
            "directional_tile_ratio": {key: round(value / total, 6) for key, value in sorted(sectors.items())},
        }

    @staticmethod
    def _sector(dx: int, dy: int) -> str:
        if dx == dy == 0:
            return "center"
        angle = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
        return ("east", "southeast", "south", "southwest", "west", "northwest", "north", "northeast")[int((angle + 22.5) // 45) % 8]

    @staticmethod
    def _ground_transitions(grounds: dict[tuple[int, int, int], int]) -> list[dict[str, Any]]:
        transitions: Counter[tuple[int, int]] = Counter()
        for (x, y, z), ground in grounds.items():
            for neighbor in ((x + 1, y, z), (x, y + 1, z)):
                other = grounds.get(neighbor)
                if other is not None and other != ground:
                    transitions[tuple(sorted((ground, other)))] += 1
        return [
            {"ground_a": pair[0], "ground_b": pair[1], "edges": count}
            for pair, count in transitions.most_common()
        ]

    def _border_mixes(
        self,
        tiles: list[dict[str, Any]],
        grounds: dict[tuple[int, int, int], int],
    ) -> list[dict[str, Any]]:
        mixes: Counter[tuple[int, int, int]] = Counter()
        for tile in tiles:
            x, y, z = tile["x"], tile["y"], tile["z"]
            border_ids = [
                item_id for item_id in tile["items"]
                if "border" in {kind for kind, _ in self.brush_by_item.get(item_id, ())}
                or "border" in self.category_by_item.get(item_id, ())
            ]
            if not border_ids:
                continue
            ground_ids = {
                ground for position in (
                    (x, y, z), (x - 1, y, z), (x + 1, y, z), (x, y - 1, z), (x, y + 1, z)
                ) if (ground := grounds.get(position)) is not None
            }
            for ground_id in ground_ids:
                for border_id in border_ids:
                    mixes[(z, ground_id, border_id)] += 1
        return [
            {"floor": floor, "ground_id": ground_id, "border_id": border_id, "count": count}
            for (floor, ground_id, border_id), count in mixes.most_common()
        ]

    @staticmethod
    def _vertical_overlap(grounds: dict[tuple[int, int, int], int]) -> dict[str, float]:
        positions = set(grounds)
        pairs: Counter[str] = Counter()
        totals: Counter[str] = Counter()
        for x, y, z in positions:
            key = f"{z}->{z - 1}"
            totals[key] += 1
            if (x, y, z - 1) in positions:
                pairs[key] += 1
        return {key: round(pairs[key] / max(1, value), 6) for key, value in sorted(totals.items())}

    @staticmethod
    def _sidecars(path: Path) -> dict[str, Any]:
        rows: dict[str, Any] = {}
        for kind in ("house", "monster", "npc", "zones"):
            source = path.with_name(f"{path.stem}-{kind}.xml")
            if not source.is_file():
                rows[kind] = {"present": False, "count": 0}
                continue
            try:
                root = ET.parse(source).getroot()
                rows[kind] = {
                    "present": True,
                    "root": root.tag,
                    "count": len(list(root)),
                    "tags": dict(Counter(element.tag for element in root.iter())),
                }
            except ET.ParseError as exc:
                rows[kind] = {"present": True, "count": 0, "error": str(exc)}
        return rows

    def _category_index(self) -> dict[int, tuple[str, ...]]:
        reverse: dict[int, set[str]] = defaultdict(set)
        for category, item_ids in self.classification["categories"].items():
            if category in {"sprite_backed", "valid_base_ground", "invalid_for_ground"}:
                continue
            for item_id in item_ids:
                reverse[int(item_id)].add(str(category))
        return {item_id: tuple(sorted(values)) for item_id, values in reverse.items()}

    def _brush_index(self) -> dict[int, tuple[tuple[str, str], ...]]:
        reverse: dict[int, set[tuple[str, str]]] = defaultdict(set)

        def item_ids(value: Any):
            if isinstance(value, int):
                yield value
                return
            if hasattr(value, "item_id"):
                yield int(value.item_id)
                return
            if isinstance(value, dict):
                for nested in value.values():
                    yield from item_ids(nested)
                return
            if isinstance(value, (tuple, list, set, frozenset)):
                for nested in value:
                    yield from item_ids(nested)

        for name, brush in self.brush_engine.ground_brushes.items():
            for item in brush.items:
                reverse[item.item_id].add(("ground", name))
        for name, brush in self.brush_engine.doodad_brushes.items():
            for item in brush.items:
                reverse[item.item_id].add(("doodad", name))
            for composite in brush.composites:
                for item_id in item_ids(composite):
                    reverse[item_id].add(("doodad", name))
        for kind, brushes in (
            ("wall", self.brush_engine.wall_brushes),
            ("table", self.brush_engine.table_brushes),
            ("carpet", self.brush_engine.carpet_brushes),
            ("wall_decoration", self.brush_engine.wall_decoration_brushes),
        ):
            for name, brush in brushes.items():
                values = brush.variants.values()
                for value in values:
                    for item_id in item_ids(value):
                        reverse[item_id].add((kind, name))
        for border_id, border in self.brush_engine.borders.items():
            for item_id in item_ids(border.edges):
                reverse[item_id].add(("border", str(border_id)))
        return {item_id: tuple(sorted(values)) for item_id, values in reverse.items()}

    def _family_members(self) -> dict[tuple[str, str], set[int]]:
        members: dict[tuple[str, str], set[int]] = defaultdict(set)
        for item_id, families in self.brush_by_item.items():
            for family in families:
                members[family].add(int(item_id))
        return dict(members)

    def _vertical_connector_index(self) -> dict[int, tuple[str, ...]]:
        """Resolve connector membership from RME's official stairs tileset."""
        candidates = (
            self.root / "projects" / "canary-extracted" / "canary-map-editor-v4.0-windows"
            / "data" / "materials" / "tilesets" / "stairs.xml",
            self.root / "data" / "materials" / "tilesets" / "stairs.xml",
        )
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            return {}
        root = ET.parse(source).getroot()
        connector_families: dict[int, set[str]] = defaultdict(set)
        for element in root.iter():
            if element.tag == "brush" and element.get("name"):
                name = str(element.get("name"))
                for item_id, families in self.brush_by_item.items():
                    if any(family_name == name for _kind, family_name in families):
                        connector_families[int(item_id)].add(name)
            elif element.tag == "item" and element.get("id", "").isdigit():
                connector_families[int(element.get("id"))].add("Stairs / Ramps / Ladders RAW")
            elif (
                element.tag == "item"
                and element.get("fromid", "").isdigit()
                and element.get("toid", "").isdigit()
            ):
                start, end = int(element.get("fromid")), int(element.get("toid"))
                for item_id in range(start, end + 1):
                    connector_families[item_id].add("Stairs / Ramps / Ladders RAW")
        return {
            item_id: tuple(sorted(families))
            for item_id, families in connector_families.items()
        }

    def _family_coverage(
        self,
        brush_counts: Counter[tuple[str, str]],
        item_counts: Counter[int],
    ) -> list[dict[str, Any]]:
        used_members: dict[tuple[str, str], set[int]] = defaultdict(set)
        for item_id, families in self.brush_by_item.items():
            if not item_counts.get(item_id, 0):
                continue
            for family in families:
                used_members[family].add(item_id)
        rows = []
        for family, usage_count in brush_counts.most_common():
            official_count = len(self.family_members.get(family, ()))
            used_count = len(used_members.get(family, ()))
            rows.append({
                "kind": family[0],
                "name": family[1],
                "usage_count": usage_count,
                "used_members": used_count,
                "official_members": official_count,
                "coverage_ratio": round(used_count / max(1, official_count), 6),
            })
        return rows

    @staticmethod
    def _biome_family_mixes(
        families_by_position: dict[tuple[int, int, int], set[tuple[str, str]]],
    ) -> list[dict[str, Any]]:
        ecological_kinds = {"ground", "doodad", "wall"}
        mixes: Counter[tuple[int, tuple[str, str], tuple[str, str]]] = Counter()
        for (x, y, z), families in families_by_position.items():
            for dx, dy in ((1, 0), (0, 1)):
                adjacent = families_by_position.get((x + dx, y + dy, z), set())
                for left in families:
                    for right in adjacent:
                        if (
                            left == right
                            or left[0] not in ecological_kinds
                            or right[0] not in ecological_kinds
                        ):
                            continue
                        first, second = sorted((left, right))
                        mixes[(z, first, second)] += 1
        return [
            {
                "floor": floor,
                "family_a": {"kind": left[0], "name": left[1]},
                "family_b": {"kind": right[0], "name": right[1]},
                "adjacency_count": count,
            }
            for (floor, left, right), count in mixes.most_common(256)
        ]

    @staticmethod
    def _vertical_connectors(
        connectors: dict[tuple[int, int, int], set[str]],
        grounds: dict[tuple[int, int, int], int],
    ) -> list[dict[str, Any]]:
        rows: Counter[tuple[int, str, bool, bool]] = Counter()
        for (x, y, z), families in connectors.items():
            upper_support = any(
                (x + dx, y + dy, z - 1) in grounds
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            )
            lower_support = any(
                (x + dx, y + dy, z + 1) in grounds
                for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            )
            for family in families:
                rows[(z, family, upper_support, lower_support)] += 1
        return [
            {
                "floor": floor,
                "family": family,
                "usage_count": count,
                "adjacent_upper_floor_support": upper,
                "adjacent_lower_floor_support": lower,
                "coordinates_included": False,
            }
            for (floor, family, upper, lower), count in rows.most_common()
        ]

    def _is_ground(self, item_id: int) -> bool:
        return item_id in self.brush_engine.valid_base_ground or any(
            kind == "ground" for kind, _name in self.brush_by_item.get(item_id, ())
        )

    def _tile_minimap_color(self, tile: dict[str, Any]) -> tuple[int, int, str] | None:
        items = [int(item_id) for item_id in tile.get("items", ())]
        ground = int(tile["ground"]) if tile.get("ground") is not None else None
        non_ground_items = items[1:] if ground is not None and items and items[0] == ground else items
        for item_id in reversed(non_ground_items):
            color = self.automap_colors.get(item_id, 0)
            if color:
                return int(color), item_id, "top_item"
        if ground is not None:
            color = self.automap_colors.get(ground, 0)
            if color:
                return int(color), ground, "ground"
        return None

    @staticmethod
    def _minimap_color_profile(
        colors: Counter[int],
        materials: Counter[tuple[int, int, str]],
        tile_count: int,
    ) -> dict[str, Any]:
        colored_tiles = sum(colors.values())
        return {
            "source": "appearances.dat automap.color; Canary Tile::getMiniMapColor priority",
            "colored_tiles": colored_tiles,
            "coverage": round(colored_tiles / max(1, tile_count), 6),
            "distinct_colors": len(colors),
            "colors": [
                {
                    "color": color,
                    "rgb": list(rme_minimap_color_to_rgb(color)),
                    "tile_count": count,
                    "tile_ratio": round(count / max(1, tile_count), 6),
                }
                for color, count in colors.most_common()
            ],
            "material_sources": [
                {
                    "color": color,
                    "item_id": item_id,
                    "selection_role": selection_role,
                    "tile_count": count,
                }
                for (color, item_id, selection_role), count in materials.most_common()
            ],
        }

    def _load_automap_colors(self) -> dict[int, int]:
        render_path = self.root / "APPEARANCE_RENDER_CATALOG.json"
        item_path = self.root / "APPEARANCE_ITEM_CATALOG.json"
        appearances_path = self.root / "assets" / "appearances-ee339aff5b3cb38289287ff25cec261d8d2790e6e146938d4dfd9f138b065980.dat"
        if not render_path.is_file() or not item_path.is_file() or not appearances_path.is_file():
            return {}
        render = json.loads(render_path.read_text(encoding="utf-8"))
        items = json.loads(item_path.read_text(encoding="utf-8"))
        extractor = AppearanceDatFlagExtractor(appearances_path)
        appearance_colors: dict[int, int] = {}
        for raw_id, payload in render.items():
            if not str(raw_id).isdigit() or not isinstance(payload, dict):
                continue
            color = extractor.extract_from_catalog_entry(int(raw_id), payload).flags.get("automap_color")
            if color:
                appearance_colors[int(raw_id)] = int(color)
        colors: dict[int, int] = {}
        for raw_id, item in items.items():
            if not str(raw_id).isdigit() or not isinstance(item, dict):
                continue
            candidates = [
                item.get("appearance_id"), item.get("client_id"), item.get("lookid"), item.get("id"),
            ]
            candidates.extend(
                brush.get("lookid") for brush in item.get("brushes", ()) if isinstance(brush, dict)
            )
            candidates.append(int(raw_id))
            appearance_id = next(
                (
                    int(candidate)
                    for candidate in candidates
                    if candidate is not None and str(candidate).isdigit() and int(candidate) in appearance_colors
                ),
                None,
            )
            if appearance_id is not None:
                colors[int(raw_id)] = appearance_colors[appearance_id]
        return colors

    def _generation_rules(self, name: str, floors: list[dict[str, Any]], categories: Counter[str]) -> dict[str, Any]:
        semantic = {
            "river": "branching water corridor with varied banks and crossable access",
            "nature": "layered vegetation clusters with clear negative-space paths",
            "miniboats": "small watercraft silhouettes assembled from oriented multi-tile materials",
            "towers": "vertically overlapping footprints connected by real stairs or ramps",
            "krailos": "dry high-level hunt terrain with layered grounds, rocky borders and sparse vegetation",
            "montaña": (
                "multilevel mountain terrain with coherent cliff faces, traversable plateaus, "
                "real stairs or ramps and vertically aligned transitions"
            ),
            "firecave": (
                "volcanic cave hunt with heat-safe ground families, enclosed chambers, branching "
                "routes and coherent cave-wall borders"
            ),
        }.get(name, "abstract reference composition")
        return {
            "semantic_intent": semantic,
            "target_floor_count": len(floors),
            "category_mix": self._ratios(categories),
            "variation_policy": "resample proportions and topology; never replay source coordinates",
            "similarity_guard_required": True,
        }

    @staticmethod
    def _archetypes(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "name": profile["archetype"],
                "source_count": 1,
                "dimensions": profile["dimensions"],
                "category_mix": profile["category_mix"],
                "generation_rules": profile["generation_rules"],
            }
            for profile in profiles if profile.get("status") == "PASS"
        ]

    @staticmethod
    def _ratios(counter: Counter[Any]) -> dict[str, float]:
        total = max(1, sum(counter.values()))
        return {str(key): round(value / total, 6) for key, value in counter.most_common()}

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()


__all__ = ["ReferenceMapCorpusAnalyzer"]
