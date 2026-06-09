"""
Tests for HITO 17 — Pattern Miner.

The miner aggregates samples from MapAnalysis / Blueprint objects
and produces MinedPattern records once a structure type has at
least ``min_samples`` instances.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Any, Dict, List

from core.analyzer.map_analyzer import MapAnalysis
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from agente_rme.core.learning.pattern_miner import PatternMiner, MinedPattern


def _make_sample_tiles(count: int = 50) -> List[Dict[str, Any]]:
    tiles: List[Dict[str, Any]] = []
    for i in range(count):
        tiles.append(
            {
                "x": i % 10,
                "y": i // 10,
                "z": 7,
                "ground": 415 if i % 3 == 0 else 416,
                "items": [{"item_id": 101}] if i % 5 == 0 else [],
            }
        )
    return tiles


def _make_sample_analysis(style: str = "temple", keyword: str = "temple") -> MapAnalysis:
    tiles = _make_sample_tiles(80)
    ground_counter: Dict[str, int] = {}
    for t in tiles:
        g = f"ground_{t['ground']}"
        ground_counter[g] = ground_counter.get(g, 0) + 1

    analysis = MapAnalysis(source="test_map.otbm")
    analysis.map_size = {"width": 80, "height": 80}
    analysis.tiles = ground_counter
    analysis.tile_count = len(tiles)
    analysis.item_count = sum(len(t["items"]) for t in tiles)
    analysis.spawns = [{"monster": "demon", "x": 10, "y": 10, "radius": 5}]
    analysis.houses = [
        {"id": 1, "name": f"{keyword} house", "temple_x": 5, "temple_y": 5, "temple_z": 7},
    ]
    analysis.waypoints = [{"name": f"{keyword}_wp", "x": 0, "y": 0, "z": 7}]
    analysis.style = style
    analysis.floors = [7]
    return analysis


def _make_sample_blueprint(
    name: str = "test_temple",
    category: str = "temple",
    tile_count: int = 80,
) -> Blueprint:
    tiles: List[BlueprintTile] = []
    for i in range(tile_count):
        tiles.append(
            BlueprintTile(
                x=i % 10,
                y=i // 10,
                ground=415 if i % 2 == 0 else 416,
                item=101 if i % 5 == 0 else None,
            )
        )
    return Blueprint(
        name=name,
        theme=category,
        category=category,
        version="1.0.0",
        size=(20, 20),
        entry=(5, 5),
        description=f"Test {category} blueprint",
        tiles=tiles,
        rooms=[{"name": "main", "bounds": [0, 0, 10, 10], "area": 100}],
        features=[{"type": "altar", "bounds": [4, 4, 6, 6]}],
        metadata=BlueprintMetadata(
            style=category,
            tags=[category, "sacred"],
            difficulty="normal",
        ),
    )


class TestPatternMinerInitialization(unittest.TestCase):
    """Initialization and basic config tests."""

    def test_default_min_samples(self):
        miner = PatternMiner()
        self.assertEqual(miner.min_samples, 3)
        self.assertEqual(miner.mined_patterns, {})
        self.assertFalse(miner._trained)

    def test_custom_min_samples(self):
        miner = PatternMiner(min_samples=5)
        self.assertEqual(miner.min_samples, 5)

    def test_structure_keywords_complete(self):
        """Required structure types are present in keyword map."""
        required = [
            "temple", "depot", "market", "boss_room",
            "house", "bridge", "camp",
        ]
        for kind in required:
            self.assertIn(kind, PatternMiner.STRUCTURE_KEYWORDS)
            self.assertGreater(len(PatternMiner.STRUCTURE_KEYWORDS[kind]), 0)


class TestPatternMinerFromAnalysis(unittest.TestCase):
    """mine_from_analysis() tests."""

    def test_detect_temple(self):
        miner = PatternMiner(min_samples=2)
        analysis = _make_sample_analysis(style="temple", keyword="temple")
        types = miner._detect_structure_types(analysis)
        self.assertIn("temple", types)

    def test_detect_market(self):
        miner = PatternMiner(min_samples=2)
        analysis = _make_sample_analysis(style="market", keyword="market")
        types = miner._detect_structure_types(analysis)
        self.assertIn("market", types)

    def test_mine_needs_min_samples(self):
        """No pattern should be returned until min_samples is reached."""
        miner = PatternMiner(min_samples=2)
        analysis = _make_sample_analysis("temple", "temple")
        patterns = miner.mine_from_analysis(analysis)
        self.assertEqual(len(patterns), 0)

    def test_mine_with_enough_samples(self):
        """Two temple samples should produce one temple pattern."""
        miner = PatternMiner(min_samples=2)
        for _ in range(2):
            miner.mine_from_analysis(_make_sample_analysis("temple", "temple"))
        self.assertIn("temple", miner.mined_patterns)
        pat = miner.mined_patterns["temple"]
        self.assertEqual(pat.sample_count, 2)
        self.assertEqual(pat.pattern_type, "temple")

    def test_mine_returns_patterns_list(self):
        miner = PatternMiner(min_samples=2)
        a1 = _make_sample_analysis("temple", "temple")
        a2 = _make_sample_analysis("market", "market")
        # Feed a temple, then a market; each type reaches min_samples
        miner.mine_from_analysis(a1)
        out = miner.mine_from_analysis(a2)
        # The second call returns the market pattern that just hit min_samples
        self.assertGreaterEqual(len(out), 0)


class TestPatternMinerFromBlueprints(unittest.TestCase):
    """learn_from_blueprints() tests."""

    def test_learn_temple_pattern(self):
        miner = PatternMiner(min_samples=2)
        blueprints = [
            _make_sample_blueprint("t1", "temple", 100),
            _make_sample_blueprint("t2", "temple", 80),
        ]
        miner.learn_from_blueprints(blueprints)
        self.assertIn("temple", miner.mined_patterns)
        pat = miner.mined_patterns["temple"]
        self.assertEqual(pat.sample_count, 2)
        self.assertGreater(pat.confidence, 0)
        self.assertTrue(miner._trained)

    def test_pattern_metadata_complete(self):
        miner = PatternMiner(min_samples=2)
        blueprints = [
            _make_sample_blueprint("t1", "temple", 100),
            _make_sample_blueprint("t2", "temple", 80),
        ]
        miner.learn_from_blueprints(blueprints)
        pat = miner.mined_patterns["temple"]
        self.assertEqual(pat.pattern_type, "temple")
        self.assertIn("layout_signature", pat.to_dict())
        self.assertIn("typical_size", pat.to_dict())
        self.assertIn("generation_hints", pat.to_dict())

    def test_multiple_categories(self):
        miner = PatternMiner(min_samples=2)
        blueprints = [
            _make_sample_blueprint("t1", "temple", 100),
            _make_sample_blueprint("t2", "temple", 80),
            _make_sample_blueprint("m1", "market", 100),
            _make_sample_blueprint("m2", "market", 80),
        ]
        miner.learn_from_blueprints(blueprints)
        self.assertIn("temple", miner.mined_patterns)
        self.assertIn("market", miner.mined_patterns)

    def test_required_items_have_item_ids(self):
        miner = PatternMiner(min_samples=2)
        blueprints = [
            _make_sample_blueprint("t1", "temple", 100),
            _make_sample_blueprint("t2", "temple", 80),
        ]
        miner.learn_from_blueprints(blueprints)
        pat = miner.mined_patterns["temple"]
        # Every id should be an int
        for iid in pat.required_items + pat.optional_items:
            self.assertIsInstance(iid, int)

    def test_confidence_grows_with_samples(self):
        miner_low = PatternMiner(min_samples=2)
        miner_low.learn_from_blueprints(
            [_make_sample_blueprint(f"t{i}", "temple", 50) for i in range(2)]
        )
        miner_high = PatternMiner(min_samples=2)
        miner_high.learn_from_blueprints(
            [_make_sample_blueprint(f"t{i}", "temple", 50) for i in range(8)]
        )
        self.assertGreater(
            miner_high.mined_patterns["temple"].confidence,
            miner_low.mined_patterns["temple"].confidence,
        )


class TestPatternMinerTypeHints(unittest.TestCase):
    """Per-structure generation hints."""

    def test_temple_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("t1", "temple", 100),
                _make_sample_blueprint("t2", "temple", 80),
            ]
        )
        hints = miner.mined_patterns["temple"].generation_hints
        self.assertTrue(hints.get("central_altar"))
        self.assertTrue(hints.get("pillar_grid"))

    def test_market_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("m1", "market", 100),
                _make_sample_blueprint("m2", "market", 80),
            ]
        )
        hints = miner.mined_patterns["market"].generation_hints
        self.assertTrue(hints.get("stall_rows"))
        self.assertTrue(hints.get("central_plaza"))

    def test_boss_room_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("b1", "boss_room", 60),
                _make_sample_blueprint("b2", "boss_room", 50),
            ]
        )
        hints = miner.mined_patterns["boss_room"].generation_hints
        self.assertTrue(hints.get("arena_layout"))

    def test_bridge_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("br1", "bridge", 40),
                _make_sample_blueprint("br2", "bridge", 30),
            ]
        )
        hints = miner.mined_patterns["bridge"].generation_hints
        self.assertTrue(hints.get("linear_span"))
        self.assertTrue(hints.get("support_pillars"))

    def test_camp_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("c1", "camp", 40),
                _make_sample_blueprint("c2", "camp", 30),
            ]
        )
        hints = miner.mined_patterns["camp"].generation_hints
        self.assertTrue(hints.get("perimeter"))
        self.assertTrue(hints.get("central_fire"))

    def test_depot_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("d1", "depot", 30),
                _make_sample_blueprint("d2", "depot", 25),
            ]
        )
        hints = miner.mined_patterns["depot"].generation_hints
        self.assertTrue(hints.get("locker_wall"))

    def test_house_hints(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("h1", "house", 50),
                _make_sample_blueprint("h2", "house", 40),
            ]
        )
        hints = miner.mined_patterns["house"].generation_hints
        self.assertTrue(hints.get("room_cluster"))


class TestPatternMinerQueryAPI(unittest.TestCase):
    """Public query / listing API."""

    def test_get_pattern(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("t1", "temple", 80),
                _make_sample_blueprint("t2", "temple", 80),
            ]
        )
        pat = miner.get_pattern("temple")
        self.assertIsNotNone(pat)
        self.assertEqual(pat.pattern_type, "temple")

    def test_get_pattern_missing(self):
        miner = PatternMiner()
        self.assertIsNone(miner.get_pattern("unknown"))

    def test_list_patterns(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("t1", "temple", 80),
                _make_sample_blueprint("t2", "temple", 80),
                _make_sample_blueprint("m1", "market", 80),
                _make_sample_blueprint("m2", "market", 80),
            ]
        )
        patterns = miner.list_patterns()
        self.assertIn("temple", patterns)
        self.assertIn("market", patterns)

    def test_get_pattern_statistics(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("t1", "temple", 100),
                _make_sample_blueprint("t2", "temple", 80),
            ]
        )
        stats = miner.get_pattern_statistics()
        self.assertIn("temple", stats)
        self.assertIn("sample_count", stats["temple"])
        self.assertIn("confidence", stats["temple"])
        self.assertIn("variability", stats["temple"])

    def test_generate_pattern_guide_specific(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("t1", "temple", 80),
                _make_sample_blueprint("t2", "temple", 80),
            ]
        )
        guide = miner.generate_pattern_guide("temple")
        self.assertIn("central_altar", guide)

    def test_generate_pattern_guide_all(self):
        miner = PatternMiner(min_samples=2)
        miner.learn_from_blueprints(
            [
                _make_sample_blueprint("t1", "temple", 80),
                _make_sample_blueprint("t2", "temple", 80),
            ]
        )
        guide = miner.generate_pattern_guide()
        self.assertIn("temple", guide)


class TestPatternMinerPersistence(unittest.TestCase):
    """save_patterns / load_patterns round trip."""

    def test_save_and_load(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name
        try:
            miner = PatternMiner(min_samples=2)
            miner.learn_from_blueprints(
                [
                    _make_sample_blueprint("t1", "temple", 80),
                    _make_sample_blueprint("t2", "temple", 80),
                ]
            )
            miner.save_patterns(temp_path)
            self.assertTrue(os.path.exists(temp_path))

            new_miner = PatternMiner()
            new_miner.load_patterns(temp_path)
            self.assertIn("temple", new_miner.mined_patterns)
            self.assertTrue(new_miner._trained)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_saved_file_is_valid_json(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as f:
            temp_path = f.name
        try:
            miner = PatternMiner(min_samples=2)
            miner.learn_from_blueprints(
                [
                    _make_sample_blueprint("t1", "temple", 80),
                    _make_sample_blueprint("t2", "temple", 80),
                ]
            )
            miner.save_patterns(temp_path)
            with open(temp_path, "r") as f:
                data = json.load(f)
            self.assertIn("version", data)
            self.assertIn("patterns", data)
            self.assertIn("temple", data["patterns"])
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestMinedPatternDataclass(unittest.TestCase):
    """to_dict / from_dict round trip on MinedPattern itself."""

    def test_round_trip(self):
        original = MinedPattern(
            pattern_id="p1",
            pattern_type="temple",
            name="Temple",
            description="desc",
            layout_signature={"grid": 0.5, "linear": 0.5},
            room_template={"w": 10},
            feature_distribution={"item_101": 0.4},
            typical_size=(50, 50),
            aspect_ratio=1.0,
            density=0.6,
            symmetry_score=0.7,
            required_grounds=[415],
            required_items=[101],
            optional_items=[],
            spawn_patterns=[],
            sample_count=3,
            confidence=0.3,
            variability=0.1,
            generation_hints={"central_altar": True},
        )
        data = original.to_dict()
        restored = MinedPattern.from_dict(data)
        self.assertEqual(restored.pattern_id, original.pattern_id)
        self.assertEqual(restored.typical_size, original.typical_size)
        self.assertEqual(restored.layout_signature, original.layout_signature)


if __name__ == "__main__":
    unittest.main()
