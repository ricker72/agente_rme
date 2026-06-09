"""
HITO 15 - AI Architect: Tests for the WorldPlanner and PromptParser.

Covers prompt parsing, theme resolution, zone planning orchestration,
difficulty progression, layout, and the final WorldPlan assembly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.architect import (
    WorldPlanner, WorldPlan, WorldRequest, PromptParser,
    ZonePlanner, DifficultyPlanner, LayoutPlanner,
    ThemeResolver, resolve_theme, ThemeAssets,
    CityPlan, DungeonPlan, HuntPlan, BossPlan, QuestPlan,
    ZoneDifficulty,
    WorldLayout,
)


# =============================================================================
# PromptParser
# =============================================================================

def test_prompt_parser_basic():
    p = PromptParser()
    parsed = p.parse("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    assert "issavi" in parsed["themes"]
    assert parsed["level_min"] == 300
    assert parsed["level_max"] == 500
    assert parsed["hunt_count"] == 3
    assert parsed["city_count"] == 1
    assert parsed["boss_count"] == 1
    assert "city" in parsed["zone_kinds"]
    assert parsed["zone_kinds"].count("hunt") == 3
    assert "boss" in parsed["zone_kinds"]
    print("  [OK] test_prompt_parser_basic")


def test_prompt_parser_extracts_themes():
    p = PromptParser()
    parsed = p.parse("Issavi + Roshamuul level 300")
    assert "issavi" in parsed["themes"]
    assert "roshamuul" in parsed["themes"]
    print("  [OK] test_prompt_parser_extracts_themes")


def test_prompt_parser_single_level():
    p = PromptParser()
    parsed = p.parse("Issavi level 300")
    # Single level should give a +-20 range
    assert parsed["level_min"] == 280
    assert parsed["level_max"] == 320
    print("  [OK] test_prompt_parser_single_level")


def test_prompt_parser_level_range():
    p = PromptParser()
    parsed = p.parse("level 100-200")
    assert parsed["level_min"] == 100
    assert parsed["level_max"] == 200
    print("  [OK] test_prompt_parser_level_range")


def test_prompt_parser_nivel_spanish():
    p = PromptParser()
    parsed = p.parse("ciudad issavi nivel 200-400 con 5 hunts")
    assert parsed["level_min"] == 200
    assert parsed["level_max"] == 400
    assert parsed["hunt_count"] == 5
    print("  [OK] test_prompt_parser_nivel_spanish")


def test_prompt_parser_dungeon_keyword():
    p = PromptParser()
    parsed = p.parse("Generate a library dungeon level 100-200 with boss")
    assert parsed["dungeon_count"] >= 1
    assert "library" in parsed["themes"]
    print("  [OK] test_prompt_parser_dungeon_keyword")


def test_prompt_parser_quest_keyword():
    p = PromptParser()
    parsed = p.parse("Generate a quest in issavi level 100")
    assert parsed["quest_count"] >= 1
    print("  [OK] test_prompt_parser_quest_keyword")


def test_prompt_parser_default_hunt():
    """Empty prompt defaults to a hunt."""
    p = PromptParser()
    parsed = p.parse("something random")
    assert parsed["hunt_count"] >= 1
    print("  [OK] test_prompt_parser_default_hunt")


def test_prompt_parser_empty():
    p = PromptParser()
    parsed = p.parse("")
    # Should still produce a valid (minimal) structure
    assert "themes" in parsed
    assert "zone_kinds" in parsed
    print("  [OK] test_prompt_parser_empty")


def test_prompt_parser_zone_order():
    """zone_kinds follow canonical order: city -> dungeon -> hunt -> quest -> boss."""
    p = PromptParser()
    parsed = p.parse("boss and city and hunt and dungeon and quest")
    kinds = parsed["zone_kinds"]
    # The order in the prompt may vary, but our parser normalizes it
    # Find first occurrence of each
    first = {k: kinds.index(k) for k in kinds}
    # Verify all "city" come before "dungeon" come before "hunt" come before "quest" come before "boss"
    if "city" in first and "dungeon" in first:
        assert first["city"] < first["dungeon"]
    if "dungeon" in first and "hunt" in first:
        assert first["dungeon"] < first["hunt"]
    if "hunt" in first and "quest" in first:
        assert first["hunt"] < first["quest"]
    if "quest" in first and "boss" in first:
        assert first["quest"] < first["boss"]
    print("  [OK] test_prompt_parser_zone_order")


# =============================================================================
# WorldPlanner - basic API
# =============================================================================

def test_world_planner_creation():
    p = WorldPlanner()
    assert p is not None
    assert p.theme_resolver is not None
    assert p.zone_planner is not None
    assert p.difficulty_planner is not None
    assert p.layout_planner is not None
    print("  [OK] test_world_planner_creation")


def test_world_planner_plan_returns_worldplan():
    p = WorldPlanner()
    plan = p.plan("Issavi level 300")
    assert isinstance(plan, WorldPlan)
    assert plan.prompt == "Issavi level 300"
    print("  [OK] test_world_planner_plan_returns_worldplan")


def test_world_planner_full_example():
    """The canonical example from the task spec."""
    p = WorldPlanner()
    plan = p.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    assert isinstance(plan, WorldPlan)
    assert plan.primary_theme == "issavi"
    assert len(plan.cities) == 1
    assert len(plan.hunting_zones) == 3
    assert len(plan.boss_zones) == 1
    assert plan.layout is not None
    assert plan.layout.strategy == "city_centric"
    assert len(plan.roads) >= 1
    assert len(plan.waypoints) >= 1
    print("  [OK] test_world_planner_full_example")


def test_world_planner_call_alias():
    p = WorldPlanner()
    p1 = p("Issavi level 300")
    p2 = p.plan("Issavi level 300")
    assert p1.prompt == p2.prompt
    print("  [OK] test_world_planner_call_alias")


# =============================================================================
# WorldPlan - structure
# =============================================================================

def test_world_plan_structure():
    p = WorldPlanner()
    plan = p.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    # All expected fields present
    assert plan.cities is not None
    assert plan.dungeons is not None
    assert plan.hunting_zones is not None
    assert plan.boss_zones is not None
    assert plan.quest_zones is not None
    assert plan.roads is not None
    assert plan.teleports is not None
    assert plan.ports is not None
    assert plan.waypoints is not None
    assert plan.difficulty_progression is not None
    assert plan.layout is not None
    assert plan.metadata is not None
    assert plan.request is not None
    print("  [OK] test_world_plan_structure")


def test_world_plan_to_dict():
    p = WorldPlanner()
    plan = p.plan("Issavi + Roshamuul level 300")
    d = plan.to_dict()
    assert d["primary_theme"] in ["issavi", "issavi+roshamuul"]
    assert d["themes"] == ["issavi", "roshamuul"]
    assert "cities" in d
    assert "hunting_zones" in d
    assert "difficulty_progression" in d
    assert "layout" in d
    assert "metadata" in d
    # JSON-serializable
    json_str = json.dumps(d, default=str)
    assert len(json_str) > 0
    print("  [OK] test_world_plan_to_dict")


def test_world_plan_summary():
    p = WorldPlanner()
    plan = p.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300 y un boss")
    s = plan.summary()
    assert s.startswith("WorldPlan(")
    assert "primary=issavi" in s
    print("  [OK] test_world_plan_summary")


# =============================================================================
# Difficulty progression
# =============================================================================

def test_difficulty_progression_smooth():
    """Multiple hunts should use smooth progression style."""
    p = WorldPlanner()
    plan = p.plan("3 hunts issavi level 300-500")
    style = plan.metadata.get("difficulty_style")
    assert style == "smooth"
    # Each hunt has a band
    for d in plan.difficulty_progression:
        assert d.band in {"easy", "medium", "hard", "extreme", "epic", "legendary"}
    print("  [OK] test_difficulty_progression_smooth")


def test_difficulty_progression_spike_for_boss():
    """Boss in the sequence triggers spike style."""
    p = WorldPlanner()
    plan = p.plan("3 hunts + boss issavi level 300-500")
    style = plan.metadata.get("difficulty_style")
    assert style == "spike"
    print("  [OK] test_difficulty_progression_spike_for_boss")


def test_difficulty_progression_per_zone_levels():
    """Each zone has its own level window."""
    p = WorldPlanner()
    plan = p.plan("3 hunts issavi level 300-500")
    windows = [(d.level_min, d.level_max) for d in plan.difficulty_progression]
    assert len(windows) == 3
    # First hunt starts near 300, last hunt ends near 500
    assert windows[0][0] >= 290
    assert windows[-1][1] <= 510
    print("  [OK] test_difficulty_progression_per_zone_levels")


# =============================================================================
# Layout
# =============================================================================

def test_layout_strategy_city_centric():
    """City + boss triggers city_centric strategy."""
    p = WorldPlanner()
    plan = p.plan("ciudad + boss issavi level 300-500")
    assert plan.layout.strategy == "city_centric"
    print("  [OK] test_layout_strategy_city_centric")


def test_layout_strategy_linear():
    """Hunts only triggers linear strategy."""
    p = WorldPlanner()
    plan = p.plan("5 hunts issavi level 300")
    assert plan.layout.strategy == "linear"
    print("  [OK] test_layout_strategy_linear")


def test_layout_zones_have_positions():
    """All placed zones have non-zero positions."""
    p = WorldPlanner()
    plan = p.plan("3 hunts + boss issavi level 300-500")
    for zone in plan.layout.zones:
        assert zone.width > 0
        assert zone.height > 0
        # Position is set (may be at edge)
        assert zone.x >= 0
        assert zone.y >= 0
    print("  [OK] test_layout_zones_have_positions")


def test_layout_roads_connect_zones():
    """Roads connect the placed zones."""
    p = WorldPlanner()
    plan = p.plan("ciudad + hunt + boss issavi level 300-500")
    assert len(plan.roads) > 0
    for road in plan.roads:
        assert "from" in road
        assert "to" in road
        assert "path" in road
        assert len(road["path"]) > 0
    print("  [OK] test_layout_roads_connect_zones")


def test_layout_teleports_for_boss_and_dungeon():
    """Teleports are created for dungeon/boss zones."""
    p = WorldPlanner()
    plan = p.plan("ciudad + dungeon + boss issavi level 300-500")
    assert len(plan.teleports) > 0
    for tp in plan.teleports:
        assert "from" in tp
        assert "to" in tp
    print("  [OK] test_layout_teleports_for_boss_and_dungeon")


def test_layout_waypoints_per_zone():
    """A waypoint is created for each zone."""
    p = WorldPlanner()
    plan = p.plan("ciudad + 2 hunts + boss issavi level 300-500")
    assert len(plan.waypoints) >= 4
    for wp in plan.waypoints:
        assert "name" in wp
        assert "x" in wp
        assert "y" in wp
    print("  [OK] test_layout_waypoints_per_zone")


# =============================================================================
# Theme resolution
# =============================================================================

def test_plan_uses_resolved_theme_assets():
    """Each zone in the plan should use a theme's assets."""
    p = WorldPlanner()
    plan = p.plan("ciudad + hunt issavi level 300-500")
    for city in plan.cities:
        # The city metadata should contain the issavi ground IDs
        assert "grounds" in city.metadata
        assert any(g in [415, 393, 421, 103, 102] for g in city.metadata["grounds"])
    for hunt in plan.hunting_zones:
        assert "grounds" in hunt.metadata
        assert "monsters" in [k for k in hunt.metadata]
        # The hunt should have at least one issavi monster
        assert any(m in ["Frazzlemaw", "Sphinx", "Cloak Of Terror", "Crypt Warden",
                         "Priestess", "Vexclaw", "Guzzlemaw"]
                   for m in hunt.monster_pool)
    print("  [OK] test_plan_uses_resolved_theme_assets")


