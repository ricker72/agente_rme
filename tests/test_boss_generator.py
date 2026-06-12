"""
Tests for BossGenerator — validates boss encounter generation.

Covers: boss generation, boss types, abilities, loot, HP/damage estimates,
lair location, objectives, and QuestPackage validation.
"""

import pytest

from core.content.quest_package import QuestPackage, RoomType
from core.content.map_designer import MapDesigner
from core.content.boss_generator import BossGenerator


class FakeAssetRegistry:
    """Minimal asset registry stub for testing."""

    def __init__(self):
        self._loaded = True

    def is_loaded(self):
        return self._loaded


class FakeWorldModel:
    """Minimal world model stub for testing."""

    def __init__(self):
        self.tiles = {}
        self.structures = []
        self.regions = []


class TestBossGenerator:
    """Test the BossGenerator."""

    @pytest.fixture
    def deps(self):
        """Create shared dependencies."""
        registry = FakeAssetRegistry()
        world = FakeWorldModel()
        designer = MapDesigner(world_model=world, asset_registry=registry)
        return registry, designer, world

    @pytest.fixture
    def generator(self, deps):
        """Create a BossGenerator with fake deps."""
        registry, designer, world = deps
        return BossGenerator(registry, designer, world)

    # ------------------------------------------------------------------
    # Basic generation
    # ------------------------------------------------------------------

    def test_generate_returns_quest_package(self, generator):
        """generate() should return a QuestPackage instance."""
        pkg = generator.generate(level_range=(300, 500))
        assert isinstance(pkg, QuestPackage)

    def test_generate_level_range(self, generator):
        """Generated package should respect level range."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.level_min == 100
        assert pkg.level_max == 200

    def test_boss_has_boss_lair_room_type(self, generator):
        """Boss encounter should use BOSS_LAIR room type."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.room_type == RoomType.BOSS_LAIR

    def test_boss_has_boss_name(self, generator):
        """Boss encounter should have a boss name."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.boss_name is not None
        assert len(pkg.boss_name) > 0

    def test_boss_has_abilities_in_metadata(self, generator):
        """Boss metadata should contain abilities list."""
        pkg = generator.generate(level_range=(100, 200))
        assert "abilities" in pkg.metadata
        assert isinstance(pkg.metadata["abilities"], list)
        assert len(pkg.metadata["abilities"]) > 0

    def test_boss_has_hp_estimate(self, generator):
        """Boss metadata should contain boss_hp."""
        pkg = generator.generate(level_range=(100, 200))
        assert "boss_hp" in pkg.metadata
        assert pkg.metadata["boss_hp"] > 0

    def test_boss_has_damage_estimate(self, generator):
        """Boss metadata should contain boss_damage."""
        pkg = generator.generate(level_range=(100, 200))
        assert "boss_damage" in pkg.metadata
        assert pkg.metadata["boss_damage"] > 0

    def test_boss_hp_scales_with_level(self, generator):
        """Boss HP should increase with level."""
        low = generator.generate(level_range=(10, 20))
        high = generator.generate(level_range=(400, 500))
        assert high.metadata["boss_hp"] > low.metadata["boss_hp"]

    def test_boss_damage_scales_with_level(self, generator):
        """Boss damage should increase with level."""
        low = generator.generate(level_range=(10, 20))
        high = generator.generate(level_range=(400, 500))
        assert high.metadata["boss_damage"] > low.metadata["boss_damage"]

    def test_no_todo_placeholders(self, generator):
        """No objective should contain TODO."""
        pkg = generator.generate(level_range=(50, 100))
        for obj in pkg.objectives:
            assert "TODO" not in obj

    def test_has_rewards(self, generator):
        """Boss encounter should have gold and items."""
        pkg = generator.generate(level_range=(100, 200))
        assert "gold" in pkg.rewards
        assert "items" in pkg.rewards
        assert pkg.rewards["gold"] > 0
        assert len(pkg.rewards["items"]) >= 3

    def test_boss_gold_multiplier(self, generator):
        """Boss should give 3x gold compared to base."""
        pkg = generator.generate(level_range=(100, 200))
        base_gold = max(100, 100 * 25)  # min_level=100
        expected_gold = base_gold * 3
        assert pkg.rewards["gold"] == expected_gold

    def test_has_location(self, generator):
        """Boss encounter should have world coordinates."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.location is not None
        assert len(pkg.location) == 3

    def test_has_enemy_count(self, generator):
        """Boss should have trash mob count."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.enemy_count >= 5

    # ------------------------------------------------------------------
    # Boss type hint
    # ------------------------------------------------------------------

    def test_boss_type_in_metadata(self, generator):
        """Boss type hint should appear in metadata."""
        pkg = generator.generate(level_range=(100, 200), boss_type="dragon")
        assert pkg.metadata["boss_type"] == "dragon"

    def test_default_boss_type(self, generator):
        """Default boss type should be 'standard'."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.metadata["boss_type"] == "standard"

    # ------------------------------------------------------------------
    # Objectives
    # ------------------------------------------------------------------

    def test_objectives_include_boss_name(self, generator):
        """Objectives should reference the boss name."""
        pkg = generator.generate(level_range=(100, 200))
        text = " ".join(pkg.objectives)
        assert pkg.boss_name in text

    def test_objectives_include_lair(self, generator):
        """Objectives should reference the lair location."""
        pkg = generator.generate(level_range=(100, 200))
        text = " ".join(pkg.objectives)
        # Should mention location or chamber
        assert (
            "chamber" in text.lower()
            or "lair" in text.lower()
            or "navigate" in text.lower()
        )

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_package_is_valid(self, generator):
        """Default boss encounter should pass validation."""
        pkg = generator.generate(level_range=(100, 200))
        errors = pkg.validate()
        assert errors == [], f"Validation errors: {errors}"

    def test_low_level_valid(self, generator):
        """Low-level boss should be valid."""
        pkg = generator.generate(level_range=(5, 10))
        assert pkg.is_valid()

    def test_high_level_valid(self, generator):
        """High-level boss should be valid."""
        pkg = generator.generate(level_range=(400, 500))
        assert pkg.is_valid()

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_output(self, generator):
        """Same inputs should produce same output."""
        a = generator.generate(level_range=(300, 500))
        b = generator.generate(level_range=(300, 500))
        assert a.name == b.name
        assert a.boss_name == b.boss_name
        assert a.objectives == b.objectives

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_to_dict_roundtrip(self, generator):
        """Package should survive serialization roundtrip."""
        pkg = generator.generate(level_range=(100, 200))
        data = pkg.to_dict()
        restored = QuestPackage.from_dict(data)
        assert restored.name == pkg.name
        assert restored.boss_name == pkg.boss_name
        assert restored.room_type == RoomType.BOSS_LAIR
