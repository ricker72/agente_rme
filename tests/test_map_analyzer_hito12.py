"""Tests completos para HITO 12 — Map Analyzer y sub-analizadores."""
import io
import json
import os
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.analyzer.map_analyzer import MapAnalyzer, MapAnalysis
from core.analyzer.spawn_analyzer import SpawnAnalyzer
from core.analyzer.path_analyzer import PathAnalyzer
from core.analyzer.density_analyzer import DensityAnalyzer
from core.analyzer.architecture_analyzer import ArchitectureAnalyzer
from core.analyzer.tile_analyzer import TileAnalyzer
from core.analyzer.style_analyzer import StyleAnalyzer
from core.analyzer.pattern_extractor import PatternExtractor


# ---------------------------------------------------------------------------
# Helpers para crear datos sintéticos
# ---------------------------------------------------------------------------

def _make_minimal_otbm_bytes(width=10, height=10, version=0, tiles=4):
    """Crea bytes OTBM mínimos válidos para testing."""
    buf = bytearray()
    buf.extend(b"OTBM")                          # magic
    buf.extend(struct.pack("<I", version))        # version
    buf.extend(struct.pack("<H", width))          # width
    buf.extend(struct.pack("<H", height))         # height
    buf.extend(struct.pack("<I", 3))              # item_major
    buf.extend(struct.pack("<I", 57))             # item_minor
    # MAP_DATA node
    map_data = bytearray()
    # description string
    desc = b"Test Map"
    map_data.extend(struct.pack("<H", len(desc)))
    map_data.extend(desc)
    # spawn file string
    spawn_file = b"spawn.xml"
    map_data.extend(struct.pack("<H", len(spawn_file)))
    map_data.extend(spawn_file)
    # house file string
    house_file = b"house.xml"
    map_data.extend(struct.pack("<H", len(house_file)))
    map_data.extend(house_file)
    # TILE_AREA child
    tile_area = bytearray()
    tile_area.extend(struct.pack("<H", 0))   # base_x
    tile_area.extend(struct.pack("<H", 0))   # base_y
    tile_area.append(7)                       # base_z
    # Add some TILE nodes
    for i in range(tiles):
        tile = bytearray()
        tile.append(0x00)                     # offset_x
        tile.append(i)                        # offset_y
        tile_area.append(0x03)                 # OTBM_NODE_TILE
        tile_area.extend(struct.pack("<H", len(tile)))
        tile_area.extend(tile)
    # Embed tile_area in map_data
    map_data.append(0x02)  # OTBM_NODE_TILE_AREA
    map_data.extend(struct.pack("<H", len(tile_area)))
    map_data.extend(tile_area)
    # MAP_DATA wrapper
    buf.append(0x01)  # OTBM_NODE_MAP_DATA
    buf.extend(struct.pack("<H", len(map_data)))
    buf.extend(map_data)
    return bytes(buf)


# ---------------------------------------------------------------------------
# MapAnalyzer Tests
# ---------------------------------------------------------------------------