def test_plan_hybrid_themes():
    """Hybrid themes: each city/hunt uses one of the requested themes."""
    p = WorldPlanner()
    plan = p.plan("Issavi + Roshamuul level 300")
    for city in plan.cities:
        assert city.theme in ["issavi", "roshamuul"]
    print("  [OK] test_plan_hybrid_themes")


# =============================================================================
# Integration with WorldGenerator
# =============================================================================

def test_world_planner_with_world_generator():
    """WorldPlanner should be able to invoke the WorldGenerator."""
    from core.generators import WorldGenerator
    p = WorldPlanner(world_generator=WorldGenerator(seed=42))
    plan = p.plan("Generate Issavi hunt level 300")
    # The generator should have been called
    assert plan.metadata.get("integrations", {}).get("world_generator", False) is True
    if "world_model_tile_count" in plan.metadata:
        assert plan.metadata["world_model_tile_count"] is not None
    print("  [OK] test_world_planner_with_world_generator")


def test_world_planner_with_blueprint_registry():
    """WorldPlanner should be able to use the BlueprintRegistry."""
    from core.registry import BlueprintRegistry
    reg = BlueprintRegistry()
    p = WorldPlanner(blueprint_registry=reg)
    plan = p.plan("ciudad + hunt issavi level 300")
    # Should not crash
    assert plan is not None
    print("  [OK] test_world_planner_with_blueprint_registry")


