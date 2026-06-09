"""Integration test for the full Knowledge pipeline (build -> query -> metrics)."""

from __future__ import annotations

import os
import tempfile
import unittest

from core.knowledge import (
    DatasetBuilder,
    EntryType,
    KnowledgeCatalog,
    KnowledgeEngine,
    KnowledgeMetrics,
    KnowledgeReport,
    build_metrics,
)


def _src(name: str, theme: str = "roshamuul", with_hunt: bool = True,
        with_city: bool = True) -> dict:
    src = {
        "meta": {"name": name, "theme": theme},
        "cities": [],
        "regions": [],
        "structures": [],
        "spawns": [],
        "waypoints": [],
        "quests": [],
    }
    if with_hunt:
        src["regions"].append({
            "name": f"{name}_hunt", "theme": theme,
            "min_level": 250, "max_level": 400, "tags": ["circular"],
        })
        src["spawns"].append({
            "monster": "Guzzlemaw", "zone": f"{name}_hunt", "level": 300,
        })
    if with_city:
        src["cities"].append({
            "name": f"{name} City", "theme": theme,
            "min_level": 200, "max_level": 500,
        })
    return src


class TestKnowledgePipeline(unittest.TestCase):
    def test_build_query_metrics(self):
        """Run the full pipeline on a set of synthetic sources."""
        sources = [
            _src("roshamuul", with_hunt=True, with_city=True),
            _src("issavi", theme="issavi"),
            _src("soul_war", with_hunt=True),
            _src("ferumbras_raid", theme="ferumbras", with_hunt=False,
                  with_city=False),
        ]
        # Add a raid
        sources[-1]["raids"] = [{
            "name": "Ferumbras Raid", "min_level": 300, "max_level": 9999,
        }]

        builder = DatasetBuilder()
        ds = builder.build_from_sources(sources)
        stats = builder.last_stats
        self.assertGreaterEqual(stats.entries_added, 4)
        self.assertEqual(stats.sources_processed, 4)

        engine = KnowledgeEngine(dataset=ds)
        # Find similar hunts
        roshamuul_hunt = engine.dataset.by_name("roshamuul_hunt")
        self.assertIsNotNone(roshamuul_hunt)
        results = engine.find_similar_hunts("roshamuul_hunt", k=3)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]["name"], "roshamuul_hunt")
        self.assertEqual(results[0]["match_type"], "exact")

        # Text queries
        for q, expected_type in [
            ("circular hunt", EntryType.HUNT),
            ("city", EntryType.CITY),
        ]:
            r = engine.query_text(q, k=5)
            self.assertGreater(r.total, 0)
            types = {m.entry.entry_type for m in r.matches}
            self.assertIn(expected_type, types)
        # The "raid" text query returns a raid entry
        raid_r = engine.query_text("raid", k=5)
        self.assertGreater(raid_r.total, 0)
        self.assertIn(EntryType.RAID,
                      {m.entry.entry_type for m in raid_r.matches})

        # Metrics
        metrics = build_metrics(ds)
        self.assertGreater(metrics.total_entries, 0)
        self.assertGreater(metrics.coverage_pct, 0.0)

        # Catalog
        cat = KnowledgeCatalog.build(ds, top_n=3)
        self.assertGreater(cat.total_entries, 0)

        # Report
        report = KnowledgeReport.build(ds, metrics, cat)
        md = report.to_markdown()
        self.assertIn("OpenTibia Knowledge Dataset Report", md)
        self.assertIn("Top cities", md)

        # Save and reload
        with tempfile.TemporaryDirectory() as d:
            dataset_path = os.path.join(d, "kds.json")
            engine.save(dataset_path)
            self.assertTrue(os.path.exists(dataset_path))
            reloaded = KnowledgeEngine.load(dataset_path)
            self.assertEqual(reloaded.dataset.total(), ds.total())
            # And the metrics file
            metrics_path = os.path.join(d, "metrics.json")
            metrics.write(metrics_path)
            self.assertTrue(os.path.exists(metrics_path))
            # Re-validate the dataset can be used for a new query
            results2 = reloaded.find_similar_hunts("roshamuul_hunt", k=2)
            self.assertGreater(len(results2), 0)

    def test_extend_dataset(self):
        """Building multiple times extends the dataset instead of replacing it."""
        builder = DatasetBuilder()
        ds1 = builder.build_from_sources([_src("roshamuul")])
        before = ds1.total()
        ds2 = builder.build_from_sources([_src("issavi", theme="issavi")], dataset=ds1)
        self.assertGreater(ds2.total(), before)

    def test_attach_scores(self):
        builder = DatasetBuilder()
        ds = builder.build_from_sources([_src("roshamuul")])
        builder.attach_scores(
            ds,
            critic_report={"roshamuul_hunt": 92.0},
            playtest_report={"roshamuul_hunt": 88.0},
        )
        roshamuul = ds.by_name("roshamuul_hunt")
        self.assertEqual(roshamuul.critic_score, 92.0)
        self.assertEqual(roshamuul.playtest_score, 88.0)


if __name__ == "__main__":
    unittest.main()