class TestMapAnalyzer(unittest.TestCase):
    """Tests para MapAnalyzer — analizador principal."""

    def setUp(self):
        self.analyzer = MapAnalyzer()

    def test_map_analysis_dataclass_initialization(self):
        """MapAnalysis se inicializa correctamente con defaults."""
        ma = MapAnalysis(source="test.otbm")
        self.assertEqual(ma.source, "test.otbm")
        self.assertEqual(ma.map_size, {})
        self.assertEqual(ma.tile_count, 0)
        self.assertEqual(ma.item_count, 0)
        self.assertEqual(ma.tiles, {})
        self.assertEqual(ma.items, {})
        self.assertEqual(ma.houses, [])
        self.assertEqual(ma.spawns, [])
        self.assertEqual(ma.waypoints, [])
        self.assertIsNone(ma.style)
        self.assertIsNone(ma.path_analysis)
        self.assertIsNone(ma.density_analysis)
        self.assertIsNone(ma.architecture_analysis)

    def test_map_analysis_to_dict(self):
        """to_dict() devuelve todas las claves esperadas."""
        ma = MapAnalysis(source="test.otbm")
        ma.map_size = {"width": 10, "height": 10}
        ma.tile_count = 5
        ma.item_count = 3
        ma.tiles = {"sandstone_floor": 5}
        ma.items = {"item_100": 3}
        ma.style = "issavi"
        d = ma.to_dict()
        self.assertEqual(d["source"], "test.otbm")
        self.assertEqual(d["tile_count"], 5)
        self.assertEqual(d["item_count"], 3)
        self.assertEqual(d["style"], "issavi")
        self.assertIn("top_tiles", d)
        self.assertIn("top_items", d)

    def test_analyze_unsupported_format_raises(self):
        """analyze() lanza ValueError para formatos no soportados."""
        with self.assertRaises(ValueError):
            self.analyzer.analyze("test.unknown")

    def test_analyze_otbm_direct(self):
        """analyze() procesa OTBM vía análisis directo sin importer."""
        with tempfile.NamedTemporaryFile(suffix=".otbm", delete=False) as f:
            f.write(_make_minimal_otbm_bytes(10, 10, 0, 5))
            path = f.name
        try:
            analysis = self.analyzer.analyze(path)
            self.assertIsInstance(analysis, MapAnalysis)
            self.assertEqual(analysis.map_size["width"], 10)
            self.assertEqual(analysis.map_size["height"], 10)
            self.assertGreaterEqual(analysis.tile_count, 0)
        finally:
            os.unlink(path)

    def test_analyze_otbm_with_importer_mock(self):
        """analyze() usa importer si está disponible."""
        mock_importer = MagicMock()
        mock_importer.import_file.return_value = {
            "success": True,
            "world_dict": {
                "width": 10,
                "height": 10,
                "tiles": [
                    {"x": 0, "y": 0, "z": 7, "ground": 406, "items": [], "all_items": []},
                    {"x": 1, "y": 0, "z": 7, "ground": 406, "items": [], "all_items": []},
                ],
                "spawns": [{"monster": "Rat", "x": 5, "y": 5, "z": 7, "radius": 3}],
                "cities": [{"name": "Thais", "town_id": 1, "temple_x": 10, "temple_y": 10, "temple_z": 7}],
                "waypoints": [{"name": "WP1", "x": 0, "y": 0, "z": 7}],
            },
            "stats": {"tiles": 2, "spawns": 1, "cities": 1, "waypoints": 1},
        }
        analyzer = MapAnalyzer(otbm_importer=mock_importer)
        with tempfile.NamedTemporaryFile(suffix=".otbm", delete=False) as f:
            f.write(_make_minimal_otbm_bytes())
            path = f.name
        try:
            analysis = analyzer.analyze(path)
            self.assertIsInstance(analysis, MapAnalysis)
            self.assertEqual(analysis.tile_count, 2)
            self.assertEqual(len(analysis.spawns), 1)
            self.assertEqual(len(analysis.houses), 1)
            self.assertEqual(len(analysis.waypoints), 1)
        finally:
            os.unlink(path)

    def test_analyze_otbm_importer_failure_fallsback(self):
        """Si el importer falla, hace fallback a análisis directo."""
        mock_importer = MagicMock()
        mock_importer.import_file.side_effect = Exception("Boom")
        analyzer = MapAnalyzer(otbm_importer=mock_importer)
        with tempfile.NamedTemporaryFile(suffix=".otbm", delete=False) as f:
            f.write(_make_minimal_otbm_bytes())
            path = f.name
        try:
            analysis = analyzer.analyze(path)
            self.assertIsInstance(analysis, MapAnalysis)
        finally:
            os.unlink(path)

    def test_analyze_to_json(self):
        """analyze_to_json() genera JSON válido."""
        with tempfile.NamedTemporaryFile(suffix=".otbm", delete=False) as f:
            f.write(_make_minimal_otbm_bytes(8, 8))
            path = f.name
        try:
            json_str = self.analyzer.analyze_to_json(path)
            self.assertIsInstance(json_str, str)
            data = json.loads(json_str)
            self.assertIn("source", data)
            self.assertIn("tile_count", data)
        finally:
            os.unlink(path)

    def test_analyze_to_json_with_output_path(self):
        """analyze_to_json() escribe archivo si se proporciona output_path."""
        with tempfile.NamedTemporaryFile(suffix=".otbm", delete=False) as f:
            f.write(_make_minimal_otbm_bytes())
            src_path = f.name
        try:
            out_path = tempfile.mktemp(suffix=".json")
            self.analyzer.analyze_to_json(src_path, output_path=out_path)
            self.assertTrue(os.path.exists(out_path))
            data = json.loads(open(out_path).read())
            self.assertIn("source", data)
            os.unlink(out_path)
        finally:
            os.unlink(src_path)

    def test_extract_binary_tiles_enhanced(self):
        """_extract_binary_tiles_enhanced extrae tiles del binario."""
        data = _make_minimal_otbm_bytes(10, 10)
        result = self.analyzer._extract_binary_tiles_enhanced(data)
        self.assertIsInstance(result, dict)

    def test_extract_binary_items(self):
        """_extract_binary_items extrae items del binario."""
        data = _make_minimal_otbm_bytes(10, 10)
        result = self.analyzer._extract_binary_items(data)
        self.assertIsInstance(result, dict)

    def test_extract_binary_waypoints(self):
        """_extract_binary_waypoints retorna lista."""
        data = _make_minimal_otbm_bytes()
        result = self.analyzer._extract_binary_waypoints(data)
        self.assertIsInstance(result, list)

    def test_extract_binary_houses(self):
        """_extract_binary_houses retorna lista."""
        data = _make_minimal_otbm_bytes()
        result = self.analyzer._extract_binary_houses(data)
        self.assertIsInstance(result, list)

    def test_extract_binary_floors(self):
        """_extract_binary_floors retorna floors desde TILE_AREA."""
        data = _make_minimal_otbm_bytes()
        floors = self.analyzer._extract_binary_floors(data)
        self.assertIsInstance(floors, list)
        self.assertIn(7, floors)

    def test_normalize_waypoints(self):
        """_normalize_waypoints normaliza formato."""
        raw = [{"name": "wp1", "x": 10, "y": 20, "z": 7}]
        normalized = self.analyzer._normalize_waypoints(raw)
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["name"], "wp1")
        self.assertEqual(normalized[0]["x"], 10)

    def test_normalize_waypoints_empty(self):
        """_normalize_waypoints con lista vacía."""
        self.assertEqual(self.analyzer._normalize_waypoints([]), [])

    def test_cities_to_houses(self):
        """_cities_to_houses convierte ciudades a formato houses."""
        cities = [{"name": "Thais", "town_id": 1, "temple_x": 10, "temple_y": 10, "temple_z": 7}]
        houses = self.analyzer._cities_to_houses(cities)
        self.assertEqual(len(houses), 1)
        self.assertEqual(houses[0]["name"], "Thais")

    def test_read_file_bytes_not_found(self):
        """_read_file_bytes retorna bytes vacíos si no existe."""
        result = self.analyzer._read_file_bytes("/nonexistent/file.otbm")
        self.assertEqual(result, b"")

    def test_extract_map_size(self):
        """_extract_map_size desde XML."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<root><map><size x="50" y="60"/></map></root>')
        size = self.analyzer._extract_map_size(root)
        self.assertEqual(size["width"], 50)
        self.assertEqual(size["height"], 60)

    def test_extract_floors_xml(self):
        """_extract_floors desde XML."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('<root><map><tile z="7"/><tile z="8"/><tile z="7"/></map></root>')
        floors = self.analyzer._extract_floors(root)
        self.assertEqual(floors, [7, 8])

    def test_extract_houses_xml(self):
        """_extract_houses desde XML."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('''
            <root><houses>
                <house id="1" name="Thais" rent="100" temple_x="5" temple_y="5" temple_z="7"/>
            </houses></root>
        ''')
        houses = self.analyzer._extract_houses(root)
        self.assertEqual(len(houses), 1)
        self.assertEqual(houses[0]["name"], "Thais")
        self.assertEqual(houses[0]["rent"], 100)

    def test_extract_waypoints_xml(self):
        """_extract_waypoints desde XML."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('''
            <root><waypoints>
                <waypoint name="Start" x="0" y="0" z="7"/>
            </waypoints></root>
        ''')
        wps = self.analyzer._extract_waypoints(root)
        self.assertEqual(len(wps), 1)
        self.assertEqual(wps[0]["name"], "Start")

    def test_extract_zones(self):
        """_extract_zones desde XML."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('''
            <root><zones>
                <zone name="PvP" type="pvp" x1="0" y1="0" x2="100" y2="100" z="7"/>
            </zones></root>
        ''')
        zones = self.analyzer._extract_zones(root)
        self.assertEqual(len(zones), 1)
        self.assertEqual(zones[0]["name"], "PvP")

    def test_run_derived_analysis(self):
        """_run_derived_analysis puebla los 3 análisis derivados."""
        ma = MapAnalysis(source="test")
        ma.tiles = {"sandstone_floor": 100}
        ma.items = {"item_100": 50}
        ma.spawns = [{"monster": "rat", "x": 5, "y": 5, "z": 7, "radius": 3}]
        ma.waypoints = [{"name": "wp1", "x": 0, "y": 0, "z": 7}]
        ma.map_size = {"width": 100, "height": 100}
        self.analyzer._run_derived_analysis(ma)
        self.assertIsNotNone(ma.path_analysis)
        self.assertIsNotNone(ma.density_analysis)
        self.assertIsNotNone(ma.architecture_analysis)


# ---------------------------------------------------------------------------
# SpawnAnalyzer Tests
# ---------------------------------------------------------------------------

class TestSpawnAnalyzer(unittest.TestCase):
    """Tests para SpawnAnalyzer."""

    def setUp(self):
        self.analyzer = SpawnAnalyzer()

    def test_analyze_otbm_spawns_empty(self):
        """analyze_otbm_spawns con lista vacía."""
        result = self.analyzer.analyze_otbm_spawns([])
        self.assertEqual(result, [])

    def test_analyze_otbm_spawns_with_data(self):
        """analyze_otbm_spawns convierte spawns del world_dict."""
        raw = [
            {"monster": "Rat", "x": 10, "y": 20, "z": 7, "radius": 5, "respawn": 60, "direction": 2},
            {"name": "Dragon", "x": 30, "y": 40, "z": 7, "radius": 8},
        ]
        result = self.analyzer.analyze_otbm_spawns(raw)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["monster"], "Rat")
        self.assertEqual(result[0]["respawn"], 60)
        self.assertEqual(result[1]["monster"], "Dragon")

    def test_analyze_otbm_direct_empty(self):
        """analyze_otbm_direct con datos vacíos."""
        result = self.analyzer.analyze_otbm_direct(b"")
        self.assertEqual(result, [])

    def test_analyze_otbm_direct_no_spawns(self):
        """analyze_otbm_direct con OTBM sin spawns."""
        data = _make_minimal_otbm_bytes()
        result = self.analyzer.analyze_otbm_direct(data)
        self.assertIsInstance(result, list)

    def test_analyze_spawn_xml(self):
        """analyze_spawn_xml extrae spawns desde XML."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('''
            <root><spawns>
                <spawn monster="Rat" x="10" y="20" z="7" radius="3"/>
                <spawn monster="Dragon" x="30" y="40" z="7" radius="5"/>
            </spawns></root>
        ''')
        spawns = self.analyzer.analyze_spawn_xml(root)
        self.assertEqual(len(spawns), 2)
        self.assertEqual(spawns[0]["monster"], "Rat")
        self.assertEqual(spawns[1]["radius"], 5)

    def test_parse_monsters_in_area_empty(self):
        """_parse_monsters_in_area sin monsters."""
        data = b"\x00" * 100
        result = self.analyzer._parse_monsters_in_area(data, 0, len(data))
        self.assertEqual(result, [])

    def test_classify_zones_empty(self):
        """_classify_zones con contador vacío."""
        from collections import Counter
        result = self.analyzer._classify_zones(Counter())
        self.assertEqual(result, {})

    def test_classify_zones_endgame(self):
        """_classify_zones detecta endgame."""
        from collections import Counter
        c = Counter({"rat": 300})
        result = self.analyzer._classify_zones(c)
        self.assertEqual(result["zone"], "endgame")

    def test_classify_zones_hard(self):
        """_classify_zones detecta hard."""
        from collections import Counter
        c = Counter({"rat": 150})
        result = self.analyzer._classify_zones(c)
        self.assertEqual(result["zone"], "hard")

    def test_classify_zones_medium(self):
        """_classify_zones detecta medium."""
        from collections import Counter
        c = Counter({"rat": 80})
        result = self.analyzer._classify_zones(c)
        self.assertEqual(result["zone"], "medium")

    def test_classify_zones_easy(self):
        """_classify_zones detecta easy."""
        from collections import Counter
        c = Counter({"rat": 10})
        result = self.analyzer._classify_zones(c)
        self.assertEqual(result["zone"], "easy")

    def test_summarize_spawns_empty(self):
        """summarize_spawns con lista vacía."""
        result = self.analyzer.summarize_spawns([])
        self.assertEqual(result["total_spawns"], 0)
        self.assertEqual(result["unique_monsters"], 0)
        self.assertEqual(result["zone_classification"], "empty")

    def test_summarize_spawns_with_data(self):
        """summarize_spawns genera resumen correcto."""
        spawns = [
            {"monster": "Rat", "x": 10, "y": 20, "z": 7, "radius": 3},
            {"monster": "Rat", "x": 15, "y": 25, "z": 7, "radius": 4},
            {"monster": "Dragon", "x": 30, "y": 40, "z": 8, "radius": 8},
        ]
        result = self.analyzer.summarize_spawns(spawns)
        self.assertEqual(result["total_spawns"], 3)
        self.assertEqual(result["unique_monsters"], 2)
        self.assertEqual(len(result["top_monsters"]), 2)
        self.assertEqual(result["floors_with_spawns"], [7, 8])


# ---------------------------------------------------------------------------
# PathAnalyzer Tests
# ---------------------------------------------------------------------------

class TestPathAnalyzer(unittest.TestCase):
    """Tests para PathAnalyzer."""

    def setUp(self):
        self.analyzer = PathAnalyzer()

    def test_analyze_empty_waypoints(self):
        """analyze con waypoints vacíos."""
        result = self.analyzer.analyze([], [])
        self.assertEqual(result["total_waypoints"], 0)
        self.assertEqual(result["connectivity_summary"], "No waypoints available")

    def test_analyze_with_waypoints(self):
        """analyze con waypoints genera análisis completo."""
        waypoints = [
            {"name": "A", "x": 0, "y": 0, "z": 7},
            {"name": "B", "x": 10, "y": 0, "z": 7},
            {"name": "C", "x": 0, "y": 10, "z": 7},
        ]
        spawns = [
            {"monster": "Rat", "x": 5, "y": 5, "z": 7, "radius": 3},
        ]
        result = self.analyzer.analyze(waypoints, spawns)
        self.assertEqual(result["total_waypoints"], 3)
        self.assertTrue(len(result["waypoint_distances"]) > 0)
        self.assertTrue(len(result["nearest_waypoint_to_spawns"]) > 0)
        self.assertIn("nodes", result["path_graph"])
        self.assertIn("edges", result["path_graph"])
        self.assertIsNotNone(result.get("furthest_waypoints"))
        self.assertIsNotNone(result.get("closest_waypoints"))
        self.assertTrue(len(result["clustering"]) > 0)

    def test_manhattan_distance(self):
        """_manhattan calcula distancia correcta."""
        a = {"x": 0, "y": 0}
        b = {"x": 3, "y": 4}
        self.assertEqual(self.analyzer._manhattan(a, b), 7)

    def test_euclidean_distance(self):
        """_euclidean calcula distancia euclidiana."""
        a = {"x": 0, "y": 0}
        b = {"x": 3, "y": 4}
        self.assertAlmostEqual(self.analyzer._euclidean(a, b), 5.0)

    def test_same_floor(self):
        """_same_floor compara z."""
        a = {"z": 7}
        b = {"z": 7}
        c = {"z": 8}
        self.assertTrue(self.analyzer._same_floor(a, b))
        self.assertFalse(self.analyzer._same_floor(a, c))

    def test_compute_waypoint_distances(self):
        """_compute_waypoint_distances calcula todas las distancias."""
        wps = [
            {"name": "A", "x": 0, "y": 0, "z": 7},
            {"name": "B", "x": 5, "y": 0, "z": 7},
        ]
        dists = self.analyzer._compute_waypoint_distances(wps)
        self.assertEqual(len(dists), 1)
        self.assertEqual(dists[0]["distance"], 5)

    def test_nearest_waypoint_for_spawns(self):
        """_nearest_waypoint_for_spawns encuentra el más cercano."""
        wps = [
            {"name": "A", "x": 0, "y": 0, "z": 7},
            {"name": "B", "x": 50, "y": 50, "z": 7},
        ]
        spawns = [{"monster": "Rat", "x": 5, "y": 5, "z": 7}]
        nearest = self.analyzer._nearest_waypoint_for_spawns(wps, spawns)
        self.assertEqual(len(nearest), 1)
        self.assertEqual(nearest[0]["waypoint"], "A")

    def test_nearest_waypoint_for_spawns_empty(self):
        """_nearest_waypoint_for_spawns con entradas vacías."""
        result = self.analyzer._nearest_waypoint_for_spawns([], [])
        self.assertEqual(result, [])

    def test_summarize_connectivity(self):
        """_summarize_connectivity genera resumen."""
        wps = [{"name": "A"}, {"name": "B"}]
        dists = [{"from": "A", "to": "B", "distance": 10}]
        summary = self.analyzer._summarize_connectivity(wps, dists)
        self.assertIn("2 waypoints", summary)

    def test_find_furthest_pair_empty(self):
        """_find_furthest_pair con lista vacía."""
        self.assertIsNone(self.analyzer._find_furthest_pair([]))

    def test_find_closest_pair_empty(self):
        """_find_closest_pair con lista vacía."""
        self.assertIsNone(self.analyzer._find_closest_pair([]))

    def test_cluster_waypoints_empty(self):
        """_cluster_waypoints con lista vacía."""
        self.assertEqual(self.analyzer._cluster_waypoints([]), [])

    def test_cluster_waypoints_groups(self):
        """_cluster_waypoints agrupa waypoints cercanos."""
        wps = [
            {"name": "A", "x": 0, "y": 0, "z": 7},
            {"name": "B", "x": 5, "y": 5, "z": 7},
            {"name": "C", "x": 200, "y": 200, "z": 7},
        ]
        clusters = self.analyzer._cluster_waypoints(wps, max_distance=50)
        # A y B deberían estar en el mismo cluster, C en otro
        self.assertGreaterEqual(len(clusters), 2)
        self.assertEqual(sum(c["size"] for c in clusters), 3)


# ---------------------------------------------------------------------------
# DensityAnalyzer Tests
# ---------------------------------------------------------------------------

class TestDensityAnalyzer(unittest.TestCase):
    """Tests para DensityAnalyzer."""

    def setUp(self):
        self.analyzer = DensityAnalyzer()

    def test_analyze_empty(self):
        """analyze con datos vacíos."""
        result = self.analyzer.analyze({}, {}, [], {"width": 100, "height": 100})
        self.assertEqual(result["map_area"], 10000)
        self.assertEqual(result["total_tiles"], 0)
        self.assertEqual(result["total_items"], 0)
        self.assertEqual(result["overall_density_score"], 0)
        self.assertEqual(result["density_category"], "very_low")

    def test_analyze_with_data(self):
        """analyze con datos poblados."""
        tiles = {"sandstone_floor": 100, "polished_stone": 50}
        items = {"item_100": 30, "item_200": 20}
        spawns = [{"monster": "Rat", "x": 10, "y": 10, "z": 7, "radius": 3} for _ in range(10)]
        result = self.analyzer.analyze(
            tiles, items, spawns, {"width": 100, "height": 100}
        )
        self.assertEqual(result["total_tiles"], 150)
        self.assertEqual(result["total_items"], 50)
        self.assertEqual(result["total_spawns"], 10)
        self.assertIn("tile_density", result)
        self.assertIn("item_density", result)
        self.assertIn("spawn_density", result)
        self.assertIn("spawn_heatmap", result)
        self.assertGreater(result["overall_density_score"], 0)

    def test_compute_tile_density(self):
        """_compute_tile_density con datos."""
        tiles = {"a": 50, "b": 30, "c": 20}
        density = self.analyzer._compute_tile_density(tiles, 100)
        self.assertAlmostEqual(density["total_density"], 1.0)
        self.assertEqual(density["unique_tile_types"], 3)
        self.assertEqual(len(density["top_types"]), 3)

    def test_compute_tile_density_empty(self):
        """_compute_tile_density vacío."""
        result = self.analyzer._compute_tile_density({}, 100)
        self.assertEqual(result["total_density"], 0.0)

    def test_compute_item_density(self):
        """_compute_item_density calcula items por tile."""
        items = {"item_1": 10, "item_2": 5}
        result = self.analyzer._compute_item_density(items, 5)
        self.assertEqual(result["items_per_tile"], 3.0)
        self.assertEqual(result["unique_item_types"], 2)

    def test_compute_item_density_empty(self):
        """_compute_item_density vacío."""
        result = self.analyzer._compute_item_density({}, 10)
        self.assertEqual(result["items_per_tile"], 0.0)

    def test_compute_spawn_density(self):
        """_compute_spawn_density calcula métricas."""
        spawns = [{"monster": "Rat", "x": 50, "y": 50, "z": 7, "radius": 3}]
        result = self.analyzer._compute_spawn_density(spawns, 10000, 100, 100)
        self.assertGreater(result["spawns_per_sq"], 0)
        self.assertEqual(result["concentration_zone"], "SE")

    def test_compute_spawn_density_empty(self):
        """_compute_spawn_density vacío."""
        result = self.analyzer._compute_spawn_density([], 10000, 100, 100)
        self.assertEqual(result["spawns_per_sq"], 0.0)
        self.assertEqual(result["concentration_zone"], "none")

    def test_compute_spawn_heatmap(self):
        """_compute_spawn_heatmap genera heatmap."""
        spawns = [
            {"x": 10, "y": 10, "z": 7},
            {"x": 20, "y": 20, "z": 7},
            {"x": 80, "y": 80, "z": 7},
        ]
        cells = self.analyzer._compute_spawn_heatmap(spawns, 100, 100, grid_size=25)
        self.assertGreater(len(cells), 0)

    def test_compute_spawn_heatmap_empty(self):
        """_compute_spawn_heatmap vacío."""
        self.assertEqual(self.analyzer._compute_spawn_heatmap([], 100, 100), [])

    def test_compute_floor_distribution(self):
        """_compute_floor_distribution agrupa por floor."""
        spawns = [
            {"z": 7}, {"z": 7}, {"z": 8}
        ]
        dist = self.analyzer._compute_floor_distribution(spawns)
        self.assertEqual(dist["by_floor"]["7"], 2)
        self.assertEqual(dist["by_floor"]["8"], 1)
        self.assertEqual(dist["dominant_floor"], 7)

    def test_compute_floor_distribution_empty(self):
        """_compute_floor_distribution vacío."""
        dist = self.analyzer._compute_floor_distribution([])
        self.assertEqual(dist["by_floor"], {})

    def test_compute_overall_density(self):
        """_compute_overall_density calcula score."""
        score = self.analyzer._compute_overall_density(100, 50, 5, 100)
        self.assertGreater(score, 0)

    def test_categorize_density(self):
        """_categorize_density asigna categoría."""
        self.assertEqual(self.analyzer._categorize_density(90), "very_high")
        self.assertEqual(self.analyzer._categorize_density(70), "high")
        self.assertEqual(self.analyzer._categorize_density(50), "medium")
        self.assertEqual(self.analyzer._categorize_density(30), "low")
        self.assertEqual(self.analyzer._categorize_density(10), "very_low")


# ---------------------------------------------------------------------------
# ArchitectureAnalyzer Tests
# ---------------------------------------------------------------------------

class TestArchitectureAnalyzer(unittest.TestCase):
    """Tests para ArchitectureAnalyzer."""

    def setUp(self):
        self.analyzer = ArchitectureAnalyzer()

    def test_analyze_empty(self):
        """analyze con datos vacíos."""
        result = self.analyzer.analyze({}, {}, [], [], [], {"width": 100, "height": 100})
        self.assertIn("structural_composition", result)
        self.assertIn("urban_zones", result)
        self.assertIn("wall_analysis", result)
        self.assertIn("door_analysis", result)
        self.assertIn("building_category", result)
        self.assertIn("infrastructure_score", result)

    def test_analyze_with_data(self):
        """analyze con datos poblados."""
        tiles = {"polished_stone": 200, "sandstone_floor": 100, "roshamuul_floor": 50}
        items = {"item_100": 10, "item_101": 5, "item_200": 20}
        houses = [{"name": "Thais", "town_id": 1, "temple_x": 10, "temple_y": 10}]
        spawns = [{"monster": "Dragon", "x": 50, "y": 50, "z": 7, "radius": 5}]
        waypoints = [{"name": "WP1", "x": 0, "y": 0, "z": 7}]
        result = self.analyzer.analyze(
            tiles, items, houses, spawns, waypoints, {"width": 100, "height": 100}
        )
        self.assertEqual(result["urban_zones"]["zone_type"], "camp")
        self.assertGreater(result["infrastructure_score"]["total_score"], 0)
        self.assertTrue(len(result["zone_classification"]) > 0)

    def test_structural_composition(self):
        """_analyze_structural_composition clasifica suelos."""
        tiles = {"polished_stone": 100, "sandstone_floor": 50, "mossy_stone": 30}
        comp = self.analyzer._analyze_structural_composition(tiles)
        self.assertEqual(comp["dominant_category"], "urban")
        self.assertTrue(comp["is_urban"])
        self.assertFalse(comp["is_dungeon"])

    def test_structural_composition_empty(self):
        """_analyze_structural_composition vacío."""
        comp = self.analyzer._analyze_structural_composition({})
        self.assertEqual(comp["dominant"], "unknown")

    def test_detect_urban_zones(self):
        """_detect_urban_zones clasifica asentamientos."""
        houses = [{"name": "Thais"}, {"name": "Carlin"}, {"name": "Venore"}]
        result = self.analyzer._detect_urban_zones({"polished_stone": 500}, houses)
        self.assertEqual(result["zone_type"], "village")
        self.assertEqual(result["house_count"], 3)
        self.assertEqual(result["estimated_population"], 15)

    def test_detect_urban_zones_wilderness(self):
        """_detect_urban_zones sin houses."""
        result = self.analyzer._detect_urban_zones({}, [])
        self.assertEqual(result["zone_type"], "wilderness")

    def test_detect_urban_zones_city(self):
        """_detect_urban_zones con muchas houses = city."""
        houses = [{"name": f"House{i}"} for i in range(15)]
        result = self.analyzer._detect_urban_zones({"polished_stone": 1000}, houses)
        self.assertEqual(result["zone_type"], "city")

    def test_analyze_walls(self):
        """_analyze_walls cuenta muros por ID."""
        items = {"item_101": 10, "item_102": 5, "item_9999": 100}
        result = self.analyzer._analyze_walls(items)
        self.assertEqual(result["total_walls"], 15)
        self.assertEqual(result["wall_types"], 2)

    def test_analyze_doors(self):
        """_analyze_doors cuenta puertas por ID."""
        items = {"item_1209": 5, "item_5000": 3, "item_9999": 100}
        result = self.analyzer._analyze_doors(items)
        self.assertEqual(result["total_doors"], 8)
        self.assertEqual(result["door_types"], 2)

    def test_classify_building(self):
        """_classify_building clasifica tipo de construcción."""
        # 10 houses en 100x100 => house_density = 10 / (100*100/10000) = 10/1 = 10 > 5 => metropolis
        houses = [{"name": "t1"} for _ in range(10)]
        spawns = [{"monster": "Rat"} for _ in range(50)]
        result = self.analyzer._classify_building(houses, spawns, {"width": 100, "height": 100})
        self.assertEqual(result["building_type"], "metropolis")

    def test_classify_building_wilderness(self):
        """_classify_building sin houses ni spawns relevantes."""
        result = self.analyzer._classify_building([], [], {"width": 100, "height": 100})
        self.assertEqual(result["building_type"], "wilderness")

    def test_infrastructure_score(self):
        """_compute_infrastructure_score calcula score."""
        tiles = {"polished_stone": 300}
        items = {"item_100": 50}
        houses = [{"name": "A"}, {"name": "B"}]
        waypoints = [{"name": "wp1"}, {"name": "wp2"}, {"name": "wp3"}]
        score = self.analyzer._compute_infrastructure_score(
            tiles, items, houses, waypoints, {"width": 100, "height": 100}
        )
        self.assertGreater(score["total_score"], 0)
        self.assertIn("breakdown", score)

    def test_classify_zones(self):
        """_classify_zones clasifica zonas."""
        tiles = {"polished_stone": 100, "sandstone_floor": 600}
        items = {}
        houses = [{"name": "T"}]
        spawns = [{"monster": "D", "x": 5, "y": 5, "z": 7, "radius": 3}]
        zones = self.analyzer._classify_zones(tiles, items, houses, spawns)
        self.assertTrue(any(z["zone"] == "urban" for z in zones))
        self.assertTrue(any(z["zone"] == "hunting" for z in zones))
        self.assertTrue(any(z["zone"] == "natural" for z in zones))

    def test_complexity_metrics(self):
        """_compute_complexity calcula métricas."""
        tiles = {"a": 1, "b": 2}
        items = {"x": 1, "y": 2, "z": 3}
        houses = [{"name": "A"}]
        spawns = [{"monster": "A"}, {"monster": "B"}]
        waypoints = [{"name": "wp1"}]
        metrics = self.analyzer._compute_complexity(
            tiles, items, houses, spawns, waypoints
        )
        self.assertIn("complexity_score", metrics)
        self.assertIn("complexity_level", metrics)
        self.assertIn("components", metrics)


# ---------------------------------------------------------------------------
# TileAnalyzer Tests
# ---------------------------------------------------------------------------

class TestTileAnalyzer(unittest.TestCase):
    """Tests existentes de TileAnalyzer."""

    def setUp(self):
        self.analyzer = TileAnalyzer()

    def test_analyze_xml_tiles(self):
        """analyze_xml_tiles procesa XML tiles."""
        import xml.etree.ElementTree as ET
        root = ET.fromstring('''
            <root><map>
                <tile ground="393"/>
                <tile ground="415"/>
                <tile ground="393"><item id="100"/></tile>
            </map></root>
        ''')
        result = self.analyzer.analyze_xml_tiles(root)
        self.assertIn("sandstone_floor", result)
        self.assertEqual(result.get("sandstone_floor"), 2)

    def test_summarize_binary_tiles(self):
        """summarize_binary_tiles extrae tiles de binario con nombre textual."""
        # summarize_binary_tiles busca IDs como strings ASCII en el binario
        data = b"393\x00415\x00"
        result = self.analyzer.summarize_binary_tiles(data)
        self.assertIn("sandstone_floor", result)

    def test_summarize_ground_usage(self):
        """summarize_ground_usage combina tiles."""
        tiles = [{"a": 1, "b": 2}, {"a": 3, "c": 1}]
        result = self.analyzer.summarize_ground_usage(tiles)
        self.assertEqual(result["a"], 4)
        self.assertEqual(result["b"], 2)
        self.assertEqual(result["c"], 1)


# ---------------------------------------------------------------------------
# StyleAnalyzer Tests
# ---------------------------------------------------------------------------

class TestStyleAnalyzer(unittest.TestCase):
    """Tests para StyleAnalyzer."""

    def setUp(self):
        self.analyzer = StyleAnalyzer()

    def test_detect_style_empty(self):
        """detect_style con tiles vacíos."""
        self.assertEqual(self.analyzer.detect_style({}), "unknown")

    def test_detect_style_issavi(self):
        """detect_style identifica issavi."""
        tiles = {"sandstone_floor": 100, "polished_stone": 50}
        self.assertEqual(self.analyzer.detect_style(tiles), "issavi")

    def test_detect_style_roshamuul(self):
        """detect_style identifica roshamuul."""
        tiles = {"roshamuul_floor": 200, "polished_stone": 10}
        self.assertEqual(self.analyzer.detect_style(tiles), "roshamuul")

    def test_detect_style_unknown_when_no_match(self):
        """detect_style retorna unknown si no hay match."""
        tiles = {"unknown_floor": 100}
        self.assertEqual(self.analyzer.detect_style(tiles), "unknown")

    def test_summarize_style(self):
        """summarize_style genera resumen."""
        tiles = {"sandstone_floor": 100, "polished_stone": 50}
        houses = [{"name": "A"}, {"name": "B"}]
        summary = self.analyzer.summarize_style(tiles, houses)
        self.assertEqual(summary["dominant_style"], "issavi")
        self.assertEqual(summary["house_count"], 2)


# ---------------------------------------------------------------------------
# PatternExtractor Tests
# ---------------------------------------------------------------------------

class TestPatternExtractor(unittest.TestCase):
    """Tests para PatternExtractor."""

    def setUp(self):
        self.extractor = PatternExtractor()

    def test_extract_pattern(self):
        """extract_pattern genera patrón."""
        tiles = {"sandstone_floor": 100, "wall_1": 10, "decoration_1": 5}
        pattern = self.extractor.extract_pattern(
            source="test.otbm",
            style="issavi",
            tile_stats=tiles,
            width=10,
            height=10,
            floors=[7],
        )
        self.assertEqual(pattern["pattern"], "test_otbm")
        self.assertEqual(pattern["style"], "issavi")
        self.assertEqual(pattern["width"], 10)
        self.assertIn("sandstone_floor", pattern["ground_stats"])
        self.assertIn("wall_1", pattern["wall_stats"])

    def test_save_pattern(self):
        """save_pattern escribe a archivo."""
        pattern = {"pattern": "test", "source": "x"}
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            self.extractor.save_pattern(pattern, path)
            self.assertTrue(os.path.exists(path))
            data = json.loads(open(path).read())
            self.assertEqual(data["pattern"], "test")
        finally:
            os.unlink(path)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    unittest.main()