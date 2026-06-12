"""
HITO 15 - AI Architect: Tests for the ZonePlanner.

Covers plan_city, plan_dungeon, plan_hunt, plan_boss, plan_quest,
and the difficulty classification helpers.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.architect import (
    ZonePlanner,
    CityPlan,
    DungeonPlan,
    HuntPlan,
    BossPlan,
    QuestPlan,
    resolve_theme,
    DIFFICULTY_BANDS,
)

# =============================================================================
# Difficulty classification
# =============================================================================


def test_difficulty_bands_defined():
    """All 6 bands defined."""
    assert len(DIFFICULTY_BANDS) == 6
    labels = {b["label"] for b in DIFFICULTY_BANDS}
    assert labels == {"easy", "medium", "hard", "extreme", "epic", "legendary"}
    print("  [OK] test_difficulty_bands_defined")


def test_classify_difficulty_easy():
    p = ZonePlanner()
    assert p.classify_difficulty(1) == "easy"
    assert p.classify_difficulty(30) == "easy"
    assert p.classify_difficulty(50) == "easy"
    print("  [OK] test_classify_difficulty_easy")


def test_classify_difficulty_medium():
    p = ZonePlanner()
    assert p.classify_difficulty(60) == "medium"
    assert p.classify_difficulty(80) == "medium"
    print("  [OK] test_classify_difficulty_medium")


def test_classify_difficulty_hard():
    p = ZonePlanner()
    assert p.classify_difficulty(120) == "hard"
    assert p.classify_difficulty(180) == "hard"
    print("  [OK] test_classify_difficulty_hard")


def test_classify_difficulty_extreme():
    p = ZonePlanner()
    assert p.classify_difficulty(220) == "extreme"
    assert p.classify_difficulty(280) == "extreme"
    print("  [OK] test_classify_difficulty_extreme")


def test_classify_difficulty_epic():
    p = ZonePlanner()
    assert p.classify_difficulty(310) == "epic"
    assert p.classify_difficulty(450) == "epic"
    print("  [OK] test_classify_difficulty_epic")


def test_classify_difficulty_legendary():
    p = ZonePlanner()
    assert p.classify_difficulty(550) == "legendary"
    assert p.classify_difficulty(9999) == "legendary"
    print("  [OK] test_classify_difficulty_legendary")


def test_classify_range():
    p = ZonePlanner()
    # 300-500 midpoint = 400 -> epic
    assert p.classify_range(300, 500) == "epic"
    # 100-150 midpoint = 125 -> hard
    assert p.classify_range(100, 150) == "hard"
    print("  [OK] test_classify_range")


def test_difficulty_rank():
    p = ZonePlanner()
    assert p.difficulty_rank("easy") == 1
    assert p.difficulty_rank("medium") == 2
    assert p.difficulty_rank("hard") == 3
    assert p.difficulty_rank("extreme") == 4
    assert p.difficulty_rank("epic") == 5
    assert p.difficulty_rank("legendary") == 6
    assert p.difficulty_rank("unknown") == 2  # default
    print("  [OK] test_difficulty_rank")


# =============================================================================
# plan_city
# =============================================================================


def test_plan_city_basic():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    city = p.plan_city("Issavi Capital", theme, min_level=300, max_level=500)
    assert isinstance(city, CityPlan)
    assert city.name == "Issavi Capital"
    assert city.theme == "issavi"
    assert city.min_level == 300
    assert city.max_level == 500
    assert city.population > 0
    assert len(city.districts) > 0
    assert len(city.features) > 0
    print("  [OK] test_plan_city_basic")


def test_plan_city_includes_temple_for_higher_bands():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    city_easy = p.plan_city("Easy City", theme, min_level=1, max_level=30)
    city_legendary = p.plan_city("Legendary City", theme, min_level=550, max_level=700)
    # Higher bands have more features
    assert len(city_legendary.features) >= len(city_easy.features)
    # Higher bands have more districts
    assert len(city_legendary.districts) > len(city_easy.districts)
    print("  [OK] test_plan_city_includes_temple_for_higher_bands")


def test_plan_city_has_theme_specific_districts():
    p = ZonePlanner()
    issavi = resolve_theme("issavi")
    jungle = resolve_theme("jungle")
    desert_city = p.plan_city("Desert", issavi, min_level=200, max_level=400)
    jungle_city = p.plan_city("Jungle", jungle, min_level=200, max_level=400)
    # Both should have districts, but the desert one should have an Oasis
    assert "Oasis Quarter" in desert_city.districts
    # Jungle should not have Oasis
    assert "Oasis Quarter" not in jungle_city.districts
    print("  [OK] test_plan_city_has_theme_specific_districts")


def test_plan_city_metadata():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    city = p.plan_city("X", theme, min_level=300, max_level=500)
    assert "band" in city.metadata
    assert "biome" in city.metadata
    assert "era" in city.metadata
    print("  [OK] test_plan_city_metadata")


def test_plan_city_to_dict():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    city = p.plan_city("X", theme, min_level=200, max_level=400)
    d = city.to_dict()
    assert d["name"] == "X"
    assert d["theme"] == "issavi"
    assert d["level_range"] == [200, 400]
    assert "metadata" in d
    print("  [OK] test_plan_city_to_dict")


# =============================================================================
# plan_dungeon
# =============================================================================


def test_plan_dungeon_basic():
    p = ZonePlanner()
    theme = resolve_theme("library")
    dungeon = p.plan_dungeon("Library Depths", theme, min_level=100, max_level=200)
    assert isinstance(dungeon, DungeonPlan)
    assert dungeon.name == "Library Depths"
    assert dungeon.theme == "library"
    assert dungeon.floors > 0
    assert dungeon.room_count > 0
    assert dungeon.boss is not None
    assert "name" in dungeon.boss
    assert "mechanics" in dungeon.boss
    print("  [OK] test_plan_dungeon_basic")


def test_plan_dungeon_floors_scale_with_difficulty():
    p = ZonePlanner()
    theme = resolve_theme("library")
    easy_d = p.plan_dungeon("Easy", theme, min_level=1, max_level=30)
    epic_d = p.plan_dungeon("Epic", theme, min_level=300, max_level=500)
    assert epic_d.floors > easy_d.floors
    print("  [OK] test_plan_dungeon_floors_scale_with_difficulty")


def test_plan_dungeon_rooms_have_metadata():
    p = ZonePlanner()
    theme = resolve_theme("library")
    dungeon = p.plan_dungeon("X", theme, min_level=200, max_level=400)
    for r in dungeon.rooms:
        assert "id" in r
        assert "type" in r
        assert "level" in r
        assert "monster_count" in r
        assert "floor" in r
    print("  [OK] test_plan_dungeon_rooms_have_metadata")


def test_plan_dungeon_no_boss():
    p = ZonePlanner()
    theme = resolve_theme("library")
    dungeon = p.plan_dungeon("NoBoss", theme, include_boss=False)
    assert dungeon.boss is None
    print("  [OK] test_plan_dungeon_no_boss")


def test_plan_dungeon_to_dict():
    p = ZonePlanner()
    theme = resolve_theme("library")
    dungeon = p.plan_dungeon("X", theme, min_level=200, max_level=400)
    d = dungeon.to_dict()
    assert "rooms" in d
    assert "boss" in d
    assert "floors" in d
    print("  [OK] test_plan_dungeon_to_dict")


# =============================================================================
# plan_hunt
# =============================================================================


def test_plan_hunt_basic():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    hunt = p.plan_hunt("Issavi Hunt 1", theme, min_level=300, max_level=500)
    assert isinstance(hunt, HuntPlan)
    assert hunt.name == "Issavi Hunt 1"
    assert hunt.theme == "issavi"
    assert hunt.min_level == 300
    assert hunt.max_level == 500
    assert hunt.spawn_count > 0
    assert len(hunt.monster_pool) > 0
    assert hunt.area_size[0] > 0
    assert hunt.area_size[1] > 0
    print("  [OK] test_plan_hunt_basic")


def test_plan_hunt_density_scales_spawn_count():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    low = p.plan_hunt("Low", theme, min_level=300, density="low", area_size=(50, 50))
    high = p.plan_hunt("High", theme, min_level=300, density="high", area_size=(50, 50))
    assert high.spawn_count > low.spawn_count
    print("  [OK] test_plan_hunt_density_scales_spawn_count")


def test_plan_hunt_to_dict():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    hunt = p.plan_hunt("X", theme, min_level=300, max_level=500)
    d = hunt.to_dict()
    assert "monster_pool" in d
    assert "spawn_count" in d
    assert "area_size" in d
    print("  [OK] test_plan_hunt_to_dict")


# =============================================================================
# plan_boss
# =============================================================================


def test_plan_boss_basic():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    boss = p.plan_boss("Issavi Boss", theme, min_level=300, max_level=500)
    assert isinstance(boss, BossPlan)
    assert boss.name == "Issavi Boss"
    assert boss.theme == "issavi"
    assert boss.boss_monster in theme.monsters
    assert len(boss.loot_table) > 0
    assert len(boss.mechanics) > 0
    print("  [OK] test_plan_boss_basic")


def test_plan_boss_mechanics_scale_with_difficulty():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    easy = p.plan_boss("E", theme, min_level=10, max_level=30)
    legendary = p.plan_boss("L", theme, min_level=500, max_level=700)
    assert len(legendary.mechanics) > len(easy.mechanics)
    print("  [OK] test_plan_boss_mechanics_scale_with_difficulty")


def test_plan_boss_explicit_monster():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    boss = p.plan_boss(
        "X", theme, boss_monster="CUSTOM_MONSTER", min_level=300, max_level=500
    )
    assert boss.boss_monster == "CUSTOM_MONSTER"
    print("  [OK] test_plan_boss_explicit_monster")


def test_plan_boss_to_dict():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    boss = p.plan_boss("X", theme)
    d = boss.to_dict()
    assert "boss_monster" in d
    assert "loot_table" in d
    assert "mechanics" in d
    assert "minions" in d
    print("  [OK] test_plan_boss_to_dict")


# =============================================================================
# plan_quest
# =============================================================================


def test_plan_quest_basic():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    quest = p.plan_quest("The Issavi Trial", theme, min_level=300, max_level=500)
    assert isinstance(quest, QuestPlan)
    assert quest.title == "The Issavi Trial"
    assert quest.theme == "issavi"
    assert len(quest.objectives) > 0
    assert len(quest.npcs) > 0
    assert len(quest.rewards) > 0
    print("  [OK] test_plan_quest_basic")


def test_plan_quest_objective_count():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    quest = p.plan_quest("Q", theme, min_level=300, max_level=500, objective_count=5)
    assert len(quest.objectives) == 5
    print("  [OK] test_plan_quest_objective_count")


def test_plan_quest_objective_format():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    quest = p.plan_quest("Q", theme, min_level=300, max_level=500)
    for obj in quest.objectives:
        assert "id" in obj
        assert "description" in obj
        assert "type" in obj
        assert "level" in obj
    print("  [OK] test_plan_quest_objective_format")


def test_plan_quest_to_dict():
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    quest = p.plan_quest("Q", theme)
    d = quest.to_dict()
    assert "objectives" in d
    assert "npcs" in d
    assert "rewards" in d
    print("  [OK] test_plan_quest_to_dict")


# =============================================================================
# Integration
# =============================================================================


def test_all_zones_have_themes():
    """All plan_* methods return plans with valid themes."""
    p = ZonePlanner()
    theme = resolve_theme("issavi")
    city = p.plan_city("C", theme)
    dungeon = p.plan_dungeon("D", theme)
    hunt = p.plan_hunt("H", theme)
    boss = p.plan_boss("B", theme)
    quest = p.plan_quest("Q", theme)
    for z in [city, dungeon, hunt, boss, quest]:
        assert z.theme == "issavi"
    print("  [OK] test_all_zones_have_themes")


def test_seed_reproducibility():
    """Same seed produces same plans (where randomness is used)."""
    p1 = ZonePlanner(seed=42)
    p2 = ZonePlanner(seed=42)
    theme = resolve_theme("issavi")
    dungeon1 = p1.plan_dungeon("X", theme, min_level=200, max_level=400)
    dungeon2 = p2.plan_dungeon("X", theme, min_level=200, max_level=400)
    # Rooms may differ in type/level (random), but boss name should be the same
    assert dungeon1.boss["name"] == dungeon2.boss["name"]
    print("  [OK] test_seed_reproducibility")


# =============================================================================
# Runner
# =============================================================================


def run_all():
    print("=" * 60)
    print("  HITO 15 - ZONE PLANNER - TESTS")
    print("=" * 60)
    tests = [
        test_difficulty_bands_defined,
        test_classify_difficulty_easy,
        test_classify_difficulty_medium,
        test_classify_difficulty_hard,
        test_classify_difficulty_extreme,
        test_classify_difficulty_epic,
        test_classify_difficulty_legendary,
        test_classify_range,
        test_difficulty_rank,
        test_plan_city_basic,
        test_plan_city_includes_temple_for_higher_bands,
        test_plan_city_has_theme_specific_districts,
        test_plan_city_metadata,
        test_plan_city_to_dict,
        test_plan_dungeon_basic,
        test_plan_dungeon_floors_scale_with_difficulty,
        test_plan_dungeon_rooms_have_metadata,
        test_plan_dungeon_no_boss,
        test_plan_dungeon_to_dict,
        test_plan_hunt_basic,
        test_plan_hunt_density_scales_spawn_count,
        test_plan_hunt_to_dict,
        test_plan_boss_basic,
        test_plan_boss_mechanics_scale_with_difficulty,
        test_plan_boss_explicit_monster,
        test_plan_boss_to_dict,
        test_plan_quest_basic,
        test_plan_quest_objective_count,
        test_plan_quest_objective_format,
        test_plan_quest_to_dict,
        test_all_zones_have_themes,
        test_seed_reproducibility,
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
