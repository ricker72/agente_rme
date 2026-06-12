"""
Tests for RaidGenerator — validates raid content generation.

Covers: raid generation, difficulty levels, party sizes, boss selection,
objectives, rewards, and QuestPackage validation.
"""

import pytest

from core.content.quest_package import QuestPackage, RoomType
from core.content.map_designer import MapDesigner
from core.content.raid_generator import RaidGenerator


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


class TestRaidGenerator:
    """Test the RaidGenerator."""

    @pytest.fixture
    def deps(self):
        """Create shared dependencies."""
        registry = FakeAssetRegistry()
        world = FakeWorldModel()
        designer = MapDesigner(world_model=world, asset_registry=registry)
        return registry, designer, world

    @pytest.fixture
    def generator(self, deps):
        """Create a RaidGenerator with fake deps."""
        registry, designer, world = deps
        return RaidGenerator(registry, designer, world)

    # ------------------------------------------------------------------
    # Basic generation
    # ------------------------------------------------------------------

    def test_generate_returns_quest_package(self, generator):
        """generate() should return a QuestPackage instance."""
        pkg = generator.generate(level_range=(300, 500))
        assert isinstance(pkg, QuestPackage)

    def test_generate_level_range(self, generator):
        """Generated package should respect level range."""
        pkg = generator.generate(level_range=(150, 300))
        assert pkg.level_min == 150
        assert pkg.level_max == 300

    def test_raid_has_arena_room_type(self, generator):
        """Raid should use ARENA room type."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.room_type == RoomType.ARENA

    def test_raid_has_boss(self, generator):
        """Raid should always have a boss."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.boss_name is not None
        assert len(pkg.boss_name) > 0

    def test_raid_has_boss_metadata(self, generator):
        """Raid metadata should contain boss_abilities."""
        pkg = generator.generate(level_range=(100, 200))
        assert "boss_abilities" in pkg.metadata
        assert len(pkg.metadata["boss_abilities"]) > 0

    def test_raid_has_raid_flag(self, generator):
        """Raid metadata should have raid=True."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.metadata.get("raid") is True

    def test_no_todo_placeholders(self, generator):
        """No objective should contain TODO."""
        pkg = generator.generate(level_range=(50, 100))
        for obj in pkg.objectives:
            assert "TODO" not in obj

    def test_has_rewards(self, generator):
        """Raid should have gold and items."""
        pkg = generator.generate(level_range=(100, 200))
        assert "gold" in pkg.rewards
        assert "items" in pkg.rewards
        assert pkg.rewards["gold"] > 0
        assert len(pkg.rewards["items"]) >= 3

    def test_has_location(self, generator):
        """Raid should have world coordinates."""
        pkg = generator.generate(level_range=(100, 200))
        assert pkg.location is not None
        assert len(pkg.location) == 3

    # ------------------------------------------------------------------
    # Party size
    # ------------------------------------------------------------------

    def test_party_size_in_objectives(self, generator):
        """Objectives should reference the party size."""
        pkg = generator.generate(level_range=(100, 200), party_size=8)
        text = " ".join(pkg.objectives)
        assert "8" in text

    def test_party_size_in_metadata(self, generator):
        """Metadata should contain party_size."""
        pkg = generator.generate(level_range=(100, 200), party_size=6)
        assert pkg.metadata["party_size"] == 6

    # ------------------------------------------------------------------
    # Difficulty
    # ------------------------------------------------------------------

    def test_normal_difficulty(self, generator):
        """Normal difficulty should produce valid package."""
        pkg = generator.generate(level_range=(100, 200), difficulty="normal")
        assert pkg.is_valid()
        assert pkg.metadata["difficulty"] == "normal"

    def test_hard_difficulty_more_gold(self, generator):
        """Hard difficulty should give more gold than normal."""
        normal = generator.generate(level_range=(100, 200), difficulty="normal")
        hard = generator.generate(level_range=(100, 200), difficulty="hard")
        assert hard.rewards["gold"] >= normal.rewards["gold"]

    def test_epic_difficulty_more_items(self, generator):
        """Epic difficulty should give more items."""
        normal = generator.generate(level_range=(100, 200), difficulty="normal")
        epic = generator.generate(level_range=(100, 200), difficulty="epic")
        assert len(epic.rewards["items"]) >= len(normal.rewards["items"])

    def test_epic_has_enrage_objective(self, generator):
        """Epic difficulty should include enrage phase objective."""
        pkg = generator.generate(level_range=(100, 200), difficulty="epic")
        text = " ".join(pkg.objectives).lower()
        assert "enrage" in text

    def test_hard_has_elite_objective(self, generator):
        """Hard difficulty should include elite guard objective."""
        pkg = generator.generate(level_range=(100, 200), difficulty="hard")
        text = " ".join(pkg.objectives).lower()
        assert "elite" in text

    # ------------------------------------------------------------------
    # Enemy count
    # ------------------------------------------------------------------

    def test_enemy_count_scales_with_level(self, generator):
        """Higher level raids should have more enemies."""
        low = generator.generate(level_range=(50, 100))
        high = generator.generate(level_range=(400, 500))
        assert high.enemy_count >= low.enemy_count

    def test_enemy_count_minimum(self, generator):
        """Enemy count should be at least 10."""
        pkg = generator.generate(level_range=(1, 5))
        assert pkg.enemy_count >= 10

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_package_is_valid(self, generator):
        """Default raid should pass validation."""
        pkg = generator.generate(level_range=(100, 200))
        errors = pkg.validate()
        assert errors == [], f"Validation errors: {errors}"

    def test_all_difficulties_valid(self, generator):
        """All difficulty levels should produce valid packages."""
        for diff in ("normal", "hard", "epic"):
            pkg = generator.generate(level_range=(100, 200), difficulty=diff)
            assert pkg.is_valid(), f"Difficulty '{diff}' failed: {pkg.validate()}"

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_output(self, generator):
        """Same inputs should produce same output."""
        a = generator.generate(level_range=(300, 500))
        b = generator.generate(level_range=(300, 500))
        assert a.name == b.name
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
        assert restored.level_min == pkg.level_min
        assert restored.boss_name == pkg.boss_name
