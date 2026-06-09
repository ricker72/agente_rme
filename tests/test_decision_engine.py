"""
HITO 18 — Tests for :mod:`agente_rme.core.designer.decision_engine`.

Covers prompt parsing, level range detection, style detection, theme
sequence generation, count estimation and the registry-bias path.
"""

from __future__ import annotations

import re
import unittest
from typing import List

from agente_rme.core.designer import (
    DecisionEngine,
    DesignDecision,
    DesignGoal,
    THEME_CATALOG,
    STYLE_THEME_SEQUENCES,
    difficulty_for_level,
    layout_for_zone_count,
)


class TestDecisionEnginePromptParsing(unittest.TestCase):
    """Test the parsing of free-form prompts into :class:`DesignGoal`."""

    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_default_goal(self) -> None:
        goal = self.engine.parse_goal("")
        self.assertIsInstance(goal, DesignGoal)
        self.assertEqual(goal.min_level, 1)
        self.assertEqual(goal.max_level, 100)

    def test_level_range_dash(self) -> None:
        goal = self.engine.parse_goal("map level 1-1000")
        self.assertEqual(goal.min_level, 1)
        self.assertEqual(goal.max_level, 1000)

    def test_level_range_to(self) -> None:
        goal = self.engine.parse_goal("dungeon level 10 to 80")
        self.assertEqual(goal.min_level, 10)
        self.assertEqual(goal.max_level, 80)

    def test_level_range_en_dash(self) -> None:
        goal = self.engine.parse_goal("levels 50–200")
        self.assertEqual(goal.min_level, 50)
        self.assertEqual(goal.max_level, 200)

    def test_size_in_prompt(self) -> None:
        goal = self.engine.parse_goal("map 512x512 level 1-50")
        self.assertEqual(goal.target_size, (512, 512))

    def test_size_with_x_mark(self) -> None:
        goal = self.engine.parse_goal("map 256×256 level 1-50")
        self.assertEqual(goal.target_size, (256, 256))

    def test_default_size_heuristic(self) -> None:
        goal = self.engine.parse_goal("map level 1-50")
        # No size in prompt -> heuristic
        w, h = goal.target_size
        self.assertGreaterEqual(w, 128)
        self.assertLessEqual(w, 1024)
        self.assertEqual(w, h)

    # ------------------------------------------------------------------
    # Style detection
    # ------------------------------------------------------------------

    def test_style_ice(self) -> None:
        self.assertEqual(self.engine.parse_goal("frozen map").style, "ice")
        self.assertEqual(self.engine.parse_goal("winter wonderland").style, "ice")
        self.assertEqual(self.engine.parse_goal("snow dungeon").style, "ice")

    def test_style_jungle(self) -> None:
        self.assertEqual(self.engine.parse_goal("jungle temple").style, "jungle")
        self.assertEqual(self.engine.parse_goal("tropical island").style, "jungle")

    def test_style_dungeon(self) -> None:
        self.assertEqual(self.engine.parse_goal("dungeon crawler").style, "dungeon")
        self.assertEqual(self.engine.parse_goal("undead crypt").style, "dungeon")

    def test_style_city(self) -> None:
        self.assertEqual(self.engine.parse_goal("city map").style, "city")
        self.assertEqual(self.engine.parse_goal("urban sprawl").style, "city")

    def test_style_volcanic(self) -> None:
        self.assertEqual(self.engine.parse_goal("volcanic lair").style, "volcanic")
        self.assertEqual(self.engine.parse_goal("lava dungeon").style, "volcanic")

    def test_style_desert(self) -> None:
        self.assertEqual(self.engine.parse_goal("desert tomb").style, "desert")

    def test_style_fantasy(self) -> None:
        self.assertEqual(self.engine.parse_goal("fantasy kingdom").style, "fantasy")

    def test_style_mmorpg_default(self) -> None:
        # No specific style keywords -> "mixed"
        self.assertEqual(
            self.engine.parse_goal("MMORPG map level 1-1000").style, "mixed"
        )

    def test_unknown_style_falls_back_to_mixed(self) -> None:
        self.assertEqual(self.engine.parse_goal("random gibberish level 1-50").style, "mixed")

    # ------------------------------------------------------------------
    # Difficulty curve
    # ------------------------------------------------------------------

    def test_difficulty_curve_default_linear(self) -> None:
        goal = self.engine.parse_goal("map level 1-100")
        self.assertEqual(goal.difficulty_curve, "linear")

    def test_difficulty_curve_exponential(self) -> None:
        goal = self.engine.parse_goal("hardcore exponential map")
        self.assertEqual(goal.difficulty_curve, "exponential")

    def test_difficulty_curve_stepped(self) -> None:
        goal = self.engine.parse_goal("stepped tier map")
        self.assertEqual(goal.difficulty_curve, "stepped")


