"""
Tests for QuestGenerator — validates quest content generation.

Covers: quest generation, quest types (exploration, combat, lever, puzzle,
boss, rescue, collection), QuestPackage validation, level ranges, and
integration with MapDesigner.
"""

import pytest

from core.content.quest_package import QuestPackage, RoomType
from core.content.map_designer import MapDesigner
from core.content.quest_generator import QuestGenerator


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


class TestQuestGenerator:
    """Test the QuestGenerator."""

    @pytest.fixture
    def deps(self):
        """Create shared dependencies."""
        registry = FakeAssetRegistry()
        world = FakeWorldModel()
        designer = MapDesigner(world_model=world, asset_registry=registry)
        return registry, designer, world

    @pytest.fixture
    def generator(self, deps):
        """Create a QuestGenerator with fake deps."""
        registry, designer, world = deps
        return QuestGenerator(registry, designer, world)

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

    def test_generate_low_level(self, generator):
        """Low-level quests should work."""
        pkg = generator.generate(level_range=(5, 10))
        assert pkg.level_min == 5
        assert pkg.level_max == 10
        assert pkg.is_valid()

    def test_generate_high_level(self, generator):
        """High-level quests should work."""
        pkg = generator.generate(level_range=(400, 500))
        assert pkg.level_min == 400
        assert pkg.is_valid()

    def test_no_todo_placeholders(self, generator):
        """No objective should contain TODO."""
        pkg = generator.generate(level_range=(50, 100))
        for obj in pkg.objectives:
            assert "TODO" not in obj

    def test_has_name(self, generator):
        """Package should have a non-empty name."""
        pkg = generator.generate(level_range=(50, 100))
        assert pkg.name
        assert len(pkg.name) > 0

    def test_has_description(self, generator):
        """Package should have a non-empty description."""
        pkg = generator.generate(level_range=(50, 100))
        assert pkg.description
        assert len(pkg.description) > 0

    def test_has_objectives(self, generator):
        """Package should have at least one objective."""
        pkg = generator.generate(level_range=(50, 100))
        assert len(pkg.objectives) > 0

    def test_has_rewards(self, generator):
        """Package should have rewards with gold and items."""
        pkg = generator.generate(level_range=(50, 100))
        assert "gold" in pkg.rewards
        assert "items" in pkg.rewards
        assert pkg.rewards["gold"] > 0
        assert len(pkg.rewards["items"]) > 0

    def test_has_location(self, generator):
        """Package should have world coordinates."""
        pkg = generator.generate(level_range=(50, 100))
        assert pkg.location is not None
        assert len(pkg.location) == 3

    def test_enemy_count_scales(self, generator):
        """Enemy count should increase with level."""
        low = generator.generate(level_range=(10, 20))
        high = generator.generate(level_range=(400, 500))
        assert high.enemy_count >= low.enemy_count

    # ------------------------------------------------------------------
    # Quest types
    # ------------------------------------------------------------------

    def test_exploration_quest(self, generator):
        """Exploration quest should have exploration objectives."""
        pkg = generator.generate(level_range=(50, 100), quest_type="exploration")
        assert "exploration" in pkg.metadata.get("quest_type", "")
        assert pkg.room_type == RoomType.NONE

    def test_combat_quest(self, generator):
        """Combat quest should have combat objectives."""
        pkg = generator.generate(level_range=(50, 100), quest_type="combat")
        assert any("Defeat" in o or "enemy" in o.lower() for o in pkg.objectives)

    def test_lever_quest(self, generator):
        """Lever quest should have lever room type."""
        pkg = generator.generate(level_range=(50, 100), quest_type="lever")
        assert pkg.room_type == RoomType.LEVER
        assert len(pkg.objectives) >= 2

    def test_puzzle_quest(self, generator):
        """Puzzle quest should have puzzle room type."""
        pkg = generator.generate(level_range=(50, 100), quest_type="puzzle")
        assert pkg.room_type == RoomType.PUZZLE
        assert len(pkg.objectives) >= 2

    def test_boss_quest(self, generator):
        """Boss quest should have boss lair room type and boss name."""
        pkg = generator.generate(level_range=(50, 100), quest_type="boss")
        assert pkg.room_type == RoomType.BOSS_LAIR
        assert pkg.boss_name is not None
        assert len(pkg.boss_name) > 0

    def test_rescue_quest(self, generator):
        """Rescue quest should have rescue-themed objectives."""
        pkg = generator.generate(level_range=(50, 100), quest_type="rescue")
        text = " ".join(pkg.objectives).lower()
        assert "captive" in text or "guard" in text or "escort" in text

    def test_collection_quest(self, generator):
        """Collection quest should have collection objectives."""
        pkg = generator.generate(level_range=(50, 100), quest_type="collection")
        text = " ".join(pkg.objectives).lower()
        assert "artifact" in text or "relic" in text or "gather" in text

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def test_package_is_valid(self, generator):
        """Default quest package should pass validation."""
        pkg = generator.generate(level_range=(50, 100))
        errors = pkg.validate()
        assert errors == [], f"Validation errors: {errors}"

    def test_all_quest_types_valid(self, generator):
        """All quest types should produce valid packages."""
        for qtype in (
            "exploration",
            "combat",
            "rescue",
            "collection",
            "lever",
            "puzzle",
            "boss",
        ):
            pkg = generator.generate(level_range=(50, 100), quest_type=qtype)
            assert pkg.is_valid(), (
                f"Quest type '{qtype}' failed validation: {pkg.validate()}"
            )

    # ------------------------------------------------------------------
    # Determinism
    # ------------------------------------------------------------------

    def test_deterministic_output(self, generator):
        """Same inputs should produce same output."""
        a = generator.generate(level_range=(300, 500))
        b = generator.generate(level_range=(300, 500))
        assert a.name == b.name
        assert a.objectives == b.objectives
        assert a.rewards == b.rewards

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def test_to_dict_roundtrip(self, generator):
        """Package should survive to_dict → from_dict roundtrip."""
        pkg = generator.generate(level_range=(100, 200))
        data = pkg.to_dict()
        restored = QuestPackage.from_dict(data)
        assert restored.name == pkg.name
        assert restored.level_min == pkg.level_min
        assert restored.level_max == pkg.level_max
        assert restored.objectives == pkg.objectives
