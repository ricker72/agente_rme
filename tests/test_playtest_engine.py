"""Tests for the Playtest Engine (integration)."""

import sys
import os
import json
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.playtest.playtest_engine import PlaytestEngine, DEFAULT_MONSTERS
from core.playtest.report_generator import PlaytestReport, ReportGenerator


def _build_hunt_world() -> WorldModel:
    world = WorldModel()
    region = Region(name="issavi_hunt")
    world.regions.append(region)

    monster_names = ["Dragon", "Hydra", "Demon", "Vampire", "Dragon"]
    idx = 0
    for x in range(30):
        for y in range(30):
            tile = Tile(x=x, y=y, z=7, ground=100)
            if (x + y) % 5 == 0:
                monster = monster_names[idx % len(monster_names)]
                tile.spawn = Spawn(monster=monster, respawn=60, radius=5)
                idx += 1
            world.set_tile(tile)
    return world


def _build_empty_world() -> WorldModel:
    world = WorldModel()
    for x in range(10):
        for y in range(10):
            tile = Tile(x=x, y=y, z=7, ground=100)
            world.set_tile(tile)
    return world


def _build_multi_zone_world() -> WorldModel:
    world = WorldModel()

    r1 = Region(name="easy_zone")
    world.regions.append(r1)
    for x in range(20):
        for y in range(20):
            tile = Tile(x=x, y=y, z=7, ground=100)
            if (x + y) % 6 == 0:
                tile.spawn = Spawn(monster="Rat")
            world.set_tile(tile)

    r2 = Region(name="hard_zone")
    world.regions.append(r2)
    for x in range(25, 45):
        for y in range(20):
            tile = Tile(x=x, y=y, z=7, ground=100)
            if (x + y) % 4 == 0:
                tile.spawn = Spawn(monster="Demon")
            world.set_tile(tile)

    return world


class TestPlaytestEngineInit:
    def test_default_init(self):
        engine = PlaytestEngine()
        assert engine._player_level == 300
        assert engine._rotation_minutes == 60.0

    def test_custom_init(self):
        engine = PlaytestEngine(seed=42, player_level=150, rotation_minutes=30.0)
        assert engine._seed == 42
        assert engine._player_level == 150
        assert engine._rotation_minutes == 30.0