class TestDecisionEngineZoneCount(unittest.TestCase):
    """Test that zone count scales with the level range."""

    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_small_range(self) -> None:
        decision = self.engine.decide("map level 1-10")
        self.assertGreaterEqual(len(decision.zone_targets), 4)

    def test_medium_range(self) -> None:
        decision = self.engine.decide("map level 1-100")
        self.assertGreaterEqual(len(decision.zone_targets), 6)

    def test_large_range(self) -> None:
        decision = self.engine.decide("map level 1-500")
        self.assertGreaterEqual(len(decision.zone_targets), 8)

    def test_huge_range(self) -> None:
        decision = self.engine.decide("MMORPG map level 1-1000")
        self.assertGreaterEqual(len(decision.zone_targets), 10)


class TestDecisionEngineThemeSequence(unittest.TestCase):
    """Test that theme sequences are sensible."""

    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_themes_are_known(self) -> None:
        decision = self.engine.decide("map level 1-500")
        for theme in decision.theme_sequence:
            self.assertIn(theme, THEME_CATALOG)

    def test_themes_have_progression(self) -> None:
        decision = self.engine.decide("fantasy level 1-300")
        # First theme should be easy
        self.assertIn(decision.theme_sequence[0], ("grassland", "forest", "city"))
        # Last theme should be hard
        self.assertEqual(decision.theme_sequence[-1], "roshamuul")

    def test_zone_targets_cover_full_range(self) -> None:
        decision = self.engine.decide("map level 1-200")
        # First zone's min_level <= goal.min_level
        # Last zone's max_level == goal.max_level
        self.assertEqual(decision.zone_targets[0]["min_level"], 1)
        self.assertEqual(decision.zone_targets[-1]["max_level"], 200)

    def test_zone_targets_no_overlap_gaps(self) -> None:
        decision = self.engine.decide("map level 1-100")
        # Adjacent zones should connect (next min == prev max + 1)
        for a, b in zip(decision.zone_targets, decision.zone_targets[1:]):
            self.assertLessEqual(a["max_level"], b["min_level"])
            self.assertLessEqual(b["min_level"], a["max_level"] + 1)

    def test_world_layout_selected(self) -> None:
        decision_small = self.engine.decide("tiny map level 1-5")
        decision_huge = self.engine.decide("huge map level 1-2000")
        self.assertIn(decision_small.world_layout, ("linear", "organic", "radial", "grid"))
        self.assertIn(decision_huge.world_layout, ("linear", "organic", "radial", "grid"))


class TestDecisionEngineCounts(unittest.TestCase):
    """Test hunt / boss / quest budget calculation."""

    def setUp(self) -> None:
        self.engine = DecisionEngine()

    def test_hunt_count_scales_with_level(self) -> None:
        d_small = self.engine.decide("map level 1-20")
        d_large = self.engine.decide("map level 1-500")
        self.assertGreater(d_large.target_hunt_count, d_small.target_hunt_count)

    def test_boss_count_scales_with_level(self) -> None:
        d_small = self.engine.decide("map level 1-20")
        d_large = self.engine.decide("map level 1-500")
        self.assertGreater(d_large.target_boss_count, d_small.target_boss_count)

    def test_quest_count_scales_with_level(self) -> None:
        d_small = self.engine.decide("map level 1-20")
        d_large = self.engine.decide("map level 1-500")
        self.assertGreater(d_large.target_quest_count, d_small.target_quest_count)

    def test_counts_at_least_zone_count(self) -> None:
        decision = self.engine.decide("map level 1-100")
        self.assertGreaterEqual(decision.target_hunt_count, len(decision.zone_targets))


