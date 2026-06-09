"""
Tests para OTBMExporter — WorldModel → .otbm + XMLs.

Test mínimo obligatorio:
    world = WorldModel()
    tile = Tile(x=100, y=100, z=7)
    tile.ground = 817
    world.set_tile(tile)
    OTBMExporter().export(world, "test.otbm")
    assert Path("test.otbm").exists()

Test de integración:
    world = generator.generate("Issavi hunt level 300")
    OTBMExporter().export(world, "hunt.otbm")
    assert Path("hunt.otbm").exists()
"""

import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.otbm import OTBMExporter, OtbmValidator
from core.world import WorldModel, Tile, Spawn, Item, Structure, Region
from core.generators import WorldGenerator


# =========================================================================
# TEST OBLIGATORIO
# =========================================================================

def test_mandatory_export():
    """
    Test obligatorio del Hito OTBM:
        world = WorldModel()
        tile = Tile(x=100, y=100, z=7)
        tile.ground = 817
        world.set_tile(tile)
        OTBMExporter().export(world, "test.otbm")
        assert Path("test.otbm").exists()
    """
    world = WorldModel()
    tile = Tile(x=100, y=100, z=7)
    tile.ground = 817
    world.set_tile(tile)

    exporter = OTBMExporter(generate_templates=False)
    report = exporter.export(world, "output/test_mandatory.otbm")

    assert Path("output/test_mandatory.otbm").exists(), "test.otbm no se generó"
    assert os.path.getsize("output/test_mandatory.otbm") > 0, "test.otbm está vacío"
    assert report["tiles"] == 1
    assert report["items"] == 1  # ground
    assert report["status"] == "success"

    # Validar binario
    validator = OtbmValidator()
    validation = validator.validate(open("output/test_mandatory.otbm", "rb").read())
    assert validation.is_valid, f"OTBM inválido: {validation.errors}"

    print(f"  [OK] Test obligatorio: output/test_mandatory.otbm "
          f"({os.path.getsize('output/test_mandatory.otbm')} bytes, "
          f"valid={validation.is_valid}, tiles={validation.stats['tiles']})")


# =========================================================================
# Tests de integración
# =========================================================================

def test_export_generated_world():
    """Exportar un mundo generado con WorldGenerator a .otbm."""
    gen = WorldGenerator(seed=42)
    world = gen.generate("Issavi hunt level 300")

    exporter = OTBMExporter(generate_templates=True)
    report = exporter.export(
        world,
        "output/test_hunt.otbm",
        generate_report=True,
    )

    assert Path("output/test_hunt.otbm").exists()
    assert report["tiles"] > 0
    assert report["items"] > 0
    assert report["status"] == "success"

    # Verificar XMLs
    assert Path("output/test_hunt.monster.xml").exists()
    assert Path("output/test_hunt.report.json").exists()

    with open("output/test_hunt.report.json") as f:
        json_report = json.load(f)
    assert json_report["tiles"] > 0
    assert json_report["status"] == "success"

    print(f"  [OK] Export generated world: {report['tiles']} tiles, "
          f"{report['items']} items, {report['spawns']} spawns, "
          f"{report['otbm_bytes']} bytes")


def test_export_with_spawns_and_items():
    """Exportar mundo con spawns e items adicionales."""
    world = WorldModel()

    # Tiles con ground
    world.set_tile(Tile(x=100, y=100, z=7, ground=817))
    world.set_tile(Tile(x=101, y=100, z=7, ground=415))

    # Items en tiles
    tile_with_items = Tile(x=102, y=100, z=7, ground=415)
    tile_with_items.items.append(Item(itemid=2050))  # Torch
    tile_with_items.items.append(Item(itemid=1503))  # Fountain
    world.set_tile(tile_with_items)

    # Spawns en tiles
    tile_with_spawn = Tile(x=103, y=100, z=7, ground=415)
    tile_with_spawn.spawn = Spawn(monster="Dragon", respawn=60, radius=5)
    world.set_tile(tile_with_spawn)

    # Estructura y región
    world.add_structure(Structure(
        name="temple", category="temple",
        x=100, y=100, z=7, width=10, height=10,
    ))
    world.add_region(Region(name="test", theme="issavi"))

    exporter = OTBMExporter(generate_templates=True)
    report = exporter.export(world, "output/test_spawns.otbm")

    assert Path("output/test_spawns.otbm").exists()
    assert report["tiles"] == 4
    assert report["items"] >= 5  # 4 grounds + 2 items
    assert report["spawns"] == 1

    # Verificar XML de monstruos
    monster_xml = Path("output/test_spawns.monster.xml").read_text()
    assert "Dragon" in monster_xml

    print(f"  [OK] Export with spawns: {report['tiles']} tiles, "
          f"{report['items']} items, {report['spawns']} spawns")


