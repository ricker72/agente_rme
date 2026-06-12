"""
HITO 18 â€” Tests for :mod:`agente_rme.core.designer.autonomous_designer`.

These tests exercise the end-to-end pipeline:

    goal prompt -> DecisionEngine -> ZoneExpander -> ContentBalancer
                  -> NavigationDesigner -> WorldModel

They verify that:

* the public API ``AutonomousDesigner.generate()`` works out of the box
* all 5 sub-stages are recorded in the result metadata
* the WorldModel is internally consistent (zones, hunts, bosses, quests, connections)
* level coverage matches the requested range
* persistence (save/load) round-trips correctly
* the integration points (BlueprintRegistry etc.) are optional
* ``generate_full`` exposes intermediate artefacts
"""

from __future__ import annotations

import os
import tempfile
import unittest
from typing import List

from core.designer import (
    AutonomousDesigner,
    BalanceReport,
    DesignDecision,
    NavigationGraph,
    WorldModel,
)


class TestAutonomousDesigner(unittest.TestCase):
    """End-to-end tests for the autonomous designer."""

    # ------------------------------------------------------------------
    # Basic functionality
    # ------------------------------------------------------------------

    def test_generate_returns_world_model(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("MMORPG map level 1-1000")
        self.assertIsInstance(world, WorldModel)

    def test_generate_example_from_task_spec(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("MMORPG map level 1-1000")
        # Must produce a populated world
        self.assertGreater(len(world.zones), 0)
        self.assertGreater(world.total_hunts(), 0)
        self.assertGreater(world.total_bosses(), 0)
        self.assertGreater(world.total_quests(), 0)
        self.assertGreater(len(world.connections), 0)
        # Level coverage
        lo, hi = world.level_range()
        self.assertEqual(lo, 1)
        self.assertEqual(hi, 1000)

    def test_generate_small_world(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("small dungeon level 5-20")
        self.assertGreater(len(world.zones), 0)
        lo, hi = world.level_range()
        self.assertGreaterEqual(lo, 1)
        self.assertLessEqual(hi, 100)

    def test_generate_full_exposes_intermediates(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("fantasy level 1-200")
        self.assertIsInstance(result.decision, DesignDecision)
        self.assertIsInstance(result.balance_report, BalanceReport)
        self.assertIsInstance(result.navigation, NavigationGraph)
        self.assertIsInstance(result.world, WorldModel)
        self.assertGreater(result.duration_seconds, 0.0)
        # Stages recorded
        stage_names = {s.get("stage") for s in result.stages}
        self.assertIn("decision_engine", stage_names)
        self.assertIn("zone_expander", stage_names)
        self.assertIn("content_balancer", stage_names)
        self.assertIn("navigation_designer", stage_names)

    def test_decision_engine_used(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("ice map level 50-100")
        self.assertEqual(result.decision.goal.style, "ice")

    def test_zone_expander_used(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("map level 1-100")
        for stage in result.stages:
            if stage.get("stage") == "zone_expander":
                self.assertGreater(stage.get("zone_count", 0), 0)
                break
        else:
            self.fail("zone_expander stage missing")

    def test_navigation_designer_used(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("map level 1-100")
        for stage in result.stages:
            if stage.get("stage") == "navigation_designer":
                self.assertGreater(stage.get("connections", 0), 0)
                break
        else:
            self.fail("navigation_designer stage missing")

    def test_content_balancer_used(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("map level 1-200")
        for stage in result.stages:
            if stage.get("stage") == "content_balancer":
                self.assertIn("avg_difficulty", stage)
                self.assertIn("hunts_per_level", stage)
                break
        else:
            self.fail("content_balancer stage missing")

    # ------------------------------------------------------------------
    # World model consistency
    # ------------------------------------------------------------------

    def test_world_zones_are_well_formed(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("map level 1-50")
        for z in world.zones:
            self.assertGreater(z.area(), 0)
            self.assertGreaterEqual(z.max_level, z.min_level)
            self.assertGreater(len(z.theme.name), 0)
            self.assertGreater(len(z.name), 0)

    def test_world_connections_reference_real_zones(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("map level 1-50")
        ids = {z.zone_id for z in world.zones}
        for c in world.connections:
            self.assertIn(c.from_zone, ids)
            self.assertIn(c.to_zone, ids)

    def test_world_level_coverage(self) -> None:
        designer = AutonomousDesigner(auto_rebalance=True)
        world = designer.generate("map level 1-100")
        # After auto-rebalance, every level should be covered by at least
        # one zone. The balancer will have added rebalance hunts to plug
        # any gaps.
        coverage = set()
        for z in world.zones:
            for level in range(z.min_level, z.max_level + 1):
                coverage.add(level)
        # After rebalance, all levels in [1, 100] should be covered
        missing = set(range(1, 101)) - coverage
        self.assertEqual(
            missing,
            set(),
            f"Missing levels after rebalance: {sorted(missing)[:10]}",
        )

    def test_world_serialisation_roundtrip(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("map level 1-50")
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "world.json")
            designer.save(world, path)
            self.assertTrue(os.path.exists(path))
            loaded = designer.load(path)
            self.assertEqual(loaded.name, world.name)
            self.assertEqual(len(loaded.zones), len(world.zones))
            self.assertEqual(len(loaded.connections), len(world.connections))
            self.assertEqual(loaded.goal.min_level, world.goal.min_level)
            self.assertEqual(loaded.goal.max_level, world.goal.max_level)

    def test_world_json_roundtrip(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("map level 1-50")
        text = world.to_json()
        loaded = WorldModel.from_json(text)
        self.assertEqual(loaded.to_dict(), world.to_dict())

    def test_world_summary(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("map level 1-100")
        summary = world.summary()
        self.assertIn("zone_count", summary)
        self.assertIn("hunt_count", summary)
        self.assertIn("boss_count", summary)
        self.assertIn("quest_count", summary)
        self.assertIn("connection_count", summary)
        self.assertIn("themes", summary)
        self.assertIn("validation_issues", summary)
        self.assertEqual(summary["zone_count"], len(world.zones))
        self.assertEqual(summary["hunt_count"], world.total_hunts())

    def test_world_validate_clean(self) -> None:
        designer = AutonomousDesigner()
        world = designer.generate("map level 1-50")
        issues = world.validate()
        # We don't enforce zero issues (e.g. hunts-per-level may be flagged)
        # but every connection must reference a real zone.
        bad_refs = [i for i in issues if "references unknown zone" in i]
        self.assertEqual(bad_refs, [])

    # ------------------------------------------------------------------
    # Integrations
    # ------------------------------------------------------------------

    def test_blueprint_registry_integration(self) -> None:
        registry: List[object] = []

        class FakeRegistry:
            def register(self, bp: object) -> None:
                registry.append(bp)

        designer = AutonomousDesigner(blueprint_registry=FakeRegistry())
        world = designer.generate("map level 1-50")
        # Each zone should have produced a mini-blueprint
        self.assertEqual(len(registry), len(world.zones))
        for bp in registry:
            self.assertTrue(hasattr(bp, "name"))
            self.assertTrue(hasattr(bp, "theme"))

    def test_ai_architect_integration(self) -> None:
        class FakeArchitect:
            def plan(self, prompt: str) -> dict:
                return {"min_level": 10, "max_level": 60}

        designer = AutonomousDesigner(ai_architect=FakeArchitect())
        result = designer.generate_full("anything")
        # The architect's range was respected
        self.assertEqual(result.decision.goal.min_level, 10)
        self.assertEqual(result.decision.goal.max_level, 60)

    def test_world_generator_integration(self) -> None:
        called = {"count": 0}

        class FakeGenerator:
            def from_world_model(self, world: WorldModel) -> None:
                called["count"] += 1

        designer = AutonomousDesigner(world_generator=FakeGenerator())
        designer.generate("map level 1-30")
        self.assertEqual(called["count"], 1)

    def test_evolution_engine_integration(self) -> None:
        called = {"count": 0}

        class FakeEvolution:
            def record(self, world: WorldModel) -> None:
                called["count"] += 1

        designer = AutonomousDesigner(evolution_engine=FakeEvolution())
        designer.generate("map level 1-30")
        self.assertEqual(called["count"], 1)

    def test_no_integrations_still_works(self) -> None:
        # All integrations None
        designer = AutonomousDesigner(
            blueprint_registry=None,
            ai_architect=None,
            world_generator=None,
            evolution_engine=None,
        )
        world = designer.generate("map level 1-50")
        self.assertGreater(len(world.zones), 0)

    def test_integrations_handle_exceptions(self) -> None:
        class BrokenArchitect:
            def plan(self, prompt: str) -> dict:
                raise RuntimeError("architect is on fire")

        designer = AutonomousDesigner(ai_architect=BrokenArchitect())
        # Must not crash
        world = designer.generate("map level 1-50")
        self.assertGreater(len(world.zones), 0)
        self.assertTrue(
            any("AIArchitect failed" in w for w in world.metadata.get("warnings", []))
        )

    # ------------------------------------------------------------------
    # Theming
    # ------------------------------------------------------------------

    def test_ice_theme(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("ice map level 1-200")
        themes = [z.theme.name for z in result.world.zones]
        self.assertIn("ice", themes)

    def test_dungeon_theme(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("dungeon crawler level 1-150")
        themes = [z.theme.name for z in result.world.zones]
        self.assertTrue(
            any(
                t in ("dungeon", "cave", "crypt", "undead_city", "roshamuul")
                for t in themes
            )
        )

    def test_jungle_theme(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("jungle map level 1-100")
        themes = [z.theme.name for z in result.world.zones]
        self.assertIn("jungle", themes)

    def test_custom_size_in_prompt(self) -> None:
        designer = AutonomousDesigner()
        result = designer.generate_full("map level 1-100 size 1024x1024")
        # Size was parsed (or defaulted)
        self.assertGreater(result.decision.goal.target_size[0], 0)
        self.assertGreater(result.decision.goal.target_size[1], 0)

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_output(self) -> None:
        d1 = AutonomousDesigner()
        w1 = d1.generate("MMORPG map level 1-100")
        d2 = AutonomousDesigner()
        w2 = d2.generate("MMORPG map level 1-100")
        # Same prompt should produce the same theme sequence and zone count
        self.assertEqual(len(w1.zones), len(w2.zones))
        self.assertEqual(
            [z.theme.name for z in w1.zones],
            [z.theme.name for z in w2.zones],
        )

    def test_different_prompts_different_worlds(self) -> None:
        d = AutonomousDesigner()
        w_ice = d.generate("ice map level 1-100")
        d2 = AutonomousDesigner()
        w_fire = d2.generate("volcanic map level 1-100")
        themes_ice = sorted({z.theme.name for z in w_ice.zones})
        themes_fire = sorted({z.theme.name for z in w_fire.zones})
        # Different prompts should pick different themes in at least one zone
        self.assertNotEqual(themes_ice, themes_fire)

    # ------------------------------------------------------------------
    # Stress / smoke
    # ------------------------------------------------------------------

    def test_generate_multiple_worlds(self) -> None:
        designer = AutonomousDesigner()
        for prompt in [
            "small dungeon level 1-10",
            "medium fantasy level 1-50",
            "large mmorpg level 1-200",
            "huge epic level 1-500",
        ]:
            world = designer.generate(prompt)
            self.assertGreater(len(world.zones), 0, f"failed for: {prompt}")
            self.assertGreater(world.total_hunts(), 0, f"no hunts: {prompt}")
            issues = [i for i in world.validate() if "references unknown" in i]
            self.assertEqual(issues, [], f"bad conn: {prompt}")


if __name__ == "__main__":
    unittest.main()