class TestPlaytestEngineRun:
    def test_run_on_hunt_world(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        assert isinstance(report, PlaytestReport)
        assert report.zone_count > 0
        assert report.total_spawns > 0

    def test_run_produces_report(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42)
        report = engine.run(world)
        assert isinstance(report.playable, bool)
        assert report.difficulty in ("trivial", "easy", "medium", "hard", "extreme")
        assert report.xp_hour >= 0
        assert report.loot_hour >= 0
        assert report.difficulty_score >= 0
        assert isinstance(report.issues, list)
        assert isinstance(report.recommendations, list)
        assert isinstance(report.vocation_results, dict)

    def test_run_vocation_results(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        assert len(report.vocation_results) == 5
        for voc in ["knight", "paladin", "druid", "sorcerer", "monk"]:
            assert voc in report.vocation_results
            voc_data = report.vocation_results[voc]
            assert "xp_per_hour" in voc_data
            assert "deaths" in voc_data

    def test_run_quick(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run_quick(world)
        assert isinstance(report, PlaytestReport)
        assert report.zone_count > 0

    def test_run_deterministic(self):
        world1 = _build_hunt_world()
        world2 = _build_hunt_world()
        engine1 = PlaytestEngine(seed=42, player_level=300)
        engine2 = PlaytestEngine(seed=42, player_level=300)
        r1 = engine1.run(world1)
        r2 = engine2.run(world2)
        assert r1.xp_hour == r2.xp_hour
        assert r1.deaths == r2.deaths


class TestPlaytestEngineEdgeCases:
    def test_empty_world(self):
        world = _build_empty_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        assert isinstance(report, PlaytestReport)
        assert report.playable is False

    def test_world_no_regions(self):
        world = WorldModel()
        for x in range(5):
            for y in range(5):
                tile = Tile(x=x, y=y, z=7, ground=100)
                tile.spawn = Spawn(monster="Dragon")
                world.set_tile(tile)
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        assert isinstance(report, PlaytestReport)

    def test_level_override(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world, level=100)
        assert report.vocation_results["knight"]["xp_per_hour"] >= 0


class TestPlaytestReportSerialization:
    def test_to_dict(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        d = report.to_dict()
        assert isinstance(d, dict)
        assert "playable" in d
        assert "difficulty" in d
        assert "xp_hour" in d
        assert "loot_hour" in d
        assert "deaths" in d
        assert "issues" in d
        assert "metrics" in d
        assert "vocation_results" in d

    def test_to_json(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["playable"] in (True, False)
        assert isinstance(parsed["xp_hour"], int)
        assert isinstance(parsed["deaths"], int)

    def test_save_and_load(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        gen = ReportGenerator()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name
        try:
            gen.save_report(report, path)
            loaded = gen.load_report(path)
            assert loaded.playable == report.playable
            assert loaded.difficulty == report.difficulty
            assert abs(loaded.xp_hour - report.xp_hour) < 1.0
            assert loaded.zone_count == report.zone_count
        finally:
            os.unlink(path)

    def test_format_summary(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        gen = ReportGenerator()
        summary = gen.format_summary(report)
        assert "PLAYTEST REPORT" in summary
        assert "Playable" in summary
        assert "XP/Hour" in summary


class TestMultiZonePlaytest:
    def test_multi_zone_analysis(self):
        world = _build_multi_zone_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        assert report.zone_count >= 2
        assert isinstance(report.vocation_results, dict)


class TestMonsterDatabase:
    def test_default_monsters_populated(self):
        assert len(DEFAULT_MONSTERS) > 0
        assert "Dragon" in DEFAULT_MONSTERS
        assert "Demon" in DEFAULT_MONSTERS
        assert "Rat" in DEFAULT_MONSTERS

    def test_monster_stats_structure(self):
        for name, data in DEFAULT_MONSTERS.items():
            assert "health" in data
            assert "attack" in data
            assert "defense" in data
            assert "magic_defense" in data
            assert "experience" in data
            assert "level" in data
            assert data["health"] > 0
            assert data["attack"] > 0


class TestReportGenerator:
    def test_generate_playable(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=1000000, loot_per_hour=200000,
            deaths=2, survival_rate=0.95, zone_count=3, total_spawns=150,
        )
        assert report.playable is True
        assert report.difficulty == "medium"

    def test_generate_not_playable_low_xp(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=10000, deaths=2, survival_rate=0.95,
            zone_count=3, total_spawns=150,
        )
        assert report.playable is False
        assert any("XP" in i or "xp" in i.lower() for i in report.issues)

    def test_generate_not_playable_many_deaths(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=1000000, deaths=20, survival_rate=0.95,
            zone_count=3, total_spawns=150,
        )
        assert report.playable is False
        assert any("death" in i.lower() for i in report.issues)

    def test_generate_not_playable_low_survival(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=1000000, deaths=5, survival_rate=0.3,
            zone_count=3, total_spawns=150,
        )
        assert report.playable is False

    def test_generate_not_playable_no_spawns(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=1000000, deaths=0, survival_rate=1.0,
            zone_count=3, total_spawns=0,
        )
        assert report.playable is False

    def test_generate_not_playable_no_zones(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=1000000, deaths=0, survival_rate=1.0,
            zone_count=0, total_spawns=0,
        )
        assert report.playable is False

    def test_report_to_json_roundtrip(self):
        gen = ReportGenerator()
        report = gen.generate(
            xp_per_hour=500000, deaths=1, survival_rate=0.98,
            zone_count=2, total_spawns=80,
        )
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["playable"] is True
        assert parsed["xp_hour"] == 500000


class TestPlaytestIntegration:
    def test_mandatory_example_pattern(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        report = engine.run(world)
        assert isinstance(report, PlaytestReport)
        assert report.xp_hour > 0

    def test_quick_vs_full_consistency(self):
        world = _build_hunt_world()
        engine = PlaytestEngine(seed=42, player_level=300)
        full = engine.run(world)
        quick = engine.run_quick(world)
        assert full.zone_count == quick.zone_count
        assert full.total_spawns == quick.total_spawns