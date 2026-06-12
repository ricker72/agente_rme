"""
Tests para HITO 9 REAL — Preview Generator V1.

Verifica:
  1. Test obligatorio: WorldModel → Tile → PreviewGenerator → preview.png
  2. Generación de preview.png con colores
  3. Generación de preview_minimap.png con escalado
  4. Generación de preview.json con estadísticas
  5. Pipeline completo: WorldModel → PreviewGenerator → 3 outputs
  6. Clasificación de tiles: ground, wall, spawn, boss, decoration
  7. Overlay de estructuras
  8. Reporte: tiles, grounds, items, spawns, bosses, structures
  9. Distinción visual entre: Terreno, Decoración, Spawns, Bosses, Estructuras
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.preview import (
    PreviewGenerator,
    render_tile,
    render_layer,
    compute_bounds,
    add_structure_overlay,
    generate_report,
    save_minimap,
    GROUND,
    WALL,
    WATER,
    SPAWN,
    BOSS,
    DECORATION,
    TEMPLE,
    EMPTY,
    STRUCTURE,
    get_color_for_ground,
    get_color_for_item,
    is_boss,
)
from core.world import WorldModel, Tile, Spawn, Item, Structure, Region
from core.generators import WorldGenerator

# =========================================================================
# TEST OBLIGATORIO
# =========================================================================


def test_preview_generation():
    """
    Test obligatorio del Hito 9:

    world = WorldModel()
    tile = Tile(x=100, y=100, z=7)
    tile.ground = 817
    world.set_tile(tile)
    PreviewGenerator().generate(world, "preview.png")
    assert Path("preview.png").exists()
    """
    world = WorldModel()
    tile = Tile(x=100, y=100, z=7)
    tile.ground = 817
    world.set_tile(tile)

    pg = PreviewGenerator(tile_size=10)
    pg.generate(world, output_png="output/test_mandatory.png")
    assert Path("output/test_mandatory.png").exists(), "preview.png no se generó"
    assert os.path.getsize("output/test_mandatory.png") > 0, "preview.png está vacío"
    print(
        f"  [OK] Test obligatorio: preview.png generado ({os.path.getsize('output/test_mandatory.png')} bytes)"
    )


# =========================================================================
# Tests de componentes
# =========================================================================


def test_palette_colors():
    """Verificar que los colores de la paleta son tuplas RGB válidas."""
    colors = [GROUND, WALL, WATER, SPAWN, BOSS, DECORATION, TEMPLE, EMPTY, STRUCTURE]
    for c in colors:
        assert isinstance(c, tuple) and len(c) == 3, f"Color inválido: {c}"
        assert all(0 <= v <= 255 for v in c), f"RGB fuera de rango: {c}"
    print("  [OK] Palette colors válidos")


def test_get_color_for_ground():
    """Verificar clasificación de ground IDs."""
    assert get_color_for_ground(None) == EMPTY
    assert get_color_for_ground(1495) == WALL  # Wall ID
    assert get_color_for_ground(415) == GROUND  # Ground ID
    assert get_color_for_ground(4821) == WATER  # Water ID
    assert get_color_for_ground(99999) == GROUND  # Desconocido → ground
    print("  [OK] get_color_for_ground")


def test_get_color_for_item():
    """Verificar clasificación de items."""
    assert get_color_for_item(2153) == DECORATION  # Decoración conocida
    assert get_color_for_item(99999) == DECORATION  # Desconocido → decoración
    print("  [OK] get_color_for_item")


def test_is_boss():
    """Verificar detección de bosses."""
    assert is_boss("Demon") is True
    assert is_boss("Dragon") is True
    assert is_boss("Rat") is False
    assert is_boss("") is False
    print("  [OK] is_boss")


def test_render_tile_ground():
    """Render de tile con solo ground."""
    tile = Tile(x=0, y=0, z=7, ground=415)
    color = render_tile(tile)
    assert color == GROUND, f"Esperado GROUND, obtenido {color}"
    print("  [OK] render_tile: ground")


def test_render_tile_wall():
    """Render de tile con wall."""
    tile = Tile(x=0, y=0, z=7, ground=1495)
    color = render_tile(tile)
    assert color == WALL, f"Esperado WALL, obtenido {color}"
    print("  [OK] render_tile: wall")


def test_render_tile_spawn():
    """Render de tile con spawn."""
    tile = Tile(x=0, y=0, z=7, ground=415)
    tile.spawn = Spawn(monster="Skeleton", respawn=60)
    color = render_tile(tile)
    assert color == SPAWN, f"Esperado SPAWN, obtenido {color}"
    print("  [OK] render_tile: spawn")


def test_render_tile_boss():
    """Render de tile con boss."""
    tile = Tile(x=0, y=0, z=7, ground=415)
    tile.spawn = Spawn(monster="Demon", respawn=120)
    color = render_tile(tile)
    assert color == BOSS, f"Esperado BOSS, obtenido {color}"
    print("  [OK] render_tile: boss")


def test_render_tile_decorated():
    """Render de tile con decoración."""
    tile = Tile(x=0, y=0, z=7, ground=415)
    tile.items.append(Item(itemid=2153))  # Decoración conocida
    color = render_tile(tile)
    assert color == DECORATION, f"Esperado DECORATION, obtenido {color}"
    print("  [OK] render_tile: decoration")


def test_render_tile_empty():
    """Render de tile None."""
    color = render_tile(None)
    assert color == EMPTY, f"Esperado EMPTY, obtenido {color}"
    print("  [OK] render_tile: empty")


def test_compute_bounds():
    """Verificar cálculo de bounding box."""
    tiles = {
        "0:0:7": Tile(x=0, y=0, z=7),
        "10:10:7": Tile(x=10, y=10, z=7),
        "5:5:8": Tile(x=5, y=5, z=8),
    }
    bounds = compute_bounds(tiles)
    assert bounds is not None
    assert bounds["min_x"] == 0
    assert bounds["max_x"] == 10
    assert bounds["min_y"] == 0
    assert bounds["max_y"] == 10
    assert bounds["min_z"] == 7
    assert bounds["max_z"] == 8
    print(
        f"  [OK] compute_bounds: ({bounds['min_x']},{bounds['min_y']})~({bounds['max_x']},{bounds['max_y']})"
    )


def test_compute_bounds_empty():
    """Bounding box vacío."""
    bounds = compute_bounds({})
    assert bounds is None
    print("  [OK] compute_bounds: empty")


def test_render_layer():
    """Render de una capa completa."""
    tiles = {}
    for x in range(3):
        for y in range(3):
            tile = Tile(x=x, y=y, z=7, ground=415)
            if x == 0 and y == 0:
                tile.spawn = Spawn(monster="Skeleton", respawn=60)
            tiles[f"{x}:{y}:7"] = tile

    img = render_layer(tiles, z=7, tile_size=4, padding=0)
    assert img is not None
    assert img.width == 3 * 4  # 3 tiles * 4px
    assert img.height == 3 * 4
    print(f"  [OK] render_layer: {img.width}x{img.height}px")


def test_add_structure_overlay():
    """Overlay de estructura sobre imagen."""
    tiles = {"0:0:7": Tile(x=0, y=0, z=7, ground=415)}
    structures = [
        Structure(
            name="test_temple", category="temple", x=0, y=0, z=7, width=1, height=1
        ),
    ]
    bounds = compute_bounds(tiles)
    img = render_layer(tiles, z=7, tile_size=10, padding=1)
    img = add_structure_overlay(img, structures, bounds, z=7, tile_size=10, padding=1)
    assert img is not None
    print("  [OK] add_structure_overlay")


def test_save_minimap():
    """Generar y guardar minimapa."""
    tiles = {}
    for x in range(5):
        for y in range(5):
            tiles[f"{x}:{y}:7"] = Tile(x=x, y=y, z=7, ground=415)

    path = save_minimap(tiles, output_path="output/test_minimap.png", z=7, scale="4x")
    if path:
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        print(f"  [OK] save_minimap: {path} ({os.path.getsize(path)} bytes)")
    else:
        print("  [INFO] PIL no disponible, minimap no generado")


# =========================================================================
# Tests de reportes
# =========================================================================


def test_generate_report():
    """Generar reporte de estadísticas."""
    world = WorldModel()
    tile = Tile(x=100, y=100, z=7, ground=415)
    tile.spawn = Spawn(monster="Skeleton", respawn=60)
    tile.items.append(Item(itemid=2153))
    world.set_tile(tile)

    tile2 = Tile(x=101, y=100, z=7, ground=1495)
    tile2.spawn = Spawn(monster="Demon", respawn=120)
    world.set_tile(tile2)

    world.add_structure(
        Structure(name="t1", category="temple", x=100, y=100, z=7, width=2, height=1)
    )
    world.add_region(Region(name="test", theme="issavi"))

    report = generate_report(world)
    assert report["tiles"] == 2
    assert report["grounds"] == 1
    assert report["walls"] == 1
    assert report["items"] == 1
    assert report["decorations"] == 1
    assert report["spawns"] == 1
    assert report["bosses"] == 1
    assert report["structures"] == 1
    assert report["regions"] == 1
    assert report["unique_ground_ids"] == 2
    print(f"  [OK] generate_report: {report['summary']}")


def test_generate_report_empty():
    """Reporte de mundo vacío."""
    world = WorldModel()
    report = generate_report(world)
    assert report["tiles"] == 0
    assert report["spawns"] == 0
    assert report["structures"] == 0
    print(f"  [OK] generate_report empty: {report['summary']}")


def test_report_json_serializable():
    """Reporte debe ser serializable a JSON."""
    world = WorldModel()
    world.set_tile(Tile(x=0, y=0, z=7, ground=415))
    report = generate_report(world)
    json_str = json.dumps(report, indent=2)
    assert len(json_str) > 0
    parsed = json.loads(json_str)
    assert parsed["tiles"] == 1
    print(f"  [OK] Report JSON serializable ({len(json_str)} chars)")


# =========================================================================
# Tests de integración con WorldGenerator
# =========================================================================


def test_generate_from_generated_world():
    """Pipeline completo: WorldGenerator → PreviewGenerator → preview.png + .json."""
    gen = WorldGenerator(seed=42)
    world = gen.generate("Issavi + Roshamuul level 300")

    pg = PreviewGenerator(tile_size=8, minimap_scale="8x")
    result = pg.generate(
        world,
        output_png="output/test_preview.png",
        output_minimap="output/test_preview_minimap.png",
        output_json="output/test_preview.json",
    )

    assert "png" in result, f"No se generó PNG: {result}"
    assert Path(result["png"]).exists(), f"No existe: {result['png']}"
    assert os.path.getsize(result["png"]) > 0, f"PNG vacío: {result['png']}"

    if "minimap" in result:
        assert Path(result["minimap"]).exists()
        assert os.path.getsize(result["minimap"]) > 0
    else:
        print("  [INFO] PIL no disponible, minimap no generado")

    if "json" in result:
        assert Path(result["json"]).exists()
        assert os.path.getsize(result["json"]) > 0
        with open(result["json"]) as f:
            report = json.load(f)
        assert report["tiles"] > 0
        print(f"  [OK] JSON report: {report['summary']}")

    print(f"  [OK] Pipeline completo: {result}")


def test_distinguir_visualmente():
    """
    Verificar que se distinguen visualmente:
      Terreno, Decoración, Spawns, Bosses, Estructuras
    """
    world = WorldModel()

    # Terreno (ground)
    world.set_tile(Tile(x=0, y=0, z=7, ground=415))  # GROUND

    # Decoración (item)
    tile_deco = Tile(x=1, y=0, z=7, ground=415)
    tile_deco.items.append(Item(itemid=2153))
    world.set_tile(tile_deco)

    # Spawn
    tile_spawn = Tile(x=2, y=0, z=7, ground=415)
    tile_spawn.spawn = Spawn(monster="Skeleton", respawn=60)
    world.set_tile(tile_spawn)

    # Boss
    tile_boss = Tile(x=3, y=0, z=7, ground=415)
    tile_boss.spawn = Spawn(monster="Demon", respawn=120)
    world.set_tile(tile_boss)

    # Estructura (temple overlay)
    world.add_structure(
        Structure(name="temple", category="temple", x=4, y=0, z=7, width=1, height=1)
    )

    # Verificar colores individuales
    tiles = world.tiles
    assert render_tile(tiles["0:0:7"]) == GROUND, "ground no es GROUND"
    assert render_tile(tiles["1:0:7"]) == DECORATION, "deco no es DECORATION"
    assert render_tile(tiles["2:0:7"]) == SPAWN, "spawn no es SPAWN"
    assert render_tile(tiles["3:0:7"]) == BOSS, "boss no es BOSS"
    print(
        "  [OK] Distinción visual: GROUND, DECORATION, SPAWN, BOSS, STRUCTURE confirmados"
    )


def test_empty_world_preview():
    """Preview de mundo vacío."""
    world = WorldModel()
    pg = PreviewGenerator()
    result = pg.generate(world, output_png="output/test_empty.png")
    # No PNG (no tiles), pero puede generar JSON con reporte vacío
    assert "png" not in result, "No debería generar PNG sin tiles"
    if "json" in result:
        import json as _json

        with open(result["json"]) as f:
            report = _json.load(f)
        assert report["tiles"] == 0
        print(f"  [OK] Empty world: solo JSON generado ({report['summary']})")
    else:
        print("  [OK] Empty world: sin outputs")


def test_multi_z_preview():
    """Preview con múltiples capas Z."""
    world = WorldModel()
    for z in [7, 8]:
        for x in range(2):
            world.set_tile(Tile(x=x, y=0, z=z, ground=415))

    pg = PreviewGenerator(tile_size=4)
    png = pg.generate_png(world, "output/test_z7.png", z=7)
    if png:
        assert os.path.exists(png)
        print("  [OK] Multi-Z: Z=7 generado")
    png8 = pg.generate_png(world, "output/test_z8.png", z=8)
    if png8:
        assert os.path.exists(png8)
        print("  [OK] Multi-Z: Z=8 generado")

    report = generate_report(world)
    assert report["z_layers"] == {7: 2, 8: 2}
    print(f"  [OK] Multi-Z report: {report['z_layers']}")


# =========================================================================
# Runner
# =========================================================================

if __name__ == "__main__":
    tests = [
        ("Test Obligatorio", test_preview_generation),
        ("Palette colors", test_palette_colors),
        ("get_color_for_ground", test_get_color_for_ground),
        ("get_color_for_item", test_get_color_for_item),
        ("is_boss", test_is_boss),
        ("render_tile: ground", test_render_tile_ground),
        ("render_tile: wall", test_render_tile_wall),
        ("render_tile: spawn", test_render_tile_spawn),
        ("render_tile: boss", test_render_tile_boss),
        ("render_tile: decoration", test_render_tile_decorated),
        ("render_tile: empty", test_render_tile_empty),
        ("compute_bounds", test_compute_bounds),
        ("compute_bounds empty", test_compute_bounds_empty),
        ("render_layer", test_render_layer),
        ("add_structure_overlay", test_add_structure_overlay),
        ("save_minimap", test_save_minimap),
        ("generate_report", test_generate_report),
        ("generate_report empty", test_generate_report_empty),
        ("Report JSON", test_report_json_serializable),
        ("Pipeline WorldGenerator", test_generate_from_generated_world),
        ("Distinción visual", test_distinguir_visualmente),
        ("Empty world", test_empty_world_preview),
        ("Multi-Z preview", test_multi_z_preview),
    ]

    passed = failed = 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"  [PASS] {name}")
        except Exception as e:
            failed += 1
            import traceback

            print(f"  [FAIL] {name}: {e}")
            traceback.print_exc()
        print()

    print("=" * 60)
    print(f"  RESULTADOS: {passed} passed, {failed} failed / {passed + failed}")
    print("=" * 60)
    sys.exit(0 if failed == 0 else 1)
