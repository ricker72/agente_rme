"""Integration test for knowledge search and ranking across many sources."""

from __future__ import annotations

import unittest

from core.knowledge import (
    DatasetBuilder,
    EntryType,
    KnowledgeEngine,
    build_metrics,
)


def _src(name: str, theme: str, hunt_min: int = 250, hunt_max: int = 400) -> dict:
    return {
        "meta": {"name": name, "theme": theme},
        "regions": [
            {"name": f"{name}_circular_hunt", "theme": theme,
             "min_level": hunt_min, "max_level": hunt_max, "tags": ["circular"]},
            {"name": f"{name}_linear_hunt", "theme": theme,
             "min_level": hunt_min - 50, "max_level": hunt_max - 50,
             "tags": ["linear"]},
        ],
        "cities": [{"name": f"{name}_city", "theme": theme}],
        "structures": [{
            "name": f"{name}_boss_arena", "category": "boss_room",
            "theme": theme, "width": 30, "height": 30,
            "tags": ["boss", "circular"],
        }],
        "spawns": [
            {"monster": "Guzzlemaw", "zone": f"{name}_circular_hunt",
             "level": hunt_max - 50},
        ],
        "waypoints": [],
        "quests": [],
    }


class TestKnowledgeSearch(unittest.TestCase):
    def _engine(self) -> KnowledgeEngine:
        builder = DatasetBuilder()
        sources = [
            _src("roshamuul", "roshamuul", 280, 380),
            _src("soul_war", "roshamuul", 250, 500),
            _src("issavi", "issavi", 250, 400),
            _src("asura", "issavi", 300, 450),
            _src("yalahar", "yalahar", 200, 350),
        ]
        return KnowledgeEngine(dataset=builder.build_from_sources(sources))

    def test_search_by_theme(self):
        eng = self._engine()
        r = eng.query_text("hunts in roshamuul", k=10)
        self.assertGreater(r.total, 0)
        for m in r.matches:
            self.assertEqual(m.entry.biome, "roshamuul")

    def test_search_by_level(self):
        eng = self._engine()
        r = eng.query_structured(
            EntryType.HUNT, k=20, min_level=250, max_level=400,
        )
        self.assertGreater(r.total, 0)
        for m in r.matches[:5]:
            self.assertLessEqual(m.entry.min_level, 400)
            self.assertGreaterEqual(m.entry.max_level, 250)

    def test_find_similar_by_name(self):
        eng = self._engine()
        results = eng.find_similar_hunts("roshamuul_circular_hunt", k=5)
        self.assertGreater(len(results), 1)
        self.assertEqual(results[0]["match_type"], "exact")

    def test_recommender(self):
        eng = self._engine()
        target = eng.dataset.by_name("roshamuul_circular_hunt")
        self.assertIsNotNone(target)
        from core.knowledge.knowledge_recommender import KnowledgeRecommender
        rec = KnowledgeRecommender(eng.index, eng.ranker)
        result = rec.recommend_for_entry(target, k=3)
        self.assertGreater(result.total, 0)
        for m in result.matches:
            self.assertEqual(m.entry.entry_type, EntryType.HUNT)

    def test_metrics(self):
        eng = self._engine()
        m = build_metrics(eng.dataset)
        self.assertGreater(m.total_entries, 0)
        self.assertGreater(m.circular_hunts, 0)
        self.assertGreater(m.circular_boss_rooms, 0)

    def test_lookup_for_prompt(self):
        eng = self._engine()
        result = eng.lookup_for_prompt(
            "circular hunts in roshamuul level 300-500", k=3,
        )
        self.assertEqual(result["entry_type"], "hunt")
        self.assertEqual(result["biome"], "roshamuul")
        self.assertIsInstance(result["similar"], list)


if __name__ == "__main__":
    unittest.main()