class TestDecisionEngineRegistryBias(unittest.TestCase):
    """Test that an existing BlueprintRegistry can bias theme choices."""

    def test_registry_bias_keeps_known_themes(self) -> None:
        class FakeBP:
            def __init__(self, name: str, theme: str) -> None:
                self.name = name
                self.theme = theme

        class FakeRegistry:
            def __init__(self) -> None:
                self._items = {
                    "a": FakeBP("a", "ice"),
                    "b": FakeBP("b", "ice"),
                    "c": FakeBP("c", "temple"),
                }

            def list_all(self) -> List[str]:
                return list(self._keys())

            def _keys(self) -> List[str]:
                return list(self._items.keys())

            def get(self, name: str):
                return self._items.get(name)

        engine = DecisionEngine(blueprint_registry=FakeRegistry())
        decision = engine.decide("map level 1-200")
        # Both "ice" and "temple" are in the registry and in THEME_CATALOG
        self.assertTrue(
            any(t in ("ice", "temple") for t in decision.theme_sequence)
        )

    def test_no_registry_uses_defaults(self) -> None:
        engine = DecisionEngine(blueprint_registry=None)
        decision = engine.decide("map level 1-100")
        self.assertGreater(len(decision.theme_sequence), 0)

    def test_empty_registry_uses_defaults(self) -> None:
        class EmptyRegistry:
            def list_all(self) -> List[str]:
                return []

            def get(self, name: str):
                return None

        engine = DecisionEngine(blueprint_registry=EmptyRegistry())
        decision = engine.decide("map level 1-100")
        self.assertGreater(len(decision.theme_sequence), 0)


class TestDecisionEngineHelpers(unittest.TestCase):
    """Test the module-level helpers."""

    def test_difficulty_for_level(self) -> None:
        self.assertEqual(difficulty_for_level(1), "safe")
        self.assertEqual(difficulty_for_level(5), "safe")
        self.assertEqual(difficulty_for_level(10), "easy")
        self.assertEqual(difficulty_for_level(40), "normal")
        self.assertEqual(difficulty_for_level(80), "hard")
        self.assertEqual(difficulty_for_level(150), "dangerous")
        self.assertEqual(difficulty_for_level(500), "deadly")
        self.assertEqual(difficulty_for_level(99999), "deadly")

    def test_layout_for_zone_count(self) -> None:
        self.assertEqual(layout_for_zone_count(1), "linear")
        self.assertEqual(layout_for_zone_count(50), "linear")
        self.assertEqual(layout_for_zone_count(60), "organic")
        self.assertEqual(layout_for_zone_count(500), "radial")
        self.assertEqual(layout_for_zone_count(1000), "grid")

    def test_world_name_from_prompt(self) -> None:
        engine = DecisionEngine()
        decision = engine.decide("My Cool Dungeon level 1-100")
        # The name should include something from the prompt
        self.assertIn("My_Cool_Dungeon", decision.world_name)

    def test_world_name_fallback(self) -> None:
        engine = DecisionEngine()
        # Empty/whitespace-only prompt -> fallback to autoworld
        decision = engine.decide("")
        self.assertTrue(decision.world_name.startswith("autoworld_"))
        # Some text remains -> no fallback needed, but name must not be empty
        decision2 = engine.decide("@!# level 1-10")
        self.assertGreater(len(decision2.world_name), 0)
        self.assertIn("level", decision2.world_name)


class TestDesignDecisionSerialization(unittest.TestCase):
    """Test that DesignDecision can be (de)serialised."""

    def test_to_dict(self) -> None:
        engine = DecisionEngine()
        decision = engine.decide("map level 1-100")
        data = decision.to_dict()
        self.assertIn("world_name", data)
        self.assertIn("world_layout", data)
        self.assertIn("theme_sequence", data)
        self.assertIn("zone_targets", data)
        self.assertIn("target_hunt_count", data)
        self.assertIn("target_boss_count", data)
        self.assertIn("target_quest_count", data)


if __name__ == "__main__":
    unittest.main()
