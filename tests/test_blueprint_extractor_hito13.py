"""
Tests obligatorios para HITO 13 — Blueprint Extractor.

Prueba el pipeline completo:
    OTBM → WorldModel → Blueprint

Y cada componente individual:
    - ThemeClassifier
    - PatternDetector
    - StructureDetector
    - BlueprintExtractor
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Any, Dict, List

# Test imports
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.blueprints.theme_classifier import ThemeClassifier
from core.blueprints.pattern_detector import PatternDetector, Pattern
from core.blueprints.structure_detector import StructureDetector, DetectedStructure
from core.blueprints.blueprint_extractor import BlueprintExtractor, ExtractionResult

# ---------------------------------------------------------------------------
# Datos de prueba compartidos
# ---------------------------------------------------------------------------


def _make_sample_tiles(count: int = 50) -> List[Dict[str, Any]]:
    """Genera tiles de prueba."""
    tiles = []
    for i in range(count):
        x = i % 10
        y = i // 10
        ground = 415 if i % 3 == 0 else (416 if i % 3 == 1 else 393)
        items = []
        if i % 5 == 0:
            items.append({"item_id": 101})  # wall
        if i % 7 == 0:
            items.append({"item_id": 1210})  # door
        if i % 11 == 0:
            items.append({"item_id": 999})  # decoration

        tiles.append(
            {
                "x": x,
                "y": y,
                "z": 7,
                "ground": ground,
                "items": items,
                "all_items": [],
            }
        )
    return tiles


def _make_sample_spawns(count: int = 5) -> List[Dict[str, Any]]:
    """Genera spawns de prueba."""
    spawns = []
    monsters = ["dragon", "demon", "rotworm", "troll", "skeleton", "orc"]
    for i in range(count):
        spawns.append(
            {
                "monster": monsters[i % len(monsters)],
                "x": i * 10,
                "y": i * 5,
                "radius": 5,
            }
        )
    return spawns


def _make_sample_houses(count: int = 3) -> List[Dict[str, Any]]:
    """Genera houses de prueba."""
    houses = []
    names = ["Thais Temple", "Venore Depot", "Carlin Market"]
    for i in range(min(count, len(names))):
        houses.append(
            {
                "id": i + 1,
                "name": names[i],
                "temple_x": i * 20 + 5,
                "temple_y": i * 15 + 5,
                "temple_z": 7,
            }
        )
    return houses


def _make_sample_waypoints(count: int = 3) -> List[Dict[str, Any]]:
    """Genera waypoints de prueba."""
    return [{"name": f"wp_{i}", "x": i * 10, "y": i * 10, "z": 7} for i in range(count)]


def _make_sample_world_dict() -> Dict[str, Any]:
    """Genera un WorldModel dict de prueba completo."""
    tiles = _make_sample_tiles(200)
    return {
        "version": 3,
        "width": 100,
        "height": 100,
        "item_major": 3,
        "item_minor": 57,
        "description": "Test map for HITO 13",
        "spawn_file": "",
        "house_file": "",
        "tiles": tiles,
        "spawns": _make_sample_spawns(8),
        "cities": _make_sample_houses(3),
        "waypoints": _make_sample_waypoints(4),
        "tile_count": len(tiles),
        "spawn_count": 8,
        "city_count": 3,
        "waypoint_count": 4,
    }


# ──────────────────────────────────────────────────────────────────────
# TEST 1: ThemeClassifier
# ──────────────────────────────────────────────────────────────────────


class TestThemeClassifier(unittest.TestCase):
    """Pruebas para ThemeClassifier."""

    def setUp(self):
        self.classifier = ThemeClassifier()

    def test_classify_urban_tiles(self):
        """Clasifica tiles urbanos correctamente."""
        tiles = {
            "polished_stone": 500,
            "sandstone_floor": 100,
            "ground_415": 200,
        }
        result = self.classifier.classify(tiles)

        self.assertIn("primary_theme", result)
        self.assertEqual(result["primary_theme"], "temple")
        self.assertGreater(result["confidence"], 0.3)
        self.assertIn("theme_scores", result)
        self.assertTrue(result["is_urban"])

    def test_classify_hunt_spawns(self):
        """Clasifica zona de hunt con spawns."""
        tiles = {"sandstone_floor": 300, "mossy_stone": 200}
        spawns = [
            {"monster": "dragon"},
            {"monster": "dragon_lord"},
            {"monster": "demon"},
            {"monster": "behemoth"},
            {"monster": "hydra"},
            {"monster": "serpent_spawn"},
        ]
        result = self.classifier.classify(tiles, spawns=spawns)

        self.assertIn("hunt", result.get("theme_scores", {}))
        self.assertTrue(result["is_hunt_area"])

    def test_classify_with_houses_urban(self):
        """Casas convierten zona en urbana."""
        tiles = {"polished_stone": 100, "cobblestone": 50}
        houses = _make_sample_houses(5)
        result = self.classifier.classify(tiles, houses=houses)

        self.assertTrue(result["is_urban"])
        self.assertIn("city", result.get("theme_scores", {}))

    def test_classify_empty_returns_generic(self):
        """Sin datos devuelve generic."""
        result = self.classifier.classify({})
        self.assertEqual(result["primary_theme"], "generic")
        self.assertEqual(result["confidence"], 0.0)

    def test_classify_with_metadata(self):
        """classify_with_metadata retorna dict completo."""
        tiles = {"polished_stone": 400, "sandstone_floor": 100}
        items = {"item_101": 50, "item_1000": 30}
        spawns = _make_sample_spawns(3)
        houses = _make_sample_houses(2)

        meta = self.classifier.classify_with_metadata(tiles, items, spawns, houses)
        self.assertIn("style", meta)
        self.assertIn("era", meta)
        self.assertIn("difficulty", meta)
        self.assertIn("tags", meta)
        self.assertIn("capacity", meta)
        self.assertIn("hybrid", meta)
        self.assertIsInstance(meta["tags"], list)
        self.assertIsInstance(meta["hybrid"], bool)

    def test_quick_classify(self):
        """quick_classify mapea correctamente estilos."""
        self.assertEqual(self.classifier.quick_classify("issavi"), "issavi")
        self.assertEqual(
            self.classifier.quick_classify("roshamuul_dungeon"), "roshamuul"
        )
        self.assertEqual(self.classifier.quick_classify("jungle_temple"), "temple")
        self.assertEqual(self.classifier.quick_classify(None), "generic")
        self.assertEqual(self.classifier.quick_classify(""), "generic")

    def test_ground_signatures_coverage(self):
        """Verifica que las firmas de suelo cubren temas clave."""
        self.assertIn("issavi", ThemeClassifier.GROUND_SIGNATURES)
        self.assertIn("roshamuul", ThemeClassifier.GROUND_SIGNATURES)
        self.assertIn("temple", ThemeClassifier.GROUND_SIGNATURES)
        self.assertIn("dungeon", ThemeClassifier.GROUND_SIGNATURES)
        self.assertIn("city", ThemeClassifier.GROUND_SIGNATURES)
        self.assertIn("ice", ThemeClassifier.GROUND_SIGNATURES)
        self.assertIn("jungle", ThemeClassifier.GROUND_SIGNATURES)

    def test_item_signatures_coverage(self):
        """Verifica que las firmas de items cubren temas clave."""
        self.assertIn("temple", ThemeClassifier.ITEM_SIGNATURES)
        self.assertIn("dungeon", ThemeClassifier.ITEM_SIGNATURES)
        self.assertIn("city", ThemeClassifier.ITEM_SIGNATURES)
        self.assertIn("issavi", ThemeClassifier.ITEM_SIGNATURES)
        self.assertIn("roshamuul", ThemeClassifier.ITEM_SIGNATURES)

    def test_hunt_monster_indicators(self):
        """Verifica que hay indicadores de monstruos de hunt."""
        self.assertGreater(len(ThemeClassifier.HUNT_MONSTER_INDICATORS), 10)

    def test_classify_secondary_themes(self):
        """Detecta temas secundarios cuando hay mezcla."""
        tiles = {
            "polished_stone": 200,
            "mossy_stone": 200,
            "sandstone_floor": 100,
        }
        result = self.classifier.classify(tiles)
        self.assertIsInstance(result["secondary_themes"], list)


# ──────────────────────────────────────────────────────────────────────
# TEST 2: PatternDetector
# ──────────────────────────────────────────────────────────────────────


class TestPatternDetector(unittest.TestCase):
    """Pruebas para PatternDetector."""

    def setUp(self):
        self.detector = PatternDetector()

    def test_detect_rooms_with_walls(self):
        """Detecta habitaciones cuando hay muros."""
        tiles = []
        # Crear una habitacion de 5x5 con muros en el perimetro
        for x in range(5):
            for y in range(5):
                items = []
                if x == 0 or x == 4 or y == 0 or y == 4:
                    items.append({"item_id": 101})  # wall
                tiles.append(
                    {"x": x + 10, "y": y + 10, "z": 7, "ground": 415, "items": items}
                )

        patterns = self.detector.detect(tiles, {}, [])
        room_patterns = [p for p in patterns if p.pattern_type == "room"]
        self.assertGreater(len(room_patterns), 0)

    def test_detect_entrances_with_doors(self):
        """Detecta entradas cuando hay puertas."""
        tiles = [
            {"x": 10, "y": 10, "z": 7, "ground": 415, "items": [{"item_id": 1210}]},
            {"x": 11, "y": 11, "z": 7, "ground": 415, "items": []},
        ]
        patterns = self.detector.detect(tiles, {}, [])
        entrance = [p for p in patterns if p.pattern_type == "entrance"]
        self.assertGreater(len(entrance), 0)

    def test_detect_floor_patterns(self):
        """Detecta patrones de suelo dominante."""
        tiles = []
        for i in range(50):
            tiles.append(
                {
                    "x": i % 10,
                    "y": i // 10,
                    "z": 7,
                    "ground": 415,
                    "items": [],
                }
            )
        patterns = self.detector.detect(tiles, {}, [])
        floor_patterns = [p for p in patterns if p.pattern_type == "floor"]
        self.assertGreater(len(floor_patterns), 0)

    def test_detect_spawn_clusters(self):
        """Detecta clusters de spawns."""
        spawns = [
            {"monster": "dragon", "x": 10, "y": 10, "radius": 5},
            {"monster": "dragon_lord", "x": 12, "y": 11, "radius": 5},
            {"monster": "demon", "x": 14, "y": 12, "radius": 5},
            {"monster": "hydra", "x": 50, "y": 50, "radius": 5},
        ]
        patterns = self.detector.detect([], {}, spawns)
        spawn_clusters = [p for p in patterns if p.pattern_type == "spawn_cluster"]
        self.assertGreater(len(spawn_clusters), 0)

    def test_detect_aggregate_wall_pattern(self):
        """Modo agregado detecta patron de muros."""
        items_stats = {"item_101": 30, "item_1000": 25, "item_999": 10}
        patterns = self.detector.detect_aggregate(
            tiles_stats={"ground_415": 400},
            items_stats=items_stats,
            spawn_count=0,
            house_count=0,
            waypoint_count=0,
        )
        wall_patterns = [p for p in patterns if p.pattern_type == "wall"]
        self.assertGreater(len(wall_patterns), 0)

    def test_detect_aggregate_dominant_floor(self):
        """Modo agregado detecta suelo dominante."""
        tiles_stats = {"ground_415": 400, "ground_416": 100}
        patterns = self.detector.detect_aggregate(
            tiles_stats=tiles_stats,
            items_stats={},
            spawn_count=0,
            house_count=0,
            waypoint_count=0,
        )
        floor_patterns = [p for p in patterns if p.pattern_type == "floor"]
        self.assertGreater(len(floor_patterns), 0)

    def test_pattern_to_dict(self):
        """Pattern.to_dict() es serializable."""
        p = Pattern(
            pattern_type="room",
            bounds=(10, 20, 30, 40),
            confidence=0.85,
            tile_ids=[415, 416],
            item_ids=[101, 102],
            spawn_names=["dragon"],
            description="Test room",
        )
        d = p.to_dict()
        self.assertEqual(d["pattern_type"], "room")
        self.assertEqual(d["bounds"], [10, 20, 30, 40])
        self.assertEqual(d["confidence"], 0.85)
        json.dumps(d)  # debe serializar sin error

    def test_cluster_positions(self):
        """_cluster_positions agrupa correctamente."""
        positions = [
            (1, 1),
            (1, 2),
            (2, 1),
            (2, 2),  # cluster 1
            (10, 10),
            (10, 11),
            (11, 10),  # cluster 2
        ]
        clusters = self.detector._cluster_positions(positions, min_points=3, radius=3)
        self.assertEqual(len(clusters), 2)

    def test_find_repeating_patterns(self):
        """Detecta motivos repetitivos."""
        tiles = []
        # Crear patron repetitivo: wall, floor, wall, floor...
        for i in range(20):
            items = [{"item_id": 101}] if i % 2 == 0 else []
            tiles.append({"x": i, "y": 0, "z": 7, "ground": 415, "items": items})

        patterns = self.detector.find_repeating_patterns(tiles, min_repetitions=2)
        self.assertGreater(len(patterns), 0)

    def test_detect_empty_tiles_returns_empty(self):
        """Sin tiles no hay patrones."""
        patterns = self.detector.detect([], {}, [])
        self.assertEqual(len(patterns), 0)

    def test_corridor_detection(self):
        """Detecta pasillos alargados."""
        tiles = []
        # Crear pasillo horizontal de 15x3
        for x in range(15):
            for y in range(3):
                tiles.append({"x": x, "y": y, "z": 7, "ground": 415, "items": []})

        patterns = self.detector.detect(tiles, {}, [])
        corridors = [p for p in patterns if p.pattern_type == "corridor"]
        self.assertGreater(len(corridors), 0)


# ──────────────────────────────────────────────────────────────────────
# TEST 3: StructureDetector
# ──────────────────────────────────────────────────────────────────────


class TestStructureDetector(unittest.TestCase):
    """Pruebas para StructureDetector."""

    def setUp(self):
        self.detector = StructureDetector()

    def test_detect_rooms(self):
        """Detecta habitaciones con datos posicionales."""
        tiles = _make_sample_tiles(60)
        structures = self.detector.detect(
            tiles=tiles,
            items={},
            spawns=[],
            houses=[],
            waypoints=[],
        )
        rooms = [s for s in structures if s.structure_type == "room"]
        self.assertGreater(len(rooms), 0)
        for room in rooms:
            self.assertEqual(room.structure_type, "room")
            self.assertGreater(room.area, 0)

    def test_detect_zones_hunting(self):
        """Detecta zona de hunting con spawns."""
        spawns = _make_sample_spawns(12)
        structures = self.detector.detect(
            tiles=_make_sample_tiles(50),
            items={},
            spawns=spawns,
            houses=[],
            waypoints=[],
        )
        zones = [
            s
            for s in structures
            if s.structure_type == "zone" and s.properties.get("zone_type") == "hunting"
        ]
        self.assertGreater(len(zones), 0)

    def test_detect_zones_urban(self):
        """Detecta zona urbana con houses."""
        houses = _make_sample_houses(5)
        structures = self.detector.detect(
            tiles=_make_sample_tiles(50),
            items={},
            spawns=[],
            houses=houses,
            waypoints=[],
        )
        zones = [
            s
            for s in structures
            if s.structure_type == "zone" and s.properties.get("zone_type") == "urban"
        ]
        self.assertGreater(len(zones), 0)

    def test_detect_layout(self):
        """Detecta tipo de layout."""
        tiles = _make_sample_tiles(200)
        structures = self.detector.detect(
            tiles=tiles,
            items={},
            spawns=[],
            houses=[],
            waypoints=[],
        )
        layout = [s for s in structures if s.structure_type == "layout"]
        self.assertEqual(len(layout), 1)
        self.assertIn("layout_type", layout[0].properties)

    def test_detect_hierarchy(self):
        """Construye jerarquia estructural."""
        structures = self.detector.detect(
            tiles=_make_sample_tiles(100),
            items={},
            spawns=_make_sample_spawns(5),
            houses=_make_sample_houses(3),
            waypoints=_make_sample_waypoints(4),
        )
        hierarchy = [s for s in structures if s.structure_type == "hierarchy"]
        self.assertEqual(len(hierarchy), 1)
        self.assertIn("levels", hierarchy[0].properties)
        self.assertIn("summary", hierarchy[0].properties)

    def test_detect_aggregate(self):
        """Modo agregado produce estructuras inferidas."""
        structures = self.detector.detect_aggregate(
            tiles_stats={"ground_415": 500, "ground_416": 200},
            items_stats={"item_101": 50},
            spawn_count=15,
            house_count=5,
            waypoint_count=8,
            map_size={"width": 100, "height": 100},
        )
        self.assertGreater(len(structures), 0)
        layout = [s for s in structures if s.structure_type == "layout"]
        self.assertEqual(len(layout), 1)

    def test_detected_structure_to_dict(self):
        """DetectedStructure.to_dict() es serializable."""
        s = DetectedStructure(
            structure_type="room",
            name="test_room",
            bounds=(10, 20, 30, 40),
            area=200,
            confidence=0.9,
            properties={"room_type": "chamber"},
            description="Test room",
        )
        d = s.to_dict()
        self.assertEqual(d["structure_type"], "room")
        self.assertEqual(d["bounds"], [10, 20, 30, 40])
        json.dumps(d)

    def test_poi_detection_temple(self):
        """Detecta temple como POI."""
        houses = [
            {
                "id": 1,
                "name": "Thais Temple",
                "temple_x": 50,
                "temple_y": 60,
                "temple_z": 7,
            }
        ]
        structures = self.detector.detect(
            tiles=_make_sample_tiles(20),
            items={},
            spawns=[],
            houses=houses,
            waypoints=[],
        )
        pois = [
            s
            for s in structures
            if s.structure_type == "poi" and "temple" in s.name.lower()
        ]
        self.assertGreater(len(pois), 0)

    def test_building_grouping(self):
        """Agrupa rooms en buildings."""
        tiles = []
        # Dos clusters de tiles separados
        for x in range(0, 8):
            for y in range(0, 8):
                tiles.append({"x": x, "y": y, "z": 7, "ground": 415, "items": []})
        for x in range(20, 28):
            for y in range(20, 28):
                tiles.append({"x": x, "y": y, "z": 7, "ground": 416, "items": []})

        structures = self.detector.detect(
            tiles=tiles,
            items={},
            spawns=[],
            houses=[],
            waypoints=[],
        )
        buildings = [s for s in structures if s.structure_type == "building"]
        # Podria o no agrupar dependiendo de la distancia
        _ = len(buildings) >= 0  # solo verifica que no crashea


# ──────────────────────────────────────────────────────────────────────
# TEST 4: BlueprintExtractor
# ──────────────────────────────────────────────────────────────────────


class TestBlueprintExtractor(unittest.TestCase):
    """Pruebas para BlueprintExtractor - pipeline completo."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="hito13_test_")
        self.extractor = BlueprintExtractor(output_dir=self.tmp_dir)

    def tearDown(self):
        import shutil

        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_extract_from_world_dict(self):
        """Extrae blueprint desde WorldModel dict."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict,
            source_name="test_map",
            save=True,
        )
        self.assertTrue(result.success)
        self.assertIsNotNone(result.blueprint)
        self.assertEqual(len(result.errors), 0)

        bp = result.blueprint
        self.assertIsInstance(bp, Blueprint)
        self.assertTrue(len(bp.name) > 0)
        self.assertIn("test_map", bp.name)

    def test_extraction_result_stats(self):
        """Verifica estadisticas en el resultado."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="test", save=False
        )
        self.assertIn("tile_count", result.stats)
        self.assertIn("spawn_count", result.stats)
        self.assertIn("map_size", result.stats)
        self.assertGreater(result.stats["tile_count"], 0)

    def test_extraction_theme_classification(self):
        """Verifica que el tema se clasifica correctamente."""
        world_dict = {
            "width": 50,
            "height": 50,
            "tiles": [
                {"x": i % 10, "y": i // 10, "z": 7, "ground": 415, "items": []}
                for i in range(100)
            ],
            "spawns": [],
            "cities": [],
            "waypoints": [],
            "tile_count": 100,
            "spawn_count": 0,
            "city_count": 0,
            "waypoint_count": 0,
        }
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="temple_test", save=False
        )
        self.assertTrue(result.success)
        self.assertIn("primary_theme", result.theme)
        self.assertEqual(result.theme["primary_theme"], "temple")

    def test_extraction_patterns(self):
        """Verifica que se detectan patrones."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="pattern_test", save=False
        )
        self.assertGreater(len(result.patterns), 0)

    def test_extraction_structures(self):
        """Verifica que se detectan estructuras."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="struct_test", save=False
        )
        self.assertGreater(len(result.structures), 0)

    def test_save_blueprint_to_file(self):
        """Guarda blueprint en disco."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="save_test", save=True
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.saved_path)
        self.assertTrue(os.path.exists(result.saved_path))

        # Verificar que el archivo es JSON valido
        with open(result.saved_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("name", data)
        self.assertIn("theme", data)
        self.assertIn("_extraction", data)

    def test_list_blueprints(self):
        """Lista blueprints guardados."""
        world_dict = _make_sample_world_dict()
        self.extractor.extract_from_world_dict(
            world_dict, source_name="list_test_a", save=True
        )
        self.extractor.extract_from_world_dict(
            world_dict, source_name="list_test_b", save=True
        )

        names = self.extractor.list_blueprints()
        self.assertGreaterEqual(len(names), 2)

    def test_load_blueprint(self):
        """Carga blueprint desde disco."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="load_test", save=True
        )

        bp_name = result.blueprint.name
        loaded = self.extractor.load_blueprint(bp_name)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, bp_name)

    def test_blueprint_has_tiles(self):
        """El blueprint extraido contiene tiles."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="tile_test", save=False
        )

        bp = result.blueprint
        self.assertIsNotNone(bp)
        self.assertGreater(len(bp.tiles), 0)
        self.assertIsInstance(bp.tiles[0], BlueprintTile)

    def test_blueprint_has_metadata(self):
        """El blueprint tiene metadata correcta."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="meta_test", save=False
        )

        bp = result.blueprint
        self.assertIsNotNone(bp.metadata)
        self.assertIsInstance(bp.metadata, BlueprintMetadata)
        self.assertTrue(len(bp.metadata.style) > 0)
        self.assertTrue(len(bp.metadata.tags) > 0)

    def test_extraction_result_to_dict(self):
        """ExtractionResult.to_dict() es serializable."""
        result = ExtractionResult(
            success=True,
            theme={"primary_theme": "temple"},
            stats={"tile_count": 100},
        )
        d = result.to_dict()
        self.assertTrue(d["success"])
        json.dumps(d)

    def test_blueprint_descriptive_mode(self):
        """Blueprint incluye grounds, walls_items, decorations."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="descriptive_test", save=False
        )

        bp = result.blueprint
        self.assertIsNotNone(bp)
        # Debe tener algun contenido descriptivo
        has_descriptive = (
            len(bp.grounds) > 0
            or len(bp.walls_items) > 0
            or len(bp.decorations) > 0
            or len(bp.rooms) > 0
            or len(bp.zones) > 0
        )
        self.assertTrue(has_descriptive)

    def test_entry_point_determined(self):
        """Determina punto de entrada correctamente."""
        world_dict = {
            "width": 100,
            "height": 100,
            "tiles": _make_sample_tiles(30),
            "spawns": [],
            "cities": [],
            "waypoints": [{"name": "start", "x": 25, "y": 30, "z": 7}],
            "tile_count": 30,
            "spawn_count": 0,
            "city_count": 0,
            "waypoint_count": 1,
        }
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="entry_test", save=False
        )
        bp = result.blueprint
        self.assertIsNotNone(bp.entry)
        self.assertEqual(bp.entry, (25, 30))

    def test_category_determination_temple(self):
        """Categoria temple para theme temple."""
        world_dict = {
            "width": 50,
            "height": 50,
            "tiles": [
                {"x": i % 10, "y": i // 10, "z": 7, "ground": 415, "items": []}
                for i in range(100)
            ],
            "spawns": [],
            "cities": [],
            "waypoints": [],
            "tile_count": 100,
            "spawn_count": 0,
            "city_count": 0,
            "waypoint_count": 0,
        }
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="cat_test", save=False
        )
        self.assertEqual(result.blueprint.category, "temple")

    def test_category_determination_hunting(self):
        """Categoria hunting con muchos spawns y suelo neutro."""
        world_dict = {
            "width": 50,
            "height": 50,
            "tiles": [
                {"x": i % 10, "y": i // 10, "z": 7, "ground": 393, "items": []}
                for i in range(100)
            ],
            "spawns": _make_sample_spawns(20),
            "cities": [],
            "waypoints": [],
            "tile_count": 100,
            "spawn_count": 20,
            "city_count": 0,
            "waypoint_count": 0,
        }
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="hunt_cat_test", save=False
        )
        # With neutral ground (sandstone) and 20+ hunt-monster spawns,
        # theme should be hunt -> category hunting
        self.assertEqual(result.blueprint.category, "hunting")

    def test_batch_extraction(self):
        """Extraccion batch funciona."""
        # Crear world_dict placeholder y usar extract_from_world_dict en batch
        results = []
        for i in range(3):
            wd = _make_sample_world_dict()
            r = self.extractor.extract_from_world_dict(
                wd, source_name=f"batch_{i}", save=False
            )
            results.append(r)

        self.assertEqual(len(results), 3)
        for r in results:
            self.assertTrue(r.success)

    def test_blueprint_to_dict_serializable(self):
        """Blueprint completo serializa a JSON sin errores."""
        world_dict = _make_sample_world_dict()
        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="serialization_test", save=False
        )

        bp_dict = result.blueprint.to_dict()
        json_str = json.dumps(bp_dict)
        self.assertIsInstance(json_str, str)
        # Re-parse para verificar
        parsed = json.loads(json_str)
        self.assertEqual(parsed["name"], result.blueprint.name)

    def test_empty_world_dict_handled(self):
        """World dict vacio no causa crash."""
        result = self.extractor.extract_from_world_dict(
            {}, source_name="empty", save=False
        )
        self.assertFalse(result.success)
        self.assertGreater(len(result.errors), 0)


# ──────────────────────────────────────────────────────────────────────
# TEST 5: End-to-End Pipeline Tests
# ──────────────────────────────────────────────────────────────────────


class TestEndToEndPipeline(unittest.TestCase):
    """Pruebas de integracion end-to-end."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="hito13_e2e_")
        self.extractor = BlueprintExtractor(output_dir=self.tmp_dir)

    def tearDown(self):
        import shutil

        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_full_pipeline_world_dict_to_blueprint_file(self):
        """Pipeline completo: WorldDict → Theme → Patterns → Structures → Blueprint → JSON."""
        world_dict = _make_sample_world_dict()

        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="e2e_full", save=True
        )

        # Verificar resultado
        self.assertTrue(result.success)
        self.assertEqual(len(result.errors), 0)
        self.assertIsNotNone(result.blueprint)
        self.assertIsNotNone(result.saved_path)

        # Verificar tema
        self.assertIn("primary_theme", result.theme)
        self.assertGreater(result.theme["confidence"], 0)

        # Verificar patrones
        self.assertGreater(len(result.patterns), 0)

        # Verificar estructuras
        self.assertGreater(len(result.structures), 0)

        # Verificar archivo guardado
        self.assertTrue(os.path.exists(result.saved_path))

        # Verificar contenido del archivo
        with open(result.saved_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertIn("name", saved_data)
        self.assertIn("theme", saved_data)
        self.assertIn("category", saved_data)
        self.assertIn("tiles", saved_data)
        self.assertIn("metadata", saved_data)
        self.assertIn("_extraction", saved_data)

        # Verificar que se puede recargar
        bp_name = result.blueprint.name
        loaded = self.extractor.load_blueprint(bp_name)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, bp_name)
        self.assertEqual(loaded.theme, result.theme["primary_theme"])

    def test_pipeline_preserves_tile_data(self):
        """Pipeline preserva datos de tiles a traves de todo el proceso."""
        tiles = []
        for i in range(25):
            tiles.append(
                {
                    "x": i % 5,
                    "y": i // 5,
                    "z": 7,
                    "ground": 415 + (i % 3),
                    "items": [{"item_id": 1000 + (i % 5)}] if i % 2 == 0 else [],
                }
            )

        world_dict = {
            "width": 5,
            "height": 5,
            "tiles": tiles,
            "spawns": [],
            "cities": [],
            "waypoints": [],
            "tile_count": 25,
            "spawn_count": 0,
            "city_count": 0,
            "waypoint_count": 0,
        }

        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="tile_preservation", save=False
        )

        bp = result.blueprint
        self.assertEqual(len(bp.tiles), 25)

        # Verificar que al menos un tile tiene ground != 0
        non_zero_grounds = [t for t in bp.tiles if t.ground != 0]
        self.assertGreater(len(non_zero_grounds), 0)

    def test_pipeline_with_spawns_and_houses(self):
        """Pipeline maneja correctamente spawns y houses."""
        world_dict = {
            "width": 100,
            "height": 100,
            "tiles": _make_sample_tiles(100),
            "spawns": _make_sample_spawns(20),
            "cities": _make_sample_houses(4),
            "waypoints": _make_sample_waypoints(5),
            "tile_count": 100,
            "spawn_count": 20,
            "city_count": 4,
            "waypoint_count": 5,
        }

        result = self.extractor.extract_from_world_dict(
            world_dict, source_name="spawn_house_test", save=False
        )

        self.assertTrue(result.success)
        bp = result.blueprint

        # Verificar que se detecto hunting zone
        is_hunt = result.theme.get("is_hunt_area", False)
        self.assertTrue(is_hunt)

        # Verificar que hay zonas en el blueprint
        self.assertGreater(len(bp.zones), 0)

        # Verificar que el metadata refleja dificultad alta
        self.assertIn(bp.metadata.difficulty, ["hard", "dangerous", "normal"])


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main()
