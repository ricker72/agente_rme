"""
HITO 15 - AI Architect: Tests for the main public API.

These tests cover the AIArchitect class, the WorldPlan dataclass,
and the integration with WorldGenerator, BlueprintRegistry, and
AssetRegistry.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Make sure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.architect import (
    AIArchitect, WorldPlan, WorldRequest,
    ThemeResolver, ThemeAssets,
    ZonePlanner, CityPlan, DungeonPlan, HuntPlan, BossPlan, QuestPlan,
    DifficultyPlanner,
    LayoutPlanner, WorldLayout, PlacedZone,
    WorldPlanner,
    resolve_theme, merge_themes, ai_plan,
)


# =============================================================================
# AIArchitect - basic API
# =============================================================================

def test_ai_architect_creation():
    """Test that AIArchitect can be instantiated with no args."""
    architect = AIArchitect()
    assert architect is not None
    assert architect.theme_resolver is not None
    assert architect.zone_planner is not None
    assert architect.difficulty_planner is not None
    assert architect.layout_planner is not None
    assert architect.world_planner is not None
    print("  [OK] test_ai_architect_creation")


def test_ai_architect_plan_returns_worldplan():
    """Test that plan() returns a WorldPlan."""
    architect = AIArchitect()
    plan = architect.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    assert isinstance(plan, WorldPlan)
    assert plan.summary() is not None
    print("  [OK] test_ai_architect_plan_returns_worldplan")


def test_ai_architect_plan_full_example():
    """Test the canonical example from the task spec."""
    architect = AIArchitect()
    plan = architect.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    assert len(plan.cities) == 1
    assert len(plan.hunting_zones) == 3
    assert len(plan.boss_zones) == 1
    assert plan.primary_theme == "issavi"
    assert plan.level_min == 300
    assert plan.level_max == 500
    print("  [OK] test_ai_architect_plan_full_example")


def test_ai_architect_call_alias():
    """Test that __call__ is an alias for plan()."""
    architect = AIArchitect()
    p1 = architect("Issavi level 300")
    p2 = architect.plan("Issavi level 300")
    assert isinstance(p1, WorldPlan)
    assert isinstance(p2, WorldPlan)
    assert p1.primary_theme == p2.primary_theme
    print("  [OK] test_ai_architect_call_alias")


def test_ai_architect_analyze():
    """Test analyze() returns a WorldRequest."""
    architect = AIArchitect()
    request = architect.analyze("Issavi + Roshamuul level 300-500")
    assert isinstance(request, WorldRequest)
    assert "issavi" in request.themes
    assert "roshamuul" in request.themes
    assert request.level_min == 300
    assert request.level_max == 500
    print("  [OK] test_ai_architect_analyze")


def test_ai_architect_explain():
    """Test explain() returns a multi-line string."""
    architect = AIArchitect()
    plan = architect.plan("Issavi level 300")
    explanation = architect.explain(plan)
    assert isinstance(explanation, str)
    assert "AI ARCHITECT" in explanation
    assert "issavi" in explanation.lower()
    print("  [OK] test_ai_architect_explain")


def test_ai_architect_summary():
    """Test summary() returns a short string."""
    architect = AIArchitect()
    plan = architect.plan("Issavi level 300")
    s = architect.summary(plan)
    assert isinstance(s, str)
    assert "WorldPlan" in s
    print("  [OK] test_ai_architect_summary")


def test_ai_architect_to_dict():
    """Test to_dict() returns a serializable dict."""
    architect = AIArchitect()
    plan = architect.plan("Issavi level 300")
    d = architect.to_dict(plan)
    assert isinstance(d, dict)
    assert "cities" in d
    assert "hunting_zones" in d
    assert "boss_zones" in d
    # Ensure it can be JSON-serialized
    json_str = json.dumps(d, default=str)
    assert len(json_str) > 0
    print("  [OK] test_ai_architect_to_dict")


def test_ai_architect_list_themes():
    """Test list_known_themes() returns a non-empty list."""
    architect = AIArchitect()
    themes = architect.list_known_themes()
    assert isinstance(themes, list)
    assert len(themes) > 0
    assert "issavi" in themes
    print("  [OK] test_ai_architect_list_themes")


def test_ai_architect_resolve_theme():
    """Test resolve_theme() returns a ThemeAssets."""
    architect = AIArchitect()
    theme = architect.resolve_theme("issavi")
    assert isinstance(theme, ThemeAssets)
    assert theme.name == "issavi"
    assert len(theme.monsters) > 0
    print("  [OK] test_ai_architect_resolve_theme")


# =============================================================================
# Prompt variation tests
# =============================================================================

def test_prompt_english_city_hunt_boss():
    """Test English prompt variant."""
    a = AIArchitect()
    p = a.plan("Generate a city issavi style with 3 hunts level 300 and a final boss")
    assert len(p.cities) >= 1
    assert len(p.hunting_zones) >= 3
    assert len(p.boss_zones) >= 1
    print("  [OK] test_prompt_english_city_hunt_boss")


def test_prompt_spanish_ciudad_hunts_jefe():
    """Test Spanish prompt variant."""
    a = AIArchitect()
    p = a.plan("Crea una ciudad de Yalahar con 2 hunts nivel 200 y un jefe final")
    assert p.primary_theme == "yalahar"
    assert len(p.cities) >= 1
    assert len(p.hunting_zones) >= 2
    assert len(p.boss_zones) >= 1
    print("  [OK] test_prompt_spanish_ciudad_hunts_jefe")


def test_prompt_hybrid_themes():
    """Test hybrid theme prompt (issavi + roshamuul)."""
    a = AIArchitect()
    p = a.plan("Issavi + Roshamuul level 300")
    assert "issavi" in p.themes
    assert "roshamuul" in p.themes
    assert p.primary_theme == "issavi"
    print("  [OK] test_prompt_hybrid_themes")


def test_prompt_dungeon_focus():
    """Test dungeon-focused prompt."""
    a = AIArchitect()
    p = a.plan("Generate a library dungeon level 100-200 with boss")
    assert p.primary_theme == "library"
    assert len(p.dungeons) >= 1
    print("  [OK] test_prompt_dungeon_focus")


def test_prompt_default_hunt():
    """Test that an empty/vague prompt defaults to a hunt."""
    a = AIArchitect()
    p = a.plan("something random")
    assert len(p.hunting_zones) >= 1
    print("  [OK] test_prompt_default_hunt")


# =============================================================================
# WorldPlan - serialization
# =============================================================================

def test_worldplan_to_dict_complete():
    """Test that WorldPlan.to_dict() includes all zones."""
    a = AIArchitect()
    p = a.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300-500 y un boss final")
    d = p.to_dict()
    assert "cities" in d and len(d["cities"]) == 1
    assert "hunting_zones" in d and len(d["hunting_zones"]) == 3
    assert "boss_zones" in d and len(d["boss_zones"]) == 1
    assert "difficulty_progression" in d
    assert "layout" in d
    assert "metadata" in d
    assert d["primary_theme"] == "issavi"
    print("  [OK] test_worldplan_to_dict_complete")


def test_worldplan_summary_string():
    """Test summary() format."""
    a = AIArchitect()
    p = a.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300 y un boss")
    s = p.summary()
    assert "primary=issavi" in s
    assert "cities=1" in s
    assert "hunts=3" in s
    assert "bosses=1" in s
    print("  [OK] test_worldplan_summary_string")


# =============================================================================
# Integration with registries
# =============================================================================

def test_attach_asset_registry():
    """Test that attaching an AssetRegistry works."""
    from core.registry import AssetRegistry
    a = AIArchitect()
    reg = AssetRegistry()
    a.attach_asset_registry(reg)
    assert a.asset_registry is reg
    assert a.world_planner.asset_registry is reg
    print("  [OK] test_attach_asset_registry")


def test_attach_blueprint_registry():
    """Test that attaching a BlueprintRegistry works."""
    from core.registry import BlueprintRegistry
    a = AIArchitect()
    reg = BlueprintRegistry()
    a.attach_blueprint_registry(reg)
    assert a.blueprint_registry is reg
    assert a.world_planner.blueprint_registry is reg
    print("  [OK] test_attach_blueprint_registry")


def test_attach_world_generator():
    """Test that attaching a WorldGenerator works."""
    a = AIArchitect()
    fake_gen = object()
    a.attach_world_generator(fake_gen)
    assert a.world_generator is fake_gen
    assert a.world_planner.world_generator is fake_gen
    print("  [OK] test_attach_world_generator")


def test_plan_with_world_generator_executes():
    """Test that the plan actually invokes the world_generator if attached."""
    from core.generators import WorldGenerator
    a = AIArchitect()
    wg = WorldGenerator(seed=42)
    a.attach_world_generator(wg)
    p = a.plan("Generate Issavi hunt level 300")
    # The world generator should have been called
    assert p.metadata.get("integrations", {}).get("world_generator", False) is True
    # Tile count should be set if successful
    if "world_model_tile_count" in p.metadata:
        assert p.metadata["world_model_tile_count"] is not None
    print("  [OK] test_plan_with_world_generator_executes")


# =============================================================================
# Theme resolver integration
# =============================================================================

def test_themes_in_plan_have_correct_assets():
    """Test that resolved themes have correct grounds/walls/monsters."""
    a = AIArchitect()
    p = a.plan("Issavi + Roshamuul level 300")
    theme_issavi = a.resolve_theme("issavi")
    theme_roshamuul = a.resolve_theme("roshamuul")
    assert theme_issavi.grounds[0] in [415, 393, 421, 103, 102]
    assert theme_roshamuul.grounds[0] in [1053, 1056, 1057, 447, 231, 358]
    # Each city uses one of these themes
    for c in p.cities:
        assert c.theme in ["issavi", "roshamuul"]
    print("  [OK] test_themes_in_plan_have_correct_assets")


def test_module_level_plan_helper():
    """Test the module-level plan() helper."""
    p = ai_plan("Issavi level 200")
    assert isinstance(p, WorldPlan)
    assert p.primary_theme == "issavi"
    print("  [OK] test_module_level_plan_helper")


# =============================================================================
# Repr / str
# =============================================================================

def test_repr_does_not_crash():
    """Test that printing the plan works without errors."""
    a = AIArchitect()
    p = a.plan("Issavi + Roshamuul level 300")
    s = repr(p)
    assert isinstance(s, str)
    assert "WorldPlan" in s or "primary" in s
    print("  [OK] test_repr_does_not_crash")


# =============================================================================
# Runner
# =============================================================================

def run_all():
    """Run all tests in this file."""
    print("=" * 60)
    print("  HITO 15 - AI ARCHITECT - TESTS")
    print("=" * 60)

    tests = [
        # API basics
        test_ai_architect_creation,
        test_ai_architect_plan_returns_worldplan,
        test_ai_architect_plan_full_example,
        test_ai_architect_call_alias,
        test_ai_architect_analyze,
        test_ai_architect_explain,
        test_ai_architect_summary,
        test_ai_architect_to_dict,
        test_ai_architect_list_themes,
        test_ai_architect_resolve_theme,
        # Prompt variation
        test_prompt_english_city_hunt_boss,
        test_prompt_spanish_ciudad_hunts_jefe,
        test_prompt_hybrid_themes,
        test_prompt_dungeon_focus,
        test_prompt_default_hunt,
        # WorldPlan serialization
        test_worldplan_to_dict_complete,
        test_worldplan_summary_string,
        # Integration
        test_attach_asset_registry,
        test_attach_blueprint_registry,
        test_attach_world_generator,
        test_plan_with_world_generator_executes,
        # Theme resolver integration
        test_themes_in_plan_have_correct_assets,
        test_module_level_plan_helper,
        # Misc
        test_repr_does_not_crash,
    ]

    failures: list = []
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