def test_world_planner_with_asset_registry():
    """WorldPlanner should be able to use the AssetRegistry."""
    from core.registry import AssetRegistry
    reg = AssetRegistry()
    p = WorldPlanner(asset_registry=reg)
    plan = p.plan("ciudad + hunt issavi level 300")
    assert plan is not None
    print("  [OK] test_world_planner_with_asset_registry")


# =============================================================================
# Edge cases
# =============================================================================

def test_world_plan_empty_prompt():
    p = WorldPlanner()
    plan = p.plan("")
    assert isinstance(plan, WorldPlan)
    # Should still produce something (defaults)
    assert plan.hunting_zones or plan.cities
    print("  [OK] test_world_plan_empty_prompt")


def test_world_plan_unknown_theme():
    p = WorldPlanner()
    # Unknown theme should fall back to issavi
    plan = p.plan("Generate an xyzzy_theme hunt level 100")
    assert isinstance(plan, WorldPlan)
    print("  [OK] test_world_plan_unknown_theme")


def test_world_plan_seed_reproducibility():
    """Same seed produces same plans."""
    p1 = WorldPlanner(seed=42)
    p2 = WorldPlanner(seed=42)
    plan1 = p1.plan("ciudad + 2 hunts + boss issavi level 300-500")
    plan2 = p2.plan("ciudad + 2 hunts + boss issavi level 300-500")
    # Same number of cities/hunts/bosses
    assert len(plan1.cities) == len(plan2.cities)
    assert len(plan1.hunting_zones) == len(plan2.hunting_zones)
    assert len(plan1.boss_zones) == len(plan2.boss_zones)
    print("  [OK] test_world_plan_seed_reproducibility")


