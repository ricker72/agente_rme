"""Tests for BlueprintGenerator."""

import pytest
from core.blueprints.blueprint import Blueprint, BlueprintMetadata
from core.blueprint_intelligence.blueprint_generator import BlueprintGenerator


class TestBlueprintGenerator:
    """Test blueprint generation."""

    def setup_method(self):
        self.generator = BlueprintGenerator()

    def _make_bp(self, name="test", category="hunt", theme="generic"):
        return Blueprint(
            name=name,
            category=category,
            theme=theme,
            metadata=BlueprintMetadata(tags=[category]),
        )

    def test_generate_hunt(self):
        """Test generating a hunt blueprint."""
        bp = self.generator.generate("Generate hunt level 400")
        assert bp.category == "hunt"
        assert bp.description == "Generate hunt level 400"

    def test_generate_city(self):
        """Test generating a city blueprint."""
        bp = self.generator.generate("Generate city Issavi style")
        assert bp.category == "city"

    def test_generate_city_compact(self):
        """Test generating compact city."""
        bp = self.generator.generate("compact city")
        assert bp.category == "city"
        assert bp.size[0] < 20

    def test_generate_boss_room(self):
        """Test generating a boss room."""
        bp = self.generator.generate("Generate boss room")
        assert bp.category == "boss_room"

    def test_generate_dungeon(self):
        """Test generating a dungeon."""
        bp = self.generator.generate("Generate dungeon")
        assert bp is not None
        assert bp.tiles is not None

    def test_generate_hybrid_with_prompt(self):
        """Test generating hybrid from prompt with percentages."""
        bps = [
            self._make_bp("Roshamuul", "hunt", "roshamuul"),
            self._make_bp("Soul_War", "hunt", "soul_war"),
        ]
        bp = self.generator.generate("70% Roshamuul 30% Soul War", blueprints=bps)
        assert bp is not None

    def test_generate_hybrid_method(self):
        """Test generate_hybrid with explicit ratios."""
        bps = [
            self._make_bp("Roshamuul", "hunt", "roshamuul"),
            self._make_bp("Soul_War", "hunt", "soul_war"),
        ]
        ratios = {"Roshamuul": 0.7, "Soul War": 0.3}
        bp = self.generator.generate_hybrid("hunt", bps, ratios)
        assert bp is not None

    def test_generate_from_template(self):
        """Test generating from template."""
        template = self._make_bp("template", "city")
        modified = self.generator.generate_from_template(
            template, {"theme": "issavi", "tags": ["compact"]}
        )
        assert modified.theme == "issavi"
        assert "compact" in modified.metadata.tags

    def test_extract_level(self):
        """Test level extraction from prompt."""
        assert self.generator._extract_level("hunt level 400") == 400
        assert self.generator._extract_level("level 150 zone") == 150
        assert self.generator._extract_level("no level") == 300

    def test_extract_theme(self):
        """Test theme extraction."""
        assert self.generator._extract_theme("roshamuul hunt") == "roshamuul"
        assert self.generator._extract_theme("issavi city") == "issavi"
        assert self.generator._extract_theme("unknown theme") == ""

    def test_calc_hunt_size(self):
        """Test hunt size calculation."""
        size_200 = self.generator._calc_hunt_size(200)
        assert size_200[0] == 20
        size_500 = self.generator._calc_hunt_size(500)
        assert size_500[0] == 50

    def test_generate_tiles_for_size(self):
        """Test tile generation for size."""
        tiles = self.generator._generate_tiles_for_size((5, 5))
        assert len(tiles) == 25

    def test_parse_ratios_from_prompt(self):
        """Test parsing ratios from prompt."""
        ratios = self.generator._parse_ratios_from_prompt("70% Roshamuul 30% Soul War")
        assert "Roshamuul" in ratios
        assert abs(ratios["Roshamuul"] - 0.7) < 0.01
        assert abs(ratios["Soul War"] - 0.3) < 0.01