def test_export_bytes():
    """Exportar a bytes sin escribir archivo."""
    world = WorldModel()
    world.set_tile(Tile(x=0, y=0, z=7, ground=817))

    exporter = OTBMExporter()
    otbm_bytes = exporter.export_bytes(world)
    assert len(otbm_bytes) > 0
    assert otbm_bytes[:4] == b"OTBM"

    validator = OtbmValidator()
    result = validator.validate(otbm_bytes)
    assert result.is_valid

    print(f"  [OK] Export bytes: {len(otbm_bytes)} bytes, valid={result.is_valid}")


def test_export_empty_world():
    """Exportar mundo vacío."""
    world = WorldModel()
    exporter = OTBMExporter(generate_templates=False)
    report = exporter.export(world, "output/test_empty.otbm")

    assert report["status"] == "success" or report["status"] == "warning"
    print(f"  [OK] Export empty world: {report['status']}")


def test_validate():
    """Validar datos OTBM."""
    world = WorldModel()
    world.set_tile(Tile(x=0, y=0, z=7, ground=817))

    exporter = OTBMExporter()
    otbm_bytes = exporter.export_bytes(world)

    result = exporter.validate(otbm_bytes)
    assert result.is_valid
    assert result.stats["tiles"] >= 1

    # Validar datos inválidos
    bad_result = exporter.validate(b"INVALID")
    assert not bad_result.is_valid

    print(f"  [OK] Validate: valid={result.is_valid}, "
          f"tiles={result.stats.get('tiles', 0)}")


def test_generate_xmls():
    """Generar XMLs auxiliares sin exportar .otbm."""
    world = WorldModel()
    world.set_tile(Tile(x=0, y=0, z=7, ground=415))
    tile = world.get_tile(0, 0, 7)
    tile.spawn = Spawn(monster="Dragon", respawn=60)
    tile.items.append(Item(itemid=2050))

    world.add_structure(Structure(
        name="test_house", category="house",
        x=0, y=0, z=7, width=5, height=5,
    ))

    exporter = OTBMExporter()

    monster_xml = exporter.generate_monster_xml(world)
    assert "Dragon" in monster_xml
    assert "<monsters>" in monster_xml

    house_xml = exporter.generate_house_xml(world)
    assert "House" in house_xml or "<houses>" in house_xml or house_xml == ""

    waypoint_xml = exporter.generate_waypoint_xml(world)
    assert isinstance(waypoint_xml, str)

    print(f"  [OK] Generate XMLs: monster={len(monster_xml)} chars, "
          f"house={len(house_xml)} chars, waypoint={len(waypoint_xml)} chars")


def test_export_report_structure():
    """Verificar estructura del reporte de exportación."""
    world = WorldModel()
    world.set_tile(Tile(x=100, y=100, z=7, ground=817))

    exporter = OTBMExporter(generate_templates=False)
    report = exporter.export(world, "output/test_report.otbm")

    required_keys = {"tiles", "items", "spawns", "houses", "waypoints",
                     "otbm_bytes", "validation", "status", "files"}
    for key in required_keys:
        assert key in report, f"Falta clave: {key}"

    assert "otbm" in report["files"]
    assert "passed" in report["validation"]

    print(f"  [OK] Report structure: {list(report.keys())}")


# =========================================================================
# Runner
# =========================================================================

if __name__ == "__main__":
    tests = [
        ("Test Obligatorio", test_mandatory_export),
        ("Export generated world", test_export_generated_world),
        ("Export with spawns/items", test_export_with_spawns_and_items),
        ("Export bytes", test_export_bytes),
        ("Export empty world", test_export_empty_world),
        ("Validate", test_validate),
        ("Generate XMLs", test_generate_xmls),
        ("Report structure", test_export_report_structure),
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