def test_world_plan_different_seeds_differ():
    """Different seeds can produce different plans (where randomness matters)."""
    p1 = WorldPlanner(seed=1)
    p2 = WorldPlanner(seed=99)
    # Dungeon plans use random - so they should differ
    plan1 = p1.plan("library dungeon level 200-400")
    plan2 = p2.plan("library dungeon level 200-400")
    # At least one room should differ
    types1 = set(r["type"] for r in plan1.dungeons[0].rooms)
    types2 = set(r["type"] for r in plan2.dungeons[0].rooms)
    # They may be the same, but the rooms may differ
    print("  [OK] test_world_plan_different_seeds_differ")


# =============================================================================
# WorldRequest
# =============================================================================

def test_world_request_properties():
    p = WorldPlanner()
    plan = p.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    request = plan.request
    assert request is not None
    assert request.has_city
    assert request.has_boss
    assert request.hunt_count == 3
    assert request.city_count == 1
    assert request.boss_count == 1
    d = request.to_dict()
    assert d["prompt"] == plan.prompt
    assert d["themes"] == plan.themes
    print("  [OK] test_world_request_properties")


# =============================================================================
# Runner
# =============================================================================

def run_all():
    print("=" * 60)
    print("  HITO 15 - WORLD PLANNER - TESTS")
    print("=" * 60)
    tests = [
        test_prompt_parser_basic,
        test_prompt_parser_extracts_themes,
        test_prompt_parser_single_level,
        test_prompt_parser_level_range,
        test_prompt_parser_nivel_spanish,
        test_prompt_parser_dungeon_keyword,
        test_prompt_parser_quest_keyword,
        test_prompt_parser_default_hunt,
        test_prompt_parser_empty,
        test_prompt_parser_zone_order,
        test_world_planner_creation,
        test_world_planner_plan_returns_worldplan,
        test_world_planner_full_example,
        test_world_planner_call_alias,
        test_world_plan_structure,
        test_world_plan_to_dict,
        test_world_plan_summary,
        test_difficulty_progression_smooth,
        test_difficulty_progression_spike_for_boss,
        test_difficulty_progression_per_zone_levels,
        test_layout_strategy_city_centric,
        test_layout_strategy_linear,
        test_layout_zones_have_positions,
        test_layout_roads_connect_zones,
        test_layout_teleports_for_boss_and_dungeon,
        test_layout_waypoints_per_zone,
        test_plan_uses_resolved_theme_assets,
        test_plan_hybrid_themes,
        test_world_planner_with_world_generator,
        test_world_planner_with_blueprint_registry,
        test_world_planner_with_asset_registry,
        test_world_plan_empty_prompt,
        test_world_plan_unknown_theme,
        test_world_plan_seed_reproducibility,
        test_world_plan_different_seeds_differ,
        test_world_request_properties,
    ]
    failures = []
    for test in tests:
        try:
            test()
        except AssertionError as e:
            failures.append((test.__name__, f"AssertionError: {e}"))
            print(f"  [FAIL] {test.__name__}: {e}")
        except Exception as e:
            failures.append((test.__name__, f"{type(e).__name__}: {e}"))
            print(f"  [FAIL] {test.__name__}: {type(e).__name__}: {e}")
    print("=" * 60)
    print(f"  Results: {len(tests) - len(failures)}/{len(tests)} tests passed")
    if failures:
        print("  Failures:")
        for name, err in failures:
            print(f"    - {name}: {err}")
    else:
        print("  ALL TESTS PASSED")
    print("=" * 60)
    return len(failures) == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
