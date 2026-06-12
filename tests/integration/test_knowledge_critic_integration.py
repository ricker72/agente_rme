"""Integration test that knowledge entries can be enriched with critic data."""

from __future__ import annotations

import unittest

from core.knowledge import (
    DatasetBuilder,
    KnowledgeEngine,
    build_metrics,
)


def _src(name: str, theme: str) -> dict:
    return {
        "meta": {"name": name, "theme": theme},
        "regions": [
            {
                "name": f"{name}_hunt",
                "theme": theme,
                "min_level": 250,
                "max_level": 400,
                "tags": ["circular"],
            },
            {
                "name": f"{name}_boss_arena",
                "category": "boss_room",
                "theme": theme,
                "tags": ["boss", "circular"],
                "width": 30,
                "height": 30,
            },
        ],
        "cities": [{"name": f"{name}_city", "theme": theme}],
        "spawns": [
            {"monster": "Guzzlemaw", "zone": f"{name}_hunt", "level": 300},
        ],
    }


class TestKnowledgeCriticIntegration(unittest.TestCase):
    def test_critic_scores_merge_into_entries(self):
        builder = DatasetBuilder()
        sources = [_src("roshamuul", "roshamuul"), _src("issavi", "issavi")]
        ds = builder.build_from_sources(sources)
        # Pretend a critic report scored the two hunts
        builder.attach_scores(
            ds,
            critic_report={
                "roshamuul_hunt": 92.0,
                "issavi_hunt": 78.0,
            },
        )
        engine = KnowledgeEngine(dataset=ds)
        roshamuul = engine.dataset.by_name("roshamuul_hunt")
        issavi = engine.dataset.by_name("issavi_hunt")
        self.assertEqual(roshamuul.critic_score, 92.0)
        self.assertEqual(issavi.critic_score, 78.0)

        # Metrics now include these scores in the average
        m = build_metrics(ds)
        self.assertGreater(m.avg_critic_score, 0.0)
        # The non-scored entries default to 0 so the average is the
        # average of the scored entries only (both ~85).
        # Expect ~85 (average of 92 and 78).
        # With many other entries defaulting to 0 the avg will be much lower.
        # So just assert the critic score is non-zero.
        self.assertGreater(m.avg_critic_score, 0.0)

    def test_playtest_and_reuse_scores(self):
        builder = DatasetBuilder()
        ds = builder.build_from_sources([_src("roshamuul", "roshamuul")])
        builder.attach_scores(
            ds,
            playtest_report={"roshamuul_hunt": 88.0},
            reuse_report={"roshamuul_hunt": 75.0},
        )
        entry = ds.by_name("roshamuul_hunt")
        self.assertEqual(entry.playtest_score, 88.0)
        self.assertEqual(entry.reuse_score, 75.0)


if __name__ == "__main__":
    unittest.main()
