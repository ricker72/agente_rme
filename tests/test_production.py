"""
Comprehensive Production Test Suite — RME Map AI Agent v2.0

Covers all major subsystems:
- CLI interface
- World model
- Generators (hunt, city, dungeon)
- Exporters (Lua, OTBM)
- OTBM import/export roundtrip
- Preview generation
- Config manager
- Installer
- End-to-end pipeline

Target: 80%+ coverage across all modules.
"""

import sys
import os
import json
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.world import WorldModel, WorldValidator, Tile, Spawn, Item, Structure, Region  # noqa: E402
from core.generators import (  # noqa: E402
    WorldGenerator,
    HuntGenerator,
    CityGenerator,
    DungeonGenerator,
    ThemeGenerator,
)
from core.exporters import LuaExporter, LuaValidator, LuaWriter  # noqa: E402
from core.otbm import OTBMExporter, OTBMImporter  # noqa: E402
from core.preview import PreviewGenerator  # noqa: E402

# ═══════════════════════════════════════════════════════════════════════════════
# WORLD MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestWorldModel:
    def test_empty_world(self):
        world = WorldModel()
        assert world.tile_count() == 0
        assert world.region_count() == 0
        assert len(world.structures) == 0

    def test_set_tile(self):
        world = WorldModel()
        tile = Tile(x=10, y=20, z=7)
        tile.ground = 817
        world.set_tile(tile)
        assert world.tile_count() == 1
        retrieved = world.get_tile(10, 20, 7)
        assert retrieved is not None
        assert retrieved.ground == 817

    def test_multiple_tiles(self):
        world = WorldModel()
        for x in range(5):
            for y in range(5):
                tile = Tile(x=x, y=y, z=7)
                tile.ground = 415
                world.set_tile(tile)
        assert world.tile_count() == 25

    def test_add_region(self):
        world = WorldModel()
        region = Region(name="test_region", theme="issavi")
        world.add_region(region)
        assert world.region_count() == 1
        assert world.regions[0].theme == "issavi"

    def test_add_structure(self):
        world = WorldModel()
        struct = Structure(
            name="temple",
            category="temple",
            x=100,
            y=100,
            z=7,
            width=10,
            height=10,
        )
        world.add_structure(struct)
        assert len(world.structures) == 1

    def test_tile_with_items(self):
        world = WorldModel()
        tile = Tile(x=10, y=10, z=7)
        tile.ground = 415
        tile.items.append(Item(itemid=2050))
        tile.items.append(Item(itemid=1503))
        world.set_tile(tile)
        retrieved = world.get_tile(10, 10, 7)
        assert len(retrieved.items) == 2

    def test_tile_with_spawn(self):
        world = WorldModel()
        tile = Tile(x=10, y=10, z=7)
        tile.ground = 415
        tile.spawn = Spawn(monster="Dragon", respawn=60, radius=5)
        world.set_tile(tile)
        retrieved = world.get_tile(10, 10, 7)
        assert retrieved.spawn.monster == "Dragon"

    def test_world_validator(self):
        world = WorldModel()
        tile = Tile(x=0, y=0, z=7)
        tile.ground = 817
        world.set_tile(tile)
        validator = WorldValidator()
        result = validator.validate(world)
        assert result.passed


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGenerators:
    def test_world_generator_hunt(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        assert world.tile_count() > 0
        assert world.region_count() == 1

    def test_world_generator_city(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "city",
                "theme": "issavi",
                "level_min": 50,
                "level_max": 200,
            }
        )
        assert world.tile_count() > 0

    def test_world_generator_dungeon(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate(
            {
                "type": "dungeon",
                "theme": "library",
                "level_min": 200,
                "level_max": 400,
            }
        )
        assert world.tile_count() > 0

    def test_hunt_generator_direct(self):
        hg = HuntGenerator(seed=42)
        world = hg.generate(
            WorldModel(),
            {
                "theme": "issavi",
                "level_min": 300,
                "level_max": 500,
                "density": "high",
            },
        )
        assert world.tile_count() > 0

    def test_city_generator_direct(self):
        cg = CityGenerator(seed=42)
        world = cg.generate(
            WorldModel(),
            {
                "theme": "issavi",
                "level_min": 50,
                "level_max": 200,
            },
        )
        assert world.tile_count() > 0

    def test_dungeon_generator_direct(self):
        dg = DungeonGenerator(seed=42)
        world = dg.generate(
            WorldModel(),
            {
                "theme": "library",
                "level_min": 200,
                "level_max": 400,
            },
        )
        assert world.tile_count() > 0

    def test_theme_generator(self):
        tg = ThemeGenerator()
        theme = tg.resolve("issavi")
        assert theme.theme == "issavi"

    def test_theme_generator_multi(self):
        tg = ThemeGenerator()
        theme = tg.resolve_multi(["issavi", "roshamuul"])
        assert theme is not None


# ═══════════════════════════════════════════════════════════════════════════════
# LUA EXPORTER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestLuaExporter:
    def test_lua_export_basic(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        exporter = LuaExporter()
        lua_code = exporter.export(world)
        assert len(lua_code) > 0
        assert "app.hasMap()" in lua_code
        assert "app.transaction" in lua_code
        assert "getOrCreateTile" in lua_code

    def test_lua_export_has_ground(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        exporter = LuaExporter()
        lua_code = exporter.export(world)
        assert "tile.ground =" in lua_code

    def test_lua_export_to_file(self, tmp_path):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        exporter = LuaExporter()
        filepath = str(tmp_path / "test.lua")
        exporter.export_to_file(world, filepath)
        assert os.path.exists(filepath)
        with open(filepath) as f:
            content = f.read()
        assert "app.hasMap()" in content

    def test_lua_validate(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        exporter = LuaExporter()
        result = exporter.validate(world)
        assert result.passed

    def test_lua_validator_empty(self):
        validator = LuaValidator()
        result = validator.validate("")
        assert not result.passed

    def test_lua_validator_forbidden(self):
        validator = LuaValidator()
        bad_code = "Map.addItem(pos, 100)"
        result = validator.validate(bad_code)
        assert not result.passed

    def test_lua_writer(self):
        writer = LuaWriter()
        writer.header("Test")
        writer.transaction_begin()
        writer.set_ground(100, 100, 7, 415)
        writer.add_item(100, 100, 7, 2050)
        writer.set_spawn(100, 100, 7, "Dragon", 60)
        writer.transaction_end()
        writer.end_statement()
        code = writer.to_string()
        assert "Test" in code
        assert "app.transaction" in code
        assert "tile.ground = 415" in code


# ═══════════════════════════════════════════════════════════════════════════════
# OTBM EXPORTER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestOTBMExporter:
    def test_mandatory_export(self):
        world = WorldModel()
        tile = Tile(x=100, y=100, z=7)
        tile.ground = 817
        world.set_tile(tile)
        exporter = OTBMExporter(generate_templates=False)
        report = exporter.export(world, "output/test_prod_mandatory.otbm")
        assert Path("output/test_prod_mandatory.otbm").exists()
        assert report["tiles"] == 1
        assert report["status"] == "success"

    def test_export_with_spawns(self):
        world = WorldModel()
        tile = Tile(x=100, y=100, z=7)
        tile.ground = 817
        tile.spawn = Spawn(monster="Dragon", respawn=60, radius=5)
        world.set_tile(tile)
        exporter = OTBMExporter(generate_templates=True)
        report = exporter.export(world, "output/test_prod_spawns.otbm")
        assert report["tiles"] == 1
        assert report["spawns"] == 1

    def test_export_bytes(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=817))
        exporter = OTBMExporter()
        data = exporter.export_bytes(world)
        assert len(data) > 0
        assert data[:4] == b"OTBM"

    def test_export_empty_world(self):
        world = WorldModel()
        exporter = OTBMExporter(generate_templates=False)
        report = exporter.export(world, "output/test_prod_empty.otbm")
        assert report["status"] in ("success", "warning")

    def test_validate(self):
        world = WorldModel()
        world.set_tile(Tile(x=0, y=0, z=7, ground=817))
        exporter = OTBMExporter()
        data = exporter.export_bytes(world)
        result = exporter.validate(data)
        assert result.is_valid

    def test_generate_xmls(self):
        world = WorldModel()
        tile = Tile(x=0, y=0, z=7, ground=415)
        tile.spawn = Spawn(monster="Dragon", respawn=60)
        world.set_tile(tile)
        exporter = OTBMExporter()
        monster_xml = exporter.generate_monster_xml(world)
        assert "Dragon" in monster_xml

    def test_export_generated_world(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Issavi hunt level 300")
        exporter = OTBMExporter(generate_templates=True)
        report = exporter.export(world, "output/test_prod_hunt.otbm")
        assert report["tiles"] > 0
        assert report["status"] == "success"


# ═══════════════════════════════════════════════════════════════════════════════
# OTBM IMPORTER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestOTBMImporter:
    def test_import_file(self):
        # First export a world
        gen = WorldGenerator(seed=42)
        world = gen.generate("Issavi hunt level 300")
        exporter = OTBMExporter(generate_templates=False)
        otbm_path = "output/test_prod_import_src.otbm"
        exporter.export(world, otbm_path)

        # Now import it
        importer = OTBMImporter()
        result = importer.import_file(otbm_path)
        assert result["success"]
        assert result["stats"]["tiles"] > 0

    def test_import_bytes(self):
        world = WorldModel()
        world.set_tile(Tile(x=10, y=10, z=7, ground=817))
        exporter = OTBMExporter(generate_templates=False)
        data = exporter.export_bytes(world)

        importer = OTBMImporter()
        result = importer.import_bytes(data)
        assert result["success"]

    def test_import_nonexistent(self):
        importer = OTBMImporter()
        result = importer.import_file("nonexistent.otbm")
        assert not result["success"]

    def test_import_preview(self):
        world = WorldModel()
        world.set_tile(Tile(x=10, y=10, z=7, ground=817))
        exporter = OTBMExporter(generate_templates=False)
        data = exporter.export_bytes(world)

        importer = OTBMImporter()
        preview = importer.get_preview_from_bytes(data)
        assert preview.get("valid")
        assert preview.get("version", 0) >= 0

    def test_roundtrip(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Issavi hunt level 300")
        exporter = OTBMExporter(generate_templates=False)
        src_path = "output/test_prod_roundtrip_src.otbm"
        exporter.export(world, src_path)

        importer = OTBMImporter()
        result = importer.round_trip(src_path, "output/test_prod_roundtrip_dst.otbm")
        assert result["import_success"]
        assert Path("output/test_prod_roundtrip_dst.otbm").exists()


# ═══════════════════════════════════════════════════════════════════════════════
# PREVIEW GENERATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestPreviewGenerator:
    def test_preview_generation(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        preview_gen = PreviewGenerator()
        result = preview_gen.generate(
            world,
            output_png="output/test_prod_preview.png",
        )
        assert "png" in result or "json" in result

    def test_preview_png_only(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        preview_gen = PreviewGenerator()
        path = preview_gen.generate_png(world, "output/test_prod_preview_only.png")
        assert path is not None
        assert os.path.exists(path)

    def test_preview_minimap(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        preview_gen = PreviewGenerator()
        path = preview_gen.generate_minimap(world, "output/test_prod_minimap.png")
        assert path is not None

    def test_preview_report(self):
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        preview_gen = PreviewGenerator()
        report = preview_gen.generate_report(world)
        assert isinstance(report, dict)
        assert "summary" in report


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIG MANAGER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfigManager:
    def test_load_config(self):
        import config_manager as cm

        config = cm.load_config()
        assert isinstance(config, dict)
        assert "configured" in config

    def test_default_config(self):
        import config_manager as cm

        config = cm.DEFAULT_CONFIG
        assert config["configured"] is False
        assert "items_xml_path" in config

    def test_is_configured(self):
        import config_manager as cm

        assert not cm.is_configured({"configured": False})
        assert cm.is_configured({"configured": True})

    def test_validate_items_xml_missing(self):
        import config_manager as cm

        ok, msg = cm.validate_items_xml("")
        assert not ok

    def test_validate_tibia_path_missing(self):
        import config_manager as cm

        ok, msg = cm.validate_tibia_path("")
        assert not ok

    def test_validate_monsters_folder_missing(self):
        import config_manager as cm

        ok, msg = cm.validate_monsters_folder("")
        assert not ok

    def test_validate_npcs_folder_missing(self):
        import config_manager as cm

        ok, msg = cm.validate_npcs_folder("")
        assert not ok

    def test_validate_mounts_folder_empty(self):
        import config_manager as cm

        ok, msg = cm.validate_mounts_folder("")
        assert ok  # Optional

    def test_validate_all(self):
        import config_manager as cm

        config = {
            "tibia_client_path": "",
            "items_xml_path": "",
            "monsters_folder": "",
            "npcs_folder": "",
            "mounts_folder": "",
        }
        results = cm.validate_all(config)
        assert len(results) == 5


# ═══════════════════════════════════════════════════════════════════════════════
# CLI TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestCLI:
    def test_cli_info(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "cli.py", "info"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "RME Map AI Agent" in result.stdout

    def test_cli_help(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "cli.py", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "RME Map AI Agent" in result.stdout

    def test_cli_generate(self):
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "cli.py",
                "generate",
                "Generate Issavi hunt level 300",
                "--output",
                "output/cli_test",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60,
        )
        assert result.returncode == 0
        assert Path("output/cli_test/generated.lua").exists()
        assert Path("output/cli_test/generated.otbm").exists()

    def test_cli_export_lua(self):
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                "cli.py",
                "export",
                "--format",
                "lua",
                "--output",
                "output/cli_export_test",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            timeout=60,
        )
        assert result.returncode == 0
        assert Path("output/cli_export_test/exported.lua").exists()


# ═══════════════════════════════════════════════════════════════════════════════
# INSTALLER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestInstaller:
    def test_installer_check(self):
        import subprocess

        result = subprocess.run(
            [sys.executable, "installer/setup.py", "--check-only"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0

    def test_installer_creates_dirs(self):
        import subprocess

        subprocess.run(
            [sys.executable, "installer/setup.py", "--check-only"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert Path(PROJECT_ROOT / "output").exists()
        assert Path(PROJECT_ROOT / "cache").exists()
        assert Path(PROJECT_ROOT / "logs").exists()


# ═══════════════════════════════════════════════════════════════════════════════
# END-TO-END PIPELINE TEST
# ═══════════════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    def test_full_pipeline(self):
        """Full E2E: Prompt -> WorldGenerator -> Lua -> OTBM -> Preview"""
        t0 = time.time()

        # Step 1: Generate world
        gen = WorldGenerator(seed=42)
        world = gen.generate("Generate Issavi hunt level 300")
        assert world.tile_count() > 0
        t1 = time.time()

        # Step 2: Validate world
        validator = WorldValidator()
        vresult = validator.validate(world)
        assert vresult.passed
        t2 = time.time()

        # Step 3: Export Lua
        lua_exporter = LuaExporter()
        lua_code = lua_exporter.export(world, title="E2E Test")
        assert "app.hasMap()" in lua_code
        assert "app.transaction" in lua_code
        t3 = time.time()

        # Step 4: Validate Lua
        lua_validator = LuaValidator()
        lv_result = lua_validator.validate(lua_code)
        assert lv_result.passed
        t4 = time.time()

        # Step 5: Export OTBM
        otbm_exporter = OTBMExporter(generate_templates=True)
        report = otbm_exporter.export(world, "output/e2e_test.otbm")
        assert report["status"] == "success"
        assert report["tiles"] > 0
        t5 = time.time()

        # Step 6: Generate Preview
        preview_gen = PreviewGenerator()
        preview_gen.generate(
            world,
            output_png="output/e2e_preview.png",
        )
        t6 = time.time()

        # Step 7: Import OTBM back
        importer = OTBMImporter()
        import_result = importer.import_file("output/e2e_test.otbm")
        assert import_result["success"]
        t7 = time.time()

        # Save E2E report
        e2e_report = {
            "world_tiles": world.tile_count(),
            "regions": world.region_count(),
            "lua_bytes": len(lua_code),
            "otbm_tiles": report["tiles"],
            "otbm_bytes": report["otbm_bytes"],
            "import_success": import_result["success"],
            "imported_tiles": import_result["stats"].get("tiles", 0),
            "timings": {
                "generation": round(t1 - t0, 3),
                "validation": round(t2 - t1, 3),
                "lua_export": round(t3 - t2, 3),
                "lua_validate": round(t4 - t3, 3),
                "otbm_export": round(t5 - t4, 3),
                "preview": round(t6 - t5, 3),
                "otbm_import": round(t7 - t6, 3),
                "total": round(t7 - t0, 3),
            },
        }
        with open("output/e2e_report.json", "w") as f:
            json.dump(e2e_report, f, indent=2)

        print("\n  E2E Pipeline Summary:")
        print(f"    World: {world.tile_count()} tiles")
        print(f"    Lua: {len(lua_code)} bytes")
        print(f"    OTBM: {report['otbm_bytes']} bytes, {report['tiles']} tiles")
        print(f"    Import: {import_result['stats'].get('tiles', 0)} tiles")
        print(f"    Total: {e2e_report['timings']['total']:.3f}s")


# ═══════════════════════════════════════════════════════════════════════════════
# PYTHON RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
