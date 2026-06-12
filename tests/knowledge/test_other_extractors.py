"""Tests for the remaining extractors."""

from __future__ import annotations

import unittest

from core.knowledge.extractors import (
    BiomeExtractor,
    QuestExtractor,
    RaidExtractor,
    SpawnExtractor,
    StructureExtractor,
    WaypointExtractor,
)
from core.knowledge.models import EntryType


def _world(**kw) -> dict:
    base = {
        "meta": {"name": "test", "theme": "roshamuul"},
        "cities": [], "regions": [], "structures": [],
        "spawns": [], "waypoints": [], "quests": [],
    }
    base.update(kw)
    return base


class TestRaidExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = RaidExtractor()

    def test_extracts_raid_region(self):
        w = _world(regions=[{
            "name": "ferumbras_raid", "theme": "ferumbras",
            "min_level": 300, "max_level": 9999,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.RAID)

    def test_extracts_inquisition_structure(self):
        w = _world(structures=[{
            "name": "inquisition_lair", "category": "encounter",
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.RAID)

    def test_skips_non_raid(self):
        w = _world(regions=[{
            "name": "issavi_city_center", "theme": "issavi",
        }])
        self.assertEqual(self.ext.extract(w, source="src"), [])


class TestQuestExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = QuestExtractor()

    def test_extracts_quest_from_list(self):
        w = _world(quests=[{
            "name": "Soul War", "theme": "roshamuul",
            "difficulty": "hard", "style": "linear",
            "min_level": 250, "max_level": 500,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.QUEST)
        self.assertEqual(out[0].attributes["difficulty"], "hard")

    def test_extracts_quest_region(self):
        w = _world(regions=[{
            "name": "soul_war_quest", "theme": "roshamuul",
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.QUEST)

    def test_empty(self):
        self.assertEqual(self.ext.extract(_world()), [])


class TestSpawnExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = SpawnExtractor()

    def test_groups_by_zone(self):
        w = _world(spawns=[
            {"monster": "Guzzlemaw", "zone": "soul_war_surface", "level": 280},
            {"monster": "Guzzlemaw", "zone": "soul_war_surface", "level": 280},
            {"monster": "Hellflayer", "zone": "soul_war_surface", "level": 320},
        ])
        out = self.ext.extract(w, source="src")
        self.assertGreaterEqual(len(out), 1)
        guz = next((e for e in out if "Guzzlemaw" in e.name), None)
        self.assertIsNotNone(guz)
        self.assertEqual(guz.entry_type, EntryType.SPAWN)

    def test_no_spawns(self):
        self.assertEqual(self.ext.extract(_world()), [])

    def test_centroid(self):
        w = _world(spawns=[
            {"monster": "Rat", "zone": "z1", "level": 10, "x": 100, "y": 100},
            {"monster": "Rat", "zone": "z1", "level": 10, "x": 102, "y": 100},
        ])
        out = self.ext.extract(w, source="src")
        e = out[0]
        self.assertIn("centroid", e.attributes)
        self.assertEqual(e.attributes["centroid"], (101, 100))


class TestWaypointExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = WaypointExtractor()

    def test_extracts_waypoint(self):
        w = _world(waypoints=[{
            "name": "roshamuul_tp", "theme": "roshamuul", "x": 100, "y": 200, "z": 7,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.WAYPOINT)
        self.assertEqual(out[0].attributes["x"], 100)

    def test_empty(self):
        self.assertEqual(self.ext.extract(_world()), [])


class TestStructureExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = StructureExtractor()

    def test_extracts_dungeon_region(self):
        w = _world(regions=[{
            "name": "ancient_tomb", "theme": "roshamuul",
            "min_level": 200, "max_level": 400,
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.DUNGEON)

    def test_extracts_catchall_region(self):
        w = _world(regions=[{
            "name": "mysterious_island", "theme": "island",
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].entry_type, EntryType.REGION)

    def test_skips_known_categories(self):
        w = _world(regions=[{
            "name": "issavi_city", "theme": "issavi",
        }])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 0)


class TestBiomeExtractor(unittest.TestCase):
    def setUp(self):
        self.ext = BiomeExtractor()

    def test_extracts_from_region_themes(self):
        w = _world(regions=[
            {"name": "r1", "theme": "roshamuul", "min_level": 1, "max_level": 9999},
            {"name": "r2", "theme": "issavi", "min_level": 1, "max_level": 9999},
        ])
        out = self.ext.extract(w, source="src")
        themes = {e.name for e in out}
        self.assertIn("Roshamuul", themes)
        self.assertIn("Issavi", themes)

    def test_skips_generic(self):
        w = _world(regions=[{"name": "r1", "theme": "generic"}])
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 0)

    def test_explicit_biomes(self):
        w = {
            "meta": {"name": "test"},
            "cities": [], "regions": [], "structures": [],
            "spawns": [], "waypoints": [], "quests": [],
            "biomes": [{"name": "desert", "style": "wilderness"}],
        }
        out = self.ext.extract(w, source="src")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].name, "desert")
        self.assertEqual(out[0].entry_type, EntryType.BIOME)

    def test_dedupes_across_sources(self):
        w = {
            "meta": {"name": "test"},
            "cities": [], "regions": [], "structures": [],
            "spawns": [], "waypoints": [], "quests": [],
            "biomes": [{"name": "Roshamuul"}],
        }
        out = self.ext.extract(w, source="src")
        # only one — first match wins
        names = [e.name for e in out]
        self.assertEqual(len(names), len(set(names)))


if __name__ == "__main__":
    unittest.main()
