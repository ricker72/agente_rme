"""
HITO 13 — Demo funcional del Blueprint Extractor.

Demuestra el pipeline completo:
    OTBM → WorldModel → Theme → Patterns → Structures → Blueprint → JSON

Ejemplos incluidos:
    1. Extraer desde WorldModel dict (simulado)
    2. Extraer desde datos de templo issavi
    3. Extraer desde datos de dungeon roshamuul
    4. Extraer desde datos de ciudad
    5. Batch extraction de multiples mapas
    6. Clasificacion de temas avanzada
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Asegurar que el path del proyecto esta en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.blueprints.theme_classifier import ThemeClassifier
from core.blueprints.pattern_detector import PatternDetector
from core.blueprints.structure_detector import StructureDetector
from core.blueprints.blueprint_extractor import BlueprintExtractor, ExtractionResult


# ═══════════════════════════════════════════════════════════════════════
# DATOS DE EJEMPLO
# ═══════════════════════════════════════════════════════════════════════

def make_issavi_temple_data():
    """Genera datos simulados de un templo issavi."""
    tiles = []
    # Suelo de sandstone (templo issavi)
    for x in range(50):
        for y in range(50):
            ground = 393  # sandstone_floor
            items = []

            # Muros en el perimetro
            if x == 0 or x == 49 or y == 0 or y == 49:
                items.append({"item_id": 2100})  # issavi wall
            # Puertas
            if (x == 25 and y == 0) or (x == 25 and y == 49):
                items.append({"item_id": 1210})  # door
            # Columnas internas
            if (x % 10 == 0 and y % 10 == 0) and x > 0 and x < 49 and y > 0 and y < 49:
                items.append({"item_id": 1001})  # pillar

            tiles.append({
                "x": x, "y": y, "z": 7,
                "ground": ground,
                "items": items,
                "all_items": [],
            })

    return {
        "version": 3,
        "width": 50,
        "height": 50,
        "item_major": 3,
        "item_minor": 57,
        "description": "Issavi Temple Complex",
        "spawn_file": "",
        "house_file": "",
        "tiles": tiles,
        "spawns": [
            {"monster": "dragon", "x": 10, "y": 10, "radius": 5},
            {"monster": "serpent_spawn", "x": 40, "y": 40, "radius": 5},
        ],
        "cities": [
            {
                "name": "Issavi Temple",
                "town_id": 1,
                "temple_x": 25, "temple_y": 25, "temple_z": 7,
                "x": 25, "y": 25, "z": 7,
            }
        ],
        "waypoints": [
            {"name": "entrance", "x": 25, "y": 0, "z": 7},
            {"name": "altar", "x": 25, "y": 25, "z": 7},
        ],
        "tile_count": len(tiles),
        "spawn_count": 2,
        "city_count": 1,
        "waypoint_count": 2,
    }


def make_roshamuul_dungeon_data():
    """Genera datos simulados de un dungeon roshamuul."""
    tiles = []
    for x in range(40):
        for y in range(30):
            ground = 1053 if (x + y) % 3 != 0 else 1056  # roshamuul_floor / stone
            items = []

            # Muros roshamuul
            if x == 0 or x == 39 or y == 0 or y == 29:
                items.append({"item_id": 2104})  # roshamuul wall

            tiles.append({
                "x": x, "y": y, "z": 8,
                "ground": ground,
                "items": items,
                "all_items": [],
            })

    return {
        "version": 3,
        "width": 40,
        "height": 30,
        "item_major": 3,
        "item_minor": 57,
        "description": "Roshammuul Dungeon",
        "spawn_file": "",
        "house_file": "",
        "tiles": tiles,
        "spawns": [
            {"monster": "demon", "x": 5, "y": 5, "radius": 4},
            {"monster": "behemoth", "x": 35, "y": 25, "radius": 6},
            {"monster": "dragon_lord", "x": 20, "y": 15, "radius": 5},
            {"monster": "warlock", "x": 10, "y": 25, "radius": 3},
            {"monster": "hydra", "x": 30, "y": 5, "radius": 4},
        ],
        "cities": [],
        "waypoints": [
            {"name": "dungeon_entrance", "x": 20, "y": 0, "z": 8},
            {"name": "boss_room", "x": 20, "y": 15, "z": 8},
        ],
        "tile_count": len(tiles),
        "spawn_count": 5,
        "city_count": 0,
        "waypoint_count": 2,
    }


def make_city_data():
    """Genera datos simulados de una ciudad."""
    tiles = []
    for x in range(30):
        for y in range(30):
            ground = 415  # polished_stone (urbano)
            items = []
            if x % 5 == 0 or y % 5 == 0:
                items.append({"item_id": 108})  # city wall
            tiles.append({
                "x": x, "y": y, "z": 7,
                "ground": ground,
                "items": items,
                "all_items": [],
            })

    return {
        "version": 3,
        "width": 30,
        "height": 30,
        "item_major": 3,
        "item_minor": 57,
        "description": "Sample City",
        "spawn_file": "",
        "house_file": "",
        "tiles": tiles,
        "spawns": [],
        "cities": [
            {"name": "City Hall", "town_id": 1, "temple_x": 15, "temple_y": 15, "temple_z": 7, "x": 15, "y": 15, "z": 7},
            {"name": "Market", "town_id": 2, "temple_x": 10, "temple_y": 5, "temple_z": 7, "x": 10, "y": 5, "z": 7},
            {"name": "Depot", "town_id": 3, "temple_x": 20, "temple_y": 5, "temple_z": 7, "x": 20, "y": 5, "z": 7},
            {"name": "Temple", "town_id": 4, "temple_x": 15, "temple_y": 10, "temple_z": 7, "x": 15, "y": 10, "z": 7},
        ],
        "waypoints": [
            {"name": "city_gate", "x": 0, "y": 15, "z": 7},
            {"name": "plaza", "x": 15, "y": 15, "z": 7},
        ],
        "tile_count": len(tiles),
        "spawn_count": 0,
        "city_count": 4,
        "waypoint_count": 2,
    }


# ═══════════════════════════════════════════════════════════════════════
# DEMOS
# ═══════════════════════════════════════════════════════════════════════

def demo_1_theme_classifier():
    """Demo 1: Clasificacion de temas."""
    print("=" * 60)
    print("DEMO 1: ThemeClassifier")
    print("=" * 60)

    classifier = ThemeClassifier()

    # Templo issavi (sandstone)
    issavi_tiles = {"sandstone_floor": 2000, "sandstone": 500}
    result = classifier.classify(issavi_tiles)
    print(f"\nIssavi Tiles → {result['primary_theme']} (confidence: {result['confidence']})")
    print(f"  Scores: {result['theme_scores']}")
    print(f"  Secondary: {result['secondary_themes']}")

    # Dungeon (mossy stone)
    dungeon_tiles = {"mossy_stone": 800, "dungeon_floor": 400}
    result = classifier.classify(dungeon_tiles)
    print(f"\nDungeon Tiles → {result['primary_theme']} (confidence: {result['confidence']})")

    # Hunt con spawns
    hunt_tiles = {"sandstone_floor": 300}
    hunt_spawns = [
        {"monster": "dragon"}, {"monster": "dragon_lord"},
        {"monster": "demon"}, {"monster": "hydra"},
        {"monster": "behemoth"},
    ]
    result = classifier.classify(hunt_tiles, spawns=hunt_spawns)
    print(f"\nHunt Area → {result['primary_theme']} (is_hunt: {result['is_hunt_area']})")

    # Ciudad
    city_tiles = {"polished_stone": 600, "cobblestone": 200}
    city_houses = [{"name": "Temple"}, {"name": "Depot"}, {"name": "Shop"}]
    result = classifier.classify(city_tiles, houses=city_houses)
    print(f"\nCity Tiles → {result['primary_theme']} (is_urban: {result['is_urban']})")

    # Quick classify
    print(f"\nQuick classify 'issavi_temple' → {classifier.quick_classify('issavi_temple')}")
    print(f"Quick classify 'roshamuul_dungeon' → {classifier.quick_classify('roshamuul_dungeon')}")
    print()


def demo_2_pattern_detector():
    """Demo 2: Deteccion de patrones."""
    print("=" * 60)
    print("DEMO 2: PatternDetector")
    print("=" * 60)

    detector = PatternDetector()

    # Crear tiles con patrones: habitacion con muros
    tiles = []
    for x in range(8):
        for y in range(8):
            items = []
            if x == 0 or x == 7 or y == 0 or y == 7:
                items.append({"item_id": 101})  # wall
            if (x == 3 or x == 4) and (y == 0 or y == 7):
                items.append({"item_id": 1210})  # door
            tiles.append({
                "x": x, "y": y, "z": 7,
                "ground": 415,
                "items": items,
            })

    patterns = detector.detect(tiles, {}, [])
    print(f"\nTiles analizados: {len(tiles)}")
    print(f"Patrones detectados: {len(patterns)}")
    for p in patterns:
        print(f"  - {p.pattern_type}: {p.description} (confidence: {p.confidence:.2f})")

    # Patrones agregados
    agg_patterns = detector.detect_aggregate(
        tiles_stats={"ground_415": 400, "ground_416": 200},
        items_stats={"item_101": 50, "item_1000": 30},
        spawn_count=5,
        house_count=3,
        waypoint_count=4,
    )
    print(f"\nPatrones agregados: {len(agg_patterns)}")
    for p in agg_patterns:
        print(f"  - {p.pattern_type}: {p.description}")

    # Patrones repetitivos
    repeating_tiles = []
    for i in range(30):
        items = [{"item_id": 101}] if i % 3 == 0 else []
        repeating_tiles.append({
            "x": i, "y": 0, "z": 7,
            "ground": 415,
            "items": items,
        })
    repeating = detector.find_repeating_patterns(repeating_tiles, min_repetitions=3)
    print(f"\nPatrones repetitivos encontrados: {len(repeating)}")
    for r in repeating[:5]:
        print(f"  - Seq: {r['sequence'][:60]}... (x{r['repetitions']})")
    print()


def demo_3_structure_detector():
    """Demo 3: Deteccion de estructuras."""
    print("=" * 60)
    print("DEMO 3: StructureDetector")
    print("=" * 60)

    detector = StructureDetector()

    # Crear tiles de un templo con estructuras
    tiles = []
    for x in range(20):
        for y in range(20):
            ground = 415  # polished_stone
            items = []
            if x == 0 or x == 19 or y == 0 or y == 19:
                items.append({"item_id": 1000})
            tiles.append({
                "x": x, "y": y, "z": 7, "ground": ground, "items": items,
            })

    spawns = [
        {"monster": "dragon", "x": 5, "y": 5},
        {"monster": "dragon_lord", "x": 15, "y": 15},
    ]
    houses = [
        {"id": 1, "name": "Main Temple", "temple_x": 10, "temple_y": 10, "temple_z": 7},
    ]
    waypoints = [
        {"name": "entrance", "x": 10, "y": 0, "z": 7},
    ]

    structures = detector.detect(
        tiles=tiles, items={},
        spawns=spawns, houses=houses,
        waypoints=waypoints,
        map_size={"width": 20, "height": 20},
    )

    print(f"\nEstructuras detectadas: {len(structures)}")
    for s in structures[:10]:
        print(f"  - [{s.structure_type}] {s.name}: {s.description}")

    # Layout
    layout = [s for s in structures if s.structure_type == "layout"]
    if layout:
        lt = layout[0]
        print(f"\nLayout detectado: {lt.properties.get('layout_type')}")
        print(f"  Tile density: {lt.properties.get('tile_density', 0):.4f}")

    # Hierarchy
    hierarchy = [s for s in structures if s.structure_type == "hierarchy"]
    if hierarchy:
        h = hierarchy[0]
        print(f"\nJerarquia estructural:")
        print(f"  Niveles: {h.properties.get('levels')}")
        print(f"  Resumen: {h.properties.get('summary')}")
    print()


def demo_4_blueprint_extractor_issavi():
    """Demo 4: Extraccion completa de blueprint issavi."""
    print("=" * 60)
    print("DEMO 4: Blueprint Extractor — Issavi Temple")
    print("=" * 60)

    extractor = BlueprintExtractor(output_dir="data/demo_blueprints/")
    data = make_issavi_temple_data()

    result = extractor.extract_from_world_dict(
        data, source_name="issavi_temple_demo", save=True
    )

    print(f"\nExtraccion: {'SUCCESS' if result.success else 'FAILED'}")
    if result.errors:
        print(f"  Errors: {result.errors}")

    print(f"\nStats:")
    print(f"  Tiles: {result.stats.get('tile_count')}")
    print(f"  Spawns: {result.stats.get('spawn_count')}")
    print(f"  Cities: {result.stats.get('city_count')}")
    print(f"  Waypoints: {result.stats.get('waypoint_count')}")

    print(f"\nTheme:")
    print(f"  Primary: {result.theme.get('primary_theme')}")
    print(f"  Confidence: {result.theme.get('confidence')}")
    print(f"  Secondary: {result.theme.get('secondary_themes')}")
    print(f"  Is urban: {result.theme.get('is_urban')}")
    print(f"  Is hunt: {result.theme.get('is_hunt_area')}")

    print(f"\nPatrones: {len(result.patterns)}")
    for p in result.patterns[:5]:
        print(f"  - {p.get('pattern_type')}: {p.get('description', '')[:80]}")

    print(f"\nEstructuras: {len(result.structures)}")
    for s in result.structures[:5]:
        print(f"  - {s.get('structure_type')}: {s.get('description', '')[:80]}")

    if result.blueprint:
        bp = result.blueprint
        print(f"\nBlueprint:")
        print(f"  Name: {bp.name}")
        print(f"  Theme: {bp.theme}")
        print(f"  Category: {bp.category}")
        print(f"  Size: {bp.size}")
        print(f"  Entry: {bp.entry}")
        print(f"  Tiles: {len(bp.tiles)}")
        print(f"  Rooms: {len(bp.rooms)}")
        print(f"  Zones: {len(bp.zones)}")
        print(f"  Metadata: style={bp.metadata.style}, era={bp.metadata.era}, "
              f"difficulty={bp.metadata.difficulty}")
        print(f"  Tags: {bp.metadata.tags}")

    if result.saved_path:
        print(f"\nSaved to: {result.saved_path}")
    print()


def demo_5_batch_extraction():
    """Demo 5: Extraccion batch de multiples tipos de mapa."""
    print("=" * 60)
    print("DEMO 5: Batch Extraction")
    print("=" * 60)

    extractor = BlueprintExtractor(output_dir="data/demo_blueprints/")

    datasets = [
        ("issavi_temple", make_issavi_temple_data()),
        ("roshamuul_dungeon", make_roshamuul_dungeon_data()),
        ("sample_city", make_city_data()),
    ]

    results = []
    for name, data in datasets:
        result = extractor.extract_from_world_dict(
            data, source_name=name, save=True
        )
        results.append(result)

        status = "✓" if result.success else "✗"
        theme = result.theme.get("primary_theme", "?")
        confidence = result.theme.get("confidence", 0)
        bp_name = result.blueprint.name if result.blueprint else "N/A"
        print(f"  {status} {name:25s} → {theme:12s} ({confidence:.2f}) | {bp_name}")

    # Listar blueprints guardados
    print(f"\nBlueprints guardados:")
    for name in extractor.list_blueprints():
        print(f"  - {name}")
    print()


def demo_6_theme_classification_deep():
    """Demo 6: Clasificacion de temas con metadatos completos."""
    print("=" * 60)
    print("DEMO 6: Theme Classification with Full Metadata")
    print("=" * 60)

    classifier = ThemeClassifier()

    scenarios = [
        {
            "name": "Issavi Temple",
            "tiles": {"sandstone_floor": 2500},
            "items": {"item_2100": 100, "item_2101": 50},
            "spawns": [{"monster": "dragon"}, {"monster": "serpent_spawn"}],
            "houses": [{"name": "Issavi Temple"}],
        },
        {
            "name": "Roshammuul Dungeon",
            "tiles": {"roshamuul_floor": 1200, "roshamuul_stone": 300},
            "items": {"item_2104": 80, "item_2105": 40},
            "spawns": [
                {"monster": "demon"}, {"monster": "behemoth"},
                {"monster": "dragon_lord"}, {"monster": "warlock"},
            ],
            "houses": [],
        },
        {
            "name": "Modern City",
            "tiles": {"polished_stone": 900, "cobblestone": 100},
            "items": {},
            "spawns": [],
            "houses": [
                {"name": "City Hall"}, {"name": "Market"},
                {"name": "Depot"}, {"name": "Temple"},
                {"name": "Arena"},
            ],
        },
        {
            "name": "Yalahar Quarter",
            "tiles": {"yalahar_floor": 500, "mosaic_floor": 100},
            "items": {},
            "spawns": [],
            "houses": [{"name": "Yalahar Palace"}],
        },
    ]

    for scenario in scenarios:
        meta = classifier.classify_with_metadata(
            tiles=scenario["tiles"],
            items=scenario["items"],
            spawns=scenario["spawns"],
            houses=scenario["houses"],
        )
        print(f"\n{scenario['name']}:")
        print(f"  Style:      {meta['style']}")
        print(f"  Era:        {meta['era']}")
        print(f"  Difficulty: {meta['difficulty']}")
        print(f"  Capacity:   {meta['capacity']}")
        print(f"  Hybrid:     {meta['hybrid']}")
        print(f"  Tags:       {meta['tags']}")

    print()


# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    """Ejecuta todos los demos funcionales de HITO 13."""
    print("\n" + "=" * 60)
    print("  HITO 13 -- BLUEPRINT EXTRACTOR -- FUNCTIONAL DEMOS")
    print("=" * 60 + "\n")

    demo_1_theme_classifier()
    demo_2_pattern_detector()
    demo_3_structure_detector()
    demo_4_blueprint_extractor_issavi()
    demo_5_batch_extraction()
    demo_6_theme_classification_deep()

    print("=" * 60)
    print("TODOS LOS DEMOS COMPLETADOS EXITOSAMENTE")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())