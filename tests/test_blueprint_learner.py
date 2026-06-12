"""
Tests for HITO 17 — Blueprint Learner and related modules.

Tests:
- BlueprintLearner: learn_from_otbm, learn_from_analysis, learn_batch
- PatternMiner: mine_from_analysis, learn_from_blueprints, pattern guides
- BlueprintRanker: ranking criteria, score breakdown
- BlueprintCatalog: add, search, statistics
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Any, Dict, List

# Core imports
from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from core.analyzer.map_analyzer import MapAnalysis

# Learning imports
from core.learning.blueprint_learner import BlueprintLearner, LearningResult
from core.learning.pattern_miner import PatternMiner
from core.learning.blueprint_ranker import BlueprintRanker
from core.learning.blueprint_catalog import BlueprintCatalog

# ==============================================================================
# Shared Test Helpers
# ==============================================================================


def _make_sample_tiles(count: int = 50) -> List[Dict[str, Any]]:
    """Generate sample tiles."""
    tiles = []
    for i in range(count):
        x = i % 10
        y = i // 10
        ground = 415 if i % 3 == 0 else (416 if i % 3 == 1 else 393)
        items = []
        if i % 5 == 0:
            items.append({"item_id": 101})
        tiles.append(
            {
                "x": x,
                "y": y,
                "z": 7,
                "ground": ground,
                "items": items,
            }
        )
    return tiles


def _make_sample_spawns(count: int = 5) -> List[Dict[str, Any]]:
    """Generate sample spawns."""
    monsters = ["dragon", "demon", "rotworm", "troll", "skeleton"]
    return [
        {
            "monster": monsters[i % len(monsters)],
            "x": i * 10,
            "y": i * 5,
            "radius": 5,
        }
        for i in range(count)
    ]


def _make_sample_houses(count: int = 3) -> List[Dict[str, Any]]:
    """Generate sample houses."""
    return [
        {
            "id": i + 1,
            "name": f"House {i}",
            "temple_x": i * 20 + 5,
            "temple_y": i * 15 + 5,
            "temple_z": 7,
        }
        for i in range(count)
    ]


def _make_sample_waypoints(count: int = 3) -> List[Dict[str, Any]]:
    """Generate sample waypoints."""
    return [{"name": f"wp_{i}", "x": i * 10, "y": i * 10, "z": 7} for i in range(count)]


def _make_sample_analysis(style: str = "temple") -> MapAnalysis:
    """Create a sample MapAnalysis."""
    tiles = _make_sample_tiles(100)
    ground_counter = {}
    for t in tiles:
        g = f"ground_{t['ground']}"
        ground_counter[g] = ground_counter.get(g, 0) + 1

    analysis = MapAnalysis(source="test_map.otbm")
    analysis.map_size = {"width": 100, "height": 100}
    analysis.tiles = ground_counter
    analysis.tile_count = len(tiles)
    analysis.item_count = 20
    analysis.spawns = _make_sample_spawns(5)
    analysis.houses = _make_sample_houses(2)
    analysis.waypoints = _make_sample_waypoints(3)
    analysis.style = style
    analysis.floors = [7]
    return analysis


def _make_sample_blueprint(
    name: str = "test_temple",
    theme: str = "temple",
    category: str = "temple",
    tile_count: int = 100,
) -> Blueprint:
    """Create a sample Blueprint."""
    tiles = []
    for i in range(tile_count):
        x = i % 10
        y = i // 10
        ground = 415 if i % 2 == 0 else 416
        item = 101 if i % 5 == 0 else None
        tiles.append(BlueprintTile(x=x, y=y, ground=ground, item=item))

    return Blueprint(
        name=name,
        theme=theme,
        category=category,
        version="1.0.0",
        size=(20, 20),
        entry=(5, 5),
        description=f"Test {theme} blueprint",
        tiles=tiles,
        rooms=[{"name": "main_chamber", "bounds": [0, 0, 10, 10], "area": 100}],
        zones=[{"name": "sanctuary", "type": "temple"}],
        features=[{"type": "altar", "bounds": [4, 4, 6, 6]}],
        metadata=BlueprintMetadata(
            style=theme,
            era="ancient",
            difficulty="normal",
            tags=[theme, "sacred"],
            capacity="medium",
        ),
    )


# ==============================================================================
# Test Classes
# ==============================================================================


class TestPatternMiner(unittest.TestCase):
    """Tests for PatternMiner."""

    def setUp(self):
        self.miner = PatternMiner(min_samples=2)

    def test_detect_structure_types(self):
        """Test structure type detection from analysis."""
        analysis = _make_sample_analysis("temple")
        types = self.miner._detect_structure_types(analysis)
        self.assertIn("temple", types)

    def test_mine_from_analysis(self):
        """Test mining patterns from analysis."""
        analysis = _make_sample_analysis("temple")
        patterns = self.miner.mine_from_analysis(analysis)
        # With min_samples=2, need 2 analyses for a pattern
        self.assertEqual(len(patterns), 0)

    def test_learn_from_blueprints(self):
        """Test learning from blueprints."""
        blueprints = [
            _make_sample_blueprint("temple_1", "temple", "temple", 100),
            _make_sample_blueprint("temple_2", "temple", "temple", 80),
        ]
        self.miner.learn_from_blueprints(blueprints)
        self.assertIn("temple", self.miner.mined_patterns)
        pattern = self.miner.mined_patterns["temple"]
        self.assertEqual(pattern.pattern_type, "temple")
        self.assertEqual(pattern.sample_count, 2)

    def test_pattern_generation_hints(self):
        """Test generation hints for temple pattern."""
        blueprints = [
            _make_sample_blueprint("temple_1", "temple", "temple", 100),
            _make_sample_blueprint("temple_2", "temple", "temple", 80),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["temple"]
        hints = pattern.generation_hints
        self.assertIn("central_altar", hints)
        self.assertIn("pillar_grid", hints)

    def test_market_pattern_hints(self):
        """Test market pattern hints."""
        blueprints = [
            _make_sample_blueprint("market_1", "market", "market", 100),
            _make_sample_blueprint("market_2", "market", "market", 80),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["market"]
        hints = pattern.generation_hints
        self.assertIn("stall_rows", hints)
        self.assertIn("central_plaza", hints)

    def test_camp_pattern_hints(self):
        """Test camp pattern hints."""
        blueprints = [
            _make_sample_blueprint("camp_1", "camp", "camp", 50),
            _make_sample_blueprint("camp_2", "camp", "camp", 40),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["camp"]
        hints = pattern.generation_hints
        self.assertIn("perimeter", hints)
        self.assertIn("central_fire", hints)

    def test_boss_room_pattern_hints(self):
        """Test boss room pattern hints."""
        blueprints = [
            _make_sample_blueprint("boss_1", "boss_room", "boss_room", 60),
            _make_sample_blueprint("boss_2", "boss_room", "boss_room", 50),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["boss_room"]
        hints = pattern.generation_hints
        self.assertIn("arena_layout", hints)
        self.assertIn("boss_platform", hints)

    def test_bridge_pattern_hints(self):
        """Test bridge pattern hints."""
        blueprints = [
            _make_sample_blueprint("bridge_1", "bridge", "bridge", 40),
            _make_sample_blueprint("bridge_2", "bridge", "bridge", 30),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["bridge"]
        hints = pattern.generation_hints
        self.assertIn("linear_span", hints)
        self.assertIn("support_pillars", hints)

    def test_depot_pattern_hints(self):
        """Test depot pattern hints."""
        blueprints = [
            _make_sample_blueprint("depot_1", "depot", "depot", 30),
            _make_sample_blueprint("depot_2", "depot", "depot", 25),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["depot"]
        hints = pattern.generation_hints
        self.assertIn("locker_wall", hints)
        self.assertIn("open_floor", hints)

    def test_house_pattern_hints(self):
        """Test house pattern hints."""
        blueprints = [
            _make_sample_blueprint("house_1", "house", "house", 50),
            _make_sample_blueprint("house_2", "house", "house", 40),
        ]
        self.miner.learn_from_blueprints(blueprints)
        pattern = self.miner.mined_patterns["house"]
        hints = pattern.generation_hints
        self.assertIn("room_cluster", hints)
        self.assertIn("entrance_area", hints)

    def test_get_pattern_guide(self):
        """Test generating pattern guide."""
        blueprints = [
            _make_sample_blueprint("temple_1", "temple", "temple", 100),
            _make_sample_blueprint("temple_2", "temple", "temple", 80),
        ]
        self.miner.learn_from_blueprints(blueprints)
        guide = self.miner.generate_pattern_guide("temple")
        self.assertIn("central_altar", guide)

    def test_list_patterns(self):
        """Test listing mined patterns."""
        # Need 2 samples per type since min_samples=2
        blueprints = [
            _make_sample_blueprint("temple_1", "temple", "temple", 100),
            _make_sample_blueprint("temple_2", "temple", "temple", 80),
            _make_sample_blueprint("market_1", "market", "market", 80),
            _make_sample_blueprint("market_2", "market", "market", 60),
        ]
        self.miner.learn_from_blueprints(blueprints)
        patterns = self.miner.list_patterns()
        self.assertIn("temple", patterns)
        self.assertIn("market", patterns)

    def test_save_load_patterns(self):
        """Test saving and loading patterns."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            blueprints = [
                _make_sample_blueprint("temple_1", "temple", "temple", 100),
                _make_sample_blueprint("temple_2", "temple", "temple", 80),
            ]
            self.miner.learn_from_blueprints(blueprints)
            self.miner.save_patterns(temp_path)

            # Create new miner and load
            new_miner = PatternMiner()
            new_miner.load_patterns(temp_path)
            self.assertIn("temple", new_miner.mined_patterns)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestBlueprintRanker(unittest.TestCase):
    """Tests for BlueprintRanker."""

    def setUp(self):
        self.ranker = BlueprintRanker()

    def test_rank_single_blueprint(self):
        """Test ranking a single blueprint."""
        bp = _make_sample_blueprint("test", "temple", "temple", 100)
        ranked = self.ranker.rank_blueprints([bp])
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0].rank, 1)
        self.assertGreater(ranked[0].overall_score, 0)

    def test_rank_multiple_blueprints(self):
        """Test ranking multiple blueprints."""
        blueprints = [
            _make_sample_blueprint("good_temple", "temple", "temple", 150),
            _make_sample_blueprint("poor_temple", "temple", "temple", 10),
        ]
        ranked = self.ranker.rank_blueprints(blueprints)
        self.assertEqual(len(ranked), 2)
        # Good temple should rank higher
        self.assertEqual(ranked[0].blueprint.name, "good_temple")

    def test_score_breakdown_present(self):
        """Test that score breakdown contains all components."""
        bp = _make_sample_blueprint("test", "temple", "temple", 100)
        ranked = self.ranker.rank_blueprints([bp])
        breakdown = ranked[0].score_breakdown
        expected_keys = [
            "structural_completeness",
            "tile_quality",
            "pattern_consistency",
            "metadata_richness",
            "similarity_bonus",
            "generation_suitability",
        ]
        for key in expected_keys:
            self.assertIn(key, breakdown)

    def test_recommendations_generated(self):
        """Test that recommendations are generated."""
        bp = _make_sample_blueprint("test", "temple", "temple", 10)  # Small
        ranked = self.ranker.rank_blueprints([bp])
        recs = ranked[0].recommendations
        self.assertIsInstance(recs, list)
        # Should have recommendations for small tile count
        self.assertTrue(any("tile count" in r.lower() for r in recs))

    def test_percentile_assigned(self):
        """Test percentiles are assigned correctly."""
        blueprints = [
            _make_sample_blueprint(f"bp_{i}", "temple", "temple", 50 + i * 10)
            for i in range(5)
        ]
        ranked = self.ranker.rank_blueprints(blueprints)
        self.assertEqual(ranked[0].percentile, 1.0)
        self.assertEqual(ranked[-1].percentile, 0.0)

    def test_ranking_summary(self):
        """Test ranking summary statistics."""
        blueprints = [
            _make_sample_blueprint(f"bp_{i}", "temple", "temple", 100)
            for i in range(10)
        ]
        ranked = self.ranker.rank_blueprints(blueprints)
        summary = self.ranker.get_ranking_summary(ranked)
        self.assertEqual(summary["total_ranked"], 10)
        self.assertIn("avg_score", summary)
        self.assertIn("score_distribution", summary)

    def test_custom_weights(self):
        """Test custom scoring weights."""
        config = {"weights": {"tile_quality": 0.5, "structural_completeness": 0.5}}
        ranker = BlueprintRanker(config=config)
        bp = _make_sample_blueprint("test", "temple", "temple", 200)
        ranked = ranker.rank_blueprints([bp])
        self.assertGreater(ranked[0].overall_score, 0)

    def test_save_rankings(self):
        """Test saving rankings to JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            bp = _make_sample_blueprint("test", "temple", "temple", 100)
            ranked = self.ranker.rank_blueprints([bp])
            self.ranker.save_rankings(ranked, temp_path)

            with open(temp_path, "r") as f:
                data = json.load(f)
            self.assertIn("rankings", data)
            self.assertIn("summary", data)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestBlueprintCatalog(unittest.TestCase):
    """Tests for BlueprintCatalog."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="test_catalog_")
        self.catalog = BlueprintCatalog(catalog_dir=self.tmp_dir)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_add_blueprint(self):
        """Test adding a blueprint to catalog."""
        bp = _make_sample_blueprint("test_temple", "temple", "temple", 100)
        entry = self.catalog.add_blueprint(bp)
        self.assertEqual(entry.name, "test_temple")
        self.assertEqual(entry.theme, "temple")
        self.assertEqual(self.catalog.count(), 1)

    def test_get_blueprint(self):
        """Test retrieving a blueprint."""
        bp = _make_sample_blueprint("get_test", "temple", "temple", 100)
        self.catalog.add_blueprint(bp)
        retrieved = self.catalog.get_blueprint("get_test")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "get_test")

    def test_remove_blueprint(self):
        """Test removing a blueprint."""
        bp = _make_sample_blueprint("remove_test", "temple", "temple", 100)
        self.catalog.add_blueprint(bp)
        self.assertEqual(self.catalog.count(), 1)
        self.catalog.remove_blueprint("remove_test")
        self.assertEqual(self.catalog.count(), 0)

    def test_by_theme(self):
        """Test filtering by theme."""
        self.catalog.add_blueprint(_make_sample_blueprint("t1", "temple", "temple", 50))
        self.catalog.add_blueprint(_make_sample_blueprint("h1", "hunt", "hunting", 50))
        self.catalog.add_blueprint(_make_sample_blueprint("t2", "temple", "temple", 50))

        temples = self.catalog.by_theme("temple")
        self.assertEqual(len(temples), 2)

    def test_by_category(self):
        """Test filtering by category."""
        self.catalog.add_blueprint(_make_sample_blueprint("t1", "temple", "temple", 50))
        self.catalog.add_blueprint(_make_sample_blueprint("h1", "hunt", "hunting", 50))
        self.catalog.add_blueprint(
            _make_sample_blueprint("d1", "dungeon", "dungeon", 50)
        )

        dungeons = self.catalog.by_category("dungeon")
        self.assertEqual(len(dungeons), 1)

    def test_by_tag(self):
        """Test filtering by tag."""
        bp = _make_sample_blueprint("tagged", "temple", "temple", 50)
        bp.metadata.tags = ["sacred", "ancient", "large"]
        self.catalog.add_blueprint(bp)

        results = self.catalog.by_tag("sacred")
        self.assertEqual(len(results), 1)

    def test_by_difficulty(self):
        """Test filtering by difficulty."""
        bp1 = _make_sample_blueprint("easy", "city", "city", 50)
        bp1.metadata.difficulty = "easy"
        bp2 = _make_sample_blueprint("hard", "dungeon", "dungeon", 50)
        bp2.metadata.difficulty = "hard"
        self.catalog.add_blueprint(bp1)
        self.catalog.add_blueprint(bp2)

        hard = self.catalog.by_difficulty("hard")
        self.assertEqual(len(hard), 1)
        self.assertEqual(hard[0].name, "hard")

    def test_search(self):
        """Test search functionality."""
        self.catalog.add_blueprint(
            _make_sample_blueprint("temple_main", "temple", "temple", 50)
        )
        self.catalog.add_blueprint(
            _make_sample_blueprint("dungeon_boss", "dungeon", "dungeon", 50)
        )

        results = self.catalog.search("temple")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "temple_main")

    def test_by_size_range(self):
        """Test filtering by size range."""
        bp1 = _make_sample_blueprint("small", "temple", "temple", 50)
        bp1.size = (10, 10)  # area = 100
        bp2 = _make_sample_blueprint("large", "temple", "temple", 500)
        bp2.size = (50, 50)  # area = 2500
        self.catalog.add_blueprint(bp1)
        self.catalog.add_blueprint(bp2)

        small = self.catalog.by_size_range(0, 500)
        self.assertEqual(len(small), 1)
        self.assertEqual(small[0].name, "small")

        large = self.catalog.by_size_range(1000, 10000)
        self.assertEqual(len(large), 1)
        self.assertEqual(large[0].name, "large")

    def test_statistics(self):
        """Test catalog statistics."""
        self.catalog.add_blueprint(
            _make_sample_blueprint("t1", "temple", "temple", 100)
        )
        self.catalog.add_blueprint(
            _make_sample_blueprint("t2", "temple", "temple", 150)
        )
        self.catalog.add_blueprint(_make_sample_blueprint("h1", "hunt", "hunting", 80))

        stats = self.catalog.get_statistics()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_theme"]["temple"], 2)
        self.assertEqual(stats["by_theme"]["hunt"], 1)
        self.assertIn("avg_tiles", stats)
        self.assertIn("largest_blueprint", stats)

    def test_theme_statistics(self):
        """Test theme-specific statistics."""
        self.catalog.add_blueprint(
            _make_sample_blueprint("t1", "temple", "temple", 100)
        )
        self.catalog.add_blueprint(
            _make_sample_blueprint("t2", "temple", "temple", 200)
        )

        theme_stats = self.catalog.get_theme_statistics()
        self.assertIn("temple", theme_stats)
        self.assertEqual(theme_stats["temple"]["count"], 2)

    def test_quality_score(self):
        """Test setting quality score."""
        bp = _make_sample_blueprint("quality_test", "temple", "temple", 100)
        self.catalog.add_blueprint(bp)
        self.catalog.set_quality_score("quality_test", 0.95)

        # Retrieve and check
        entry = self.catalog._index["quality_test"]
        self.assertEqual(entry.quality_score, 0.95)

    def test_usage_counter(self):
        """Test usage counter increment."""
        bp = _make_sample_blueprint("usage_test", "temple", "temple", 100)
        self.catalog.add_blueprint(bp)
        self.catalog.increment_usage("usage_test")
        self.catalog.increment_usage("usage_test")

        entry = self.catalog._index["usage_test"]
        self.assertEqual(entry.usage_count, 2)

    def test_most_used(self):
        """Test getting most used blueprints."""
        bp1 = _make_sample_blueprint("popular", "temple", "temple", 100)
        bp2 = _make_sample_blueprint("unpopular", "temple", "temple", 100)
        self.catalog.add_blueprint(bp1)
        self.catalog.add_blueprint(bp2)

        self.catalog.increment_usage("popular")
        self.catalog.increment_usage("popular")
        self.catalog.increment_usage("unpopular")

        most_used = self.catalog.get_most_used(1)
        self.assertEqual(len(most_used), 1)
        self.assertEqual(most_used[0].name, "popular")

    def test_backup_restore(self):
        """Test backup and restore."""
        bp = _make_sample_blueprint("backup_test", "temple", "temple", 100)
        self.catalog.add_blueprint(bp)

        backup_dir = tempfile.mkdtemp(prefix="backup_")
        try:
            backup_path = self.catalog.backup(backup_dir)
            self.assertTrue(os.path.exists(backup_path))

            # Restore to new catalog
            new_catalog = BlueprintCatalog(catalog_dir=backup_path)
            self.assertEqual(new_catalog.count(), 1)
        finally:
            import shutil

            shutil.rmtree(backup_dir, ignore_errors=True)

    def test_export_catalog_index(self):
        """Test exporting catalog index."""
        bp = _make_sample_blueprint("export_test", "temple", "temple", 100)
        self.catalog.add_blueprint(bp)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            self.catalog.export_catalog_index(temp_path)
            with open(temp_path, "r") as f:
                data = json.load(f)
            self.assertIn("blueprints", data)
            self.assertEqual(len(data["blueprints"]), 1)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestBlueprintLearner(unittest.TestCase):
    """Tests for BlueprintLearner - main entry point."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="learner_test_")
        self.learner = BlueprintLearner(
            catalog_dir=os.path.join(self.tmp_dir, "blueprints"),
            similarity_index_path=os.path.join(self.tmp_dir, "similarity.json"),
            pattern_index_path=os.path.join(self.tmp_dir, "patterns.json"),
        )

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test learner initializes all components."""
        self.assertIsNotNone(self.learner.extractor)
        self.assertIsNotNone(self.learner.map_analyzer)
        self.assertIsNotNone(self.learner.pattern_miner)
        self.assertIsNotNone(self.learner.similarity_engine)
        self.assertIsNotNone(self.learner.ranker)
        self.assertIsNotNone(self.learner.catalog)

    def test_list_available_structures(self):
        """Test listing detectable structure types."""
        structures = self.learner.list_available_structures()
        self.assertIn("temple", structures)
        self.assertIn("depot", structures)
        self.assertIn("market", structures)
        self.assertIn("boss_room", structures)
        self.assertIn("house", structures)
        self.assertIn("bridge", structures)
        self.assertIn("camp", structures)
        self.assertGreater(len(structures), 20)

    def test_learn_from_analysis(self):
        """Test learning from MapAnalysis."""
        analysis = _make_sample_analysis("temple")
        result = self.learner.learn_from_analysis(analysis, save_blueprint=True)

        # Result may not have blueprint if extraction fails without OTBM
        # But it should not error
        self.assertIsInstance(result, LearningResult)

    def test_blueprint_to_vector(self):
        """Test blueprint to feature vector conversion."""
        bp = _make_sample_blueprint("vec_test", "temple", "temple", 100)
        vector = self.learner._blueprint_to_vector(bp)
        self.assertIsInstance(vector, list)
        self.assertEqual(
            len(vector), 20 + 30 + 3 + 15 + 13 + 2
        )  # grounds + items + struct + themes + categories + meta

    def test_pattern_guide(self):
        """Test getting pattern guide."""
        # Add some blueprints first
        bp = _make_sample_blueprint("guide_test", "temple", "temple", 100)
        self.learner.catalog.add_blueprint(bp)

        guide = self.learner.get_pattern_guide()
        # May be empty if not enough samples
        self.assertIsInstance(guide, dict)

    def test_catalog_stats(self):
        """Test getting catalog statistics."""
        stats = self.learner.get_catalog_stats()
        self.assertIn("total", stats)
        self.assertIn("by_theme", stats)


# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":
    unittest.main()
