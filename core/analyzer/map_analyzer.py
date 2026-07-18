"""
HITO 12 — Map Analyzer: analyzes tiles, items, spawns, houses and waypoints
from .otbm or .xml files, using the complete OTBM pipeline.
"""

from __future__ import annotations

import json
import os
import struct
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .tile_analyzer import TileAnalyzer
from .room_analyzer import RoomAnalyzer
from .city_analyzer import CityAnalyzer
from .spawn_analyzer import SpawnAnalyzer
from .style_analyzer import StyleAnalyzer
from .pattern_extractor import PatternExtractor
from .path_analyzer import PathAnalyzer
from .density_analyzer import DensityAnalyzer
from .architecture_analyzer import ArchitectureAnalyzer


@dataclass
class MapAnalysis:
    """Complete result of a map analysis."""

    source: str
    map_size: Dict[str, int] = field(default_factory=dict)
    floors: List[int] = field(default_factory=list)
    tile_count: int = 0
    item_count: int = 0
    tiles: Dict[str, int] = field(default_factory=dict)
    items: Dict[str, int] = field(default_factory=dict)
    houses: List[Dict[str, object]] = field(default_factory=list)
    spawns: List[Dict[str, object]] = field(default_factory=list)
    waypoints: List[Dict[str, object]] = field(default_factory=list)
    zones: List[Dict[str, object]] = field(default_factory=list)
    style: Optional[str] = None
    patterns: List[Dict[str, object]] = field(default_factory=list)
    path_analysis: Optional[Dict[str, object]] = None
    density_analysis: Optional[Dict[str, object]] = None
    architecture_analysis: Optional[Dict[str, object]] = None

    def to_dict(self) -> Dict[str, object]:
        """Export the analysis as a JSON-serializable dictionary."""
        return {
            "source": self.source,
            "map_size": self.map_size,
            "floors": self.floors,
            "tile_count": self.tile_count,
            "item_count": self.item_count,
            "top_tiles": dict(
                sorted(self.tiles.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "top_items": dict(
                sorted(self.items.items(), key=lambda x: x[1], reverse=True)[:20]
            ),
            "total_tile_types": len(self.tiles),
            "total_item_types": len(self.items),
            "houses": self.houses,
            "house_count": len(self.houses),
            "spawns": self.spawns,
            "spawn_count": len(self.spawns),
            "waypoints": self.waypoints,
            "waypoint_count": len(self.waypoints),
            "zones": self.zones,
            "style": self.style,
            "patterns": self.patterns,
            "path_analysis": self.path_analysis,
            "density_analysis": self.density_analysis,
            "architecture_analysis": self.architecture_analysis,
        }


class MapAnalyzer:
    """Main OTBM/XML map analyzer with complete pipeline."""

    def __init__(self, otbm_importer: Optional[Any] = None):
        """
        Args:
            otbm_importer: Optional OTBMImporter instance for full OTBM analysis.
                           If not provided, basic byte analysis will be used.
        """
        self.tile_analyzer = TileAnalyzer()
        self.room_analyzer = RoomAnalyzer()
        self.city_analyzer = CityAnalyzer()
        self.spawn_analyzer = SpawnAnalyzer(otbm_importer=otbm_importer)
        self.style_analyzer = StyleAnalyzer()
        self.pattern_extractor = PatternExtractor()
        self.path_analyzer = PathAnalyzer()
        self.density_analyzer = DensityAnalyzer()
        self.architecture_analyzer = ArchitectureAnalyzer()
        self._otbm_importer = otbm_importer

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyze(self, path: str) -> MapAnalysis:
        """Analyze a map file and return a complete MapAnalysis.

        Args:
            path: Path to .otbm or .xml file
        """
        analysis = MapAnalysis(source=path)

        if path.endswith(".otbm"):
            self._analyze_otbm(path, analysis)
        elif path.endswith(".xml"):
            self._analyze_xml(path, analysis)
        else:
            raise ValueError(f"Unsupported format: {path}")

        # Run derived analyses
        self._run_derived_analysis(analysis)

        return analysis

    # ------------------------------------------------------------------
    # OTBM analysis (using full pipeline when available)
    # ------------------------------------------------------------------

    def _analyze_otbm(self, path: str, analysis: MapAnalysis) -> None:
        """Analyze .otbm file using the complete OTBM pipeline."""
        data = self._read_file_bytes(path)

        if self._otbm_importer is not None:
            self._analyze_otbm_with_importer(path, analysis)
        else:
            self._analyze_otbm_direct(data, path, analysis)

    def _analyze_otbm_with_importer(self, path: str, analysis: MapAnalysis) -> None:
        """Analysis using OTBMImporter + NodeDecoder for complete extraction."""
        try:
            result = self._otbm_importer.import_file(path)
            if not result.get("success"):
                return

            world_dict = result.get("world_dict", {})
            result.get("stats", {})

            # Map dimensions
            analysis.map_size = {
                "width": world_dict.get("width", 0),
                "height": world_dict.get("height", 0),
            }

            # Tiles and items from world_dict
            tiles_raw = world_dict.get("tiles", [])
            analysis.tile_count = len(tiles_raw)
            self._extract_tiles_and_items_from_world_dict(tiles_raw, analysis)

            # Spawns
            spawns_raw = world_dict.get("spawns", [])
            analysis.spawns = self.spawn_analyzer.analyze_otbm_spawns(spawns_raw)

            # Houses (from towns as houses)
            cities_raw = world_dict.get("cities", [])
            analysis.houses = self._cities_to_houses(cities_raw)

            # Waypoints
            waypoints_raw = world_dict.get("waypoints", [])
            analysis.waypoints = self._normalize_waypoints(waypoints_raw)

            # Floors from tiles
            floors = set()
            for tile in tiles_raw:
                z = tile.get("z", 0)
                if isinstance(z, int):
                    floors.add(z)
            analysis.floors = sorted(floors)

            # Style
            analysis.style = self.style_analyzer.detect_style(analysis.tiles)

            # Pattern
            analysis.patterns.append(
                self.pattern_extractor.extract_pattern(
                    source=os.path.basename(path),
                    style=analysis.style or "unknown",
                    tile_stats=analysis.tiles,
                    width=analysis.map_size.get("width", 0),
                    height=analysis.map_size.get("height", 0),
                    floors=analysis.floors,
                )
            )

        except Exception:
            # Fallback to direct analysis
            data = self._read_file_bytes(path)
            self._analyze_otbm_direct(data, path, analysis)

    def _analyze_otbm_direct(
        self, data: bytes, path: str, analysis: MapAnalysis
    ) -> None:
        """Direct OTBM byte analysis (fallback without importer)."""
        # Dimensions from OTBM header
        if len(data) > 20 and data[:4] == b"OTBM":
            struct.unpack_from("<I", data, 4)[0]
            width = struct.unpack_from("<H", data, 8)[0]
            height = struct.unpack_from("<H", data, 10)[0]
            analysis.map_size = {"width": width, "height": height}
        else:
            analysis.map_size = {"width": 100, "height": 100}

        # Extract tiles using tile_analyzer for bytes
        analysis.tiles = self._extract_binary_tiles_enhanced(data)
        analysis.items = self._extract_binary_items(data)
        analysis.tile_count = sum(analysis.tiles.values())
        analysis.item_count = sum(analysis.items.values())

        # Spawns from binary data
        analysis.spawns = self.spawn_analyzer.analyze_otbm_direct(data)

        # Waypoints from binary data
        analysis.waypoints = self._extract_binary_waypoints(data)

        # Houses from towns in binary
        analysis.houses = self._extract_binary_houses(data)

        # Floors from TILE_AREA (base_z)
        analysis.floors = self._extract_binary_floors(data)

        # Style and patterns
        analysis.style = self.style_analyzer.detect_style(analysis.tiles)
        analysis.patterns.append(
            self.pattern_extractor.extract_pattern(
                source=os.path.basename(path),
                style=analysis.style or "unknown",
                tile_stats=analysis.tiles,
                width=analysis.map_size.get("width", 0),
                height=analysis.map_size.get("height", 0),
                floors=analysis.floors,
            )
        )

    def _extract_tiles_and_items_from_world_dict(
        self, tiles_raw: List[Dict[str, Any]], analysis: MapAnalysis
    ) -> None:
        """Extract tile and item statistics from world_dict."""
        tile_counter = Counter()
        item_counter = Counter()

        for tile in tiles_raw:
            ground = tile.get("ground")
            if ground is not None:
                tile_counter[f"ground_{ground}"] += 1

            for item in tile.get("items", []):
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                item_counter[f"item_{item_id}"] += 1

            # Items en all_items
            for item in tile.get("all_items", []):
                item_id = item.get("item_id", item) if isinstance(item, dict) else item
                item_counter[f"item_{item_id}"] += 1

        analysis.tiles = dict(tile_counter)
        analysis.items = dict(item_counter)
        analysis.item_count = sum(item_counter.values())

        if analysis.tile_count == 0:
            analysis.tile_count = sum(tile_counter.values())

    # ------------------------------------------------------------------
    # XML analysis
    # ------------------------------------------------------------------

    def _analyze_xml(self, path: str, analysis: MapAnalysis) -> None:
        """Analyze XML file."""
        tree = ET.parse(path)
        root = tree.getroot()

        # Map size
        analysis.map_size = self._extract_map_size(root)

        # Floors
        analysis.floors = self._extract_floors(root)

        # Tiles
        analysis.tiles = self.tile_analyzer.analyze_xml_tiles(root)
        analysis.tile_count = sum(analysis.tiles.values())

        # Items from tiles
        item_counter = Counter()
        for tile in root.findall("map/tile"):
            for item in tile.findall("item"):
                item_counter[f"item_{item.get('id', 'unknown')}"] += 1
        analysis.items = dict(item_counter)
        analysis.item_count = sum(analysis.items.values())

        # Houses
        analysis.houses = self._extract_houses(root)

        # Spawns
        analysis.spawns = self.spawn_analyzer.analyze_spawn_xml(root)

        # Waypoints
        analysis.waypoints = self._extract_waypoints(root)

        # Zones
        analysis.zones = self._extract_zones(root)

        # Style and patterns
        analysis.style = self.style_analyzer.detect_style(analysis.tiles)
        analysis.patterns.append(
            self.pattern_extractor.extract_pattern(
                source=os.path.basename(path),
                style=analysis.style or "unknown",
                tile_stats=analysis.tiles,
                width=analysis.map_size.get("width", 0),
                height=analysis.map_size.get("height", 0),
                floors=analysis.floors,
            )
        )

    # ------------------------------------------------------------------
    # Derived analyses (path, density, architecture)
    # ------------------------------------------------------------------

    def _run_derived_analysis(self, analysis: MapAnalysis) -> None:
        """Run derived analyses: path, density, architecture."""
        try:
            analysis.path_analysis = self.path_analyzer.analyze(
                waypoints=analysis.waypoints,
                spawns=analysis.spawns,
            )
        except Exception:
            analysis.path_analysis = None

        try:
            analysis.density_analysis = self.density_analyzer.analyze(
                tiles=analysis.tiles,
                items=analysis.items,
                spawns=analysis.spawns,
                map_size=analysis.map_size,
            )
        except Exception:
            analysis.density_analysis = None

        try:
            analysis.architecture_analysis = self.architecture_analyzer.analyze(
                tiles=analysis.tiles,
                items=analysis.items,
                houses=analysis.houses,
                spawns=analysis.spawns,
                waypoints=analysis.waypoints,
                map_size=analysis.map_size,
            )
        except Exception:
            analysis.architecture_analysis = None

    # ------------------------------------------------------------------
    # Enhanced binary extraction methods
    # ------------------------------------------------------------------

    @staticmethod
    def _read_file_bytes(path: str) -> bytes:
        """Read a file as bytes, return empty if it does not exist."""
        try:
            return Path(path).read_bytes()
        except FileNotFoundError:
            return b""

    def _extract_binary_tiles_enhanced(self, data: bytes) -> Dict[str, int]:
        """Extract tiles from binary with enhanced detection."""
        counts = defaultdict(int)
        # Known ground IDs
        ground_ids = [393, 415, 416, 396, 1053, 1056]
        ground_names = {
            393: "sandstone_floor",
            415: "polished_stone",
            416: "mossy_stone",
            396: "yalahar_floor",
            1053: "roshamuul_floor",
            1056: "roshamuul_stone",
        }
        for gid in ground_ids:
            count = data.count(struct.pack("<H", gid))
            if count > 0:
                counts[ground_names.get(gid, f"ground_{gid}")] += count

        # Contar nodos TILE (0x03)
        counts["total_raw_tiles"] = data.count(b"\x03")

        return dict(counts)

    @staticmethod
    def _extract_binary_items(data: bytes) -> Dict[str, int]:
        """Extract item count from binary."""
        counts = defaultdict(int)
        # Search for ITEM nodes (0x04)
        offset = 0
        while True:
            idx = data.find(b"\x04", offset)
            if idx == -1 or idx + 3 >= len(data):
                break
            try:
                item_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + item_size > len(data):
                    offset = idx + 1
                    continue
                if item_size >= 2:
                    item_id = struct.unpack_from("<H", data, idx + 3)[0]
                    counts[f"item_{item_id}"] += 1
                    offset = idx + 3 + item_size
                else:
                    offset = idx + 1
            except (struct.error, IndexError):
                offset = idx + 1
        return dict(counts)

    @staticmethod
    def _extract_binary_waypoints(data: bytes) -> List[Dict[str, object]]:
        """Extract waypoints from binary WAYPOINT nodes."""
        waypoints = []
        offset = 0
        marker = b"\x19"  # OTBM_NODE_WAYPOINT
        while True:
            idx = data.find(marker, offset)
            if idx == -1 or idx + 3 >= len(data):
                break
            try:
                wp_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + wp_size > len(data):
                    offset = idx + 1
                    continue
                payload = data[idx + 3 : idx + 3 + wp_size]
                name, wp_offset = _read_string(payload, 0)
                if wp_offset + 5 <= len(payload):
                    x = struct.unpack_from("<H", payload, wp_offset)[0]
                    y = struct.unpack_from("<H", payload, wp_offset + 2)[0]
                    z = payload[wp_offset + 4]
                    waypoints.append({"name": name, "x": x, "y": y, "z": z})
                offset = idx + 3 + wp_size
            except (struct.error, IndexError):
                offset = idx + 1
        return waypoints

    @staticmethod
    def _extract_binary_houses(data: bytes) -> List[Dict[str, object]]:
        """Extract houses/towns from binary."""
        houses = []
        offset = 0
        marker = b"\x0d"  # OTBM_NODE_TOWN
        while True:
            idx = data.find(marker, offset)
            if idx == -1 or idx + 3 >= len(data):
                break
            try:
                town_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + town_size > len(data):
                    offset = idx + 1
                    continue
                payload = data[idx + 3 : idx + 3 + town_size]
                town_id = struct.unpack_from("<I", payload, 0)[0]
                name, name_offset = _read_string(payload, 4)
                if name_offset + 5 <= len(payload):
                    tx = struct.unpack_from("<H", payload, name_offset)[0]
                    ty = struct.unpack_from("<H", payload, name_offset + 2)[0]
                    tz = (
                        payload[name_offset + 4]
                        if name_offset + 4 < len(payload)
                        else 7
                    )
                    houses.append(
                        {
                            "id": town_id,
                            "name": name,
                            "temple_x": tx,
                            "temple_y": ty,
                            "temple_z": tz,
                        }
                    )
                offset = idx + 3 + town_size
            except (struct.error, IndexError):
                offset = idx + 1
        return houses

    @staticmethod
    def _extract_binary_floors(data: bytes) -> List[int]:
        """Extract floors from TILE_AREA (base_z)."""
        floors = set()
        offset = 0
        marker = b"\x02"  # OTBM_NODE_TILE_AREA
        while True:
            idx = data.find(marker, offset)
            if idx == -1 or idx + 8 >= len(data):
                break
            try:
                ta_size = struct.unpack_from("<H", data, idx + 1)[0]
                if idx + 3 + ta_size > len(data):
                    offset = idx + 1
                    continue
                payload = data[idx + 3 : idx + 3 + ta_size]
                if len(payload) >= 5:
                    bz = payload[4]  # base_z es el 5to byte
                    floors.add(bz)
                offset = idx + 3 + ta_size
            except (struct.error, IndexError):
                offset = idx + 1
        return sorted(floors) if floors else [0]

    # ------------------------------------------------------------------
    # XML extraction methods (maintained and aligned)
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_map_size(root: ET.Element) -> Dict[str, int]:
        map_size = {"width": 0, "height": 0}
        for child in root.findall("map/size"):
            map_size["width"] = int(child.get("x", 0))
            map_size["height"] = int(child.get("y", 0))
        return map_size

    @staticmethod
    def _extract_floors(root: ET.Element) -> List[int]:
        floors = set()
        for tile in root.findall("map/tile"):
            floors.add(int(tile.get("z", 0)))
        return sorted(floors)

    @staticmethod
    def _extract_houses(root: ET.Element) -> List[Dict[str, object]]:
        houses = []
        for house in root.findall("houses/house"):
            houses.append(
                {
                    "id": int(house.get("id", 0)),
                    "name": house.get("name", ""),
                    "rent": int(house.get("rent", 0)),
                    "temple_x": int(house.get("temple_x", 0)),
                    "temple_y": int(house.get("temple_y", 0)),
                    "temple_z": int(house.get("temple_z", 0)),
                }
            )
        return houses

    @staticmethod
    def _extract_waypoints(root: ET.Element) -> List[Dict[str, object]]:
        waypoints = []
        for waypoint in root.findall("waypoints/waypoint"):
            waypoints.append(
                {
                    "name": waypoint.get("name", ""),
                    "x": int(waypoint.get("x", 0)),
                    "y": int(waypoint.get("y", 0)),
                    "z": int(waypoint.get("z", 0)),
                }
            )
        return waypoints

    @staticmethod
    def _extract_zones(root: ET.Element) -> List[Dict[str, object]]:
        zones = []
        for zone in root.findall("zones/zone"):
            zones.append(
                {
                    "name": zone.get("name", ""),
                    "type": zone.get("type", ""),
                    "x1": int(zone.get("x1", 0)),
                    "y1": int(zone.get("y1", 0)),
                    "x2": int(zone.get("x2", 0)),
                    "y2": int(zone.get("y2", 0)),
                    "z": int(zone.get("z", 0)),
                }
            )
        return zones

    @staticmethod
    def _normalize_waypoints(raw: List[Dict[str, Any]]) -> List[Dict[str, object]]:
        """Normalize waypoints to standard format."""
        if not raw:
            return []
        result = []
        for wp in raw:
            result.append(
                {
                    "name": wp.get("name", ""),
                    "x": int(wp.get("x", 0)),
                    "y": int(wp.get("y", 0)),
                    "z": int(wp.get("z", 0)),
                }
            )
        return result

    @staticmethod
    def _cities_to_houses(cities: List[Dict[str, Any]]) -> List[Dict[str, object]]:
        """Convert cities/towns to houses format."""
        houses = []
        for city in cities:
            houses.append(
                {
                    "id": city.get("town_id", 0),
                    "name": city.get("name", ""),
                    "temple_x": city.get("temple_x", city.get("x", 0)),
                    "temple_y": city.get("temple_y", city.get("y", 0)),
                    "temple_z": city.get("temple_z", city.get("z", 0)),
                }
            )
        return houses

    # ------------------------------------------------------------------
    # JSON report
    # ------------------------------------------------------------------

    def analyze_to_json(self, path: str, output_path: Optional[str] = None) -> str:
        """Analyze and export to JSON.

        Args:
            path: Path to map file.
            output_path: Optional output path for JSON.
        """
        analysis = self.analyze(path)
        report = analysis.to_dict()

        if output_path:
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(report, indent=2, ensure_ascii=False))

        return json.dumps(report, indent=2, ensure_ascii=False)


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------


def _read_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Read a length-prefixed (uint16) string from bytes."""
    if offset + 2 > len(data):
        return "", offset
    length = struct.unpack_from("<H", data, offset)[0]
    offset += 2
    if offset + length > len(data):
        return "", offset - 2
    try:
        s = data[offset : offset + length].decode("utf-8", errors="replace")
    except UnicodeDecodeError:
        s = data[offset : offset + length].decode("latin-1", errors="replace")
    return s, offset + length
