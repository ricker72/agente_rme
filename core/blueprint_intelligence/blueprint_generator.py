"""
BlueprintGenerator — generates blueprints from prompts.

Can generate from:
  Natural language prompt
  Knowledge Dataset
  Pattern Library
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core.blueprints.blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from .models.blueprint_pattern import BlueprintPattern
from .blueprint_embedding_engine import BlueprintEmbeddingEngine
from .blueprint_fusion_engine import BlueprintFusionEngine


class BlueprintGenerator:
    """
    Generates new blueprints from prompts, knowledge, and patterns.

    Supports:
      - Generating blueprints from natural language prompts
      - Generating hybrid blueprints using style ratios
      - Generating from pattern libraries
    """

    def __init__(
        self,
        embedding_engine: Optional[BlueprintEmbeddingEngine] = None,
        fusion_engine: Optional[BlueprintFusionEngine] = None,
    ) -> None:
        self.embedding_engine = embedding_engine or BlueprintEmbeddingEngine()
        self.fusion_engine = fusion_engine or BlueprintFusionEngine(
            embedding_engine=self.embedding_engine,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        blueprints: Optional[List[Blueprint]] = None,
        patterns: Optional[List[BlueprintPattern]] = None,
    ) -> Blueprint:
        """
        Generate a blueprint from a natural language prompt.

        Args:
            prompt: Natural language description (e.g., "Generate hunt level 400")
            blueprints: Available blueprints for reference.
            patterns: Available patterns for reference.

        Returns:
            Generated Blueprint.
        """
        prompt_lower = prompt.lower()

        # Detect intent from prompt
        if "hunt" in prompt_lower:
            return self._generate_hunt(prompt, blueprints)
        elif "city" in prompt_lower:
            return self._generate_city(prompt, blueprints)
        elif "boss" in prompt_lower or "boss_room" in prompt_lower:
            return self._generate_boss_room(prompt, blueprints)
        elif "hybrid" in prompt_lower or "%" in prompt_lower:
            return self._generate_hybrid(prompt, blueprints)
        else:
            return self._generate_dungeon(prompt, blueprints)

    def generate_hybrid(
        self,
        prompt: str,
        blueprints: List[Blueprint],
        ratios: Optional[Dict[str, float]] = None,
    ) -> Blueprint:
        """
        Generate a hybrid blueprint from a prompt with style ratios.

        Example:
            generate_hybrid("hunt level 400", blueprints, {
                "Roshamuul": 0.7,
                "Soul War": 0.3
            })
        """
        if not ratios:
            ratios = self._parse_ratios_from_prompt(prompt)

        if not ratios or not blueprints:
            return self._generate_dungeon(prompt, blueprints)

        # Find blueprints matching the named styles
        matched: Dict[str, Blueprint] = {}
        for name in ratios:
            for bp in blueprints:
                if name.lower() in bp.name.lower():
                    matched[name] = bp
                    break

        if len(matched) < 2:
            return self._generate_dungeon(prompt, blueprints)

        # Sort by ratio and fuse
        sorted_styles = sorted(ratios.items(), key=lambda x: x[1], reverse=True)
        main_style = sorted_styles[0][0]
        secondary_style = sorted_styles[1][0]

        result = self.fusion_engine.fuse(
            matched[main_style],
            matched[secondary_style],
            ratio=ratios[main_style],
            name=f"hybrid_{main_style}_{secondary_style}",
        )

        if result.blueprint:
            result.blueprint.description = prompt
            return result.blueprint

        return self._generate_dungeon(prompt, blueprints)

    def generate_from_template(
        self,
        template: Blueprint,
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Blueprint:
        """Generate a blueprint by modifying a template."""
        import copy

        bp = copy.deepcopy(template)

        if modifications:
            if "size" in modifications:
                bp.size = modifications["size"]
            if "theme" in modifications:
                bp.theme = modifications["theme"]
            if "category" in modifications:
                bp.category = modifications["category"]
            if "tags" in modifications:
                bp.metadata.tags = modifications["tags"]

        return bp

    # ------------------------------------------------------------------
    # Generation Methods
    # ------------------------------------------------------------------

    def _generate_hunt(
        self, prompt: str, blueprints: Optional[List[Blueprint]]
    ) -> Blueprint:
        """Generate a hunt-type blueprint."""
        level = self._extract_level(prompt)
        theme = self._extract_theme(prompt)
        size = self._calc_hunt_size(level)

        bp = Blueprint(
            name=f"hunt_lvl{level}",
            theme=theme or "generic",
            category="hunt",
            size=size,
            description=prompt,
            metadata=BlueprintMetadata(
                tags=["hunt", f"level_{level}", theme or "generic"],
                difficulty="medium" if level < 300 else "hard",
            ),
        )
        bp.tiles = self._generate_tiles_for_size(size)
        return bp

    def _generate_city(
        self, prompt: str, blueprints: Optional[List[Blueprint]]
    ) -> Blueprint:
        """Generate a city-type blueprint."""
        compact = "compact" in prompt.lower()

        bp = Blueprint(
            name="generated_city",
            theme=self._extract_theme(prompt) or "city",
            category="city",
            size=(25, 25) if not compact else (15, 15),
            description=prompt,
            metadata=BlueprintMetadata(
                tags=["city", "compact" if compact else "standard"],
                difficulty="safe",
            ),
        )

        # Add city services
        services = ["depot", "temple", "market", "bank"]
        for i, service in enumerate(services):
            bp.zones.append(
                {
                    "type": service,
                    "name": f"{service}_zone",
                    "position": {"x": i * 5, "y": 5},
                }
            )

        bp.tiles = self._generate_tiles_for_size(bp.size)
        return bp

    def _generate_boss_room(
        self, prompt: str, blueprints: Optional[List[Blueprint]]
    ) -> Blueprint:
        """Generate a boss room blueprint."""
        bp = Blueprint(
            name="generated_boss_room",
            theme=self._extract_theme(prompt) or "dungeon",
            category="boss_room",
            size=(10, 10),
            description=prompt,
            metadata=BlueprintMetadata(
                tags=["boss", "boss_room"],
                difficulty="hard",
            ),
        )
        bp.zones.append(
            {
                "type": "boss_room",
                "name": "main_boss",
                "difficulty": "hard",
            }
        )
        bp.tiles = self._generate_tiles_for_size(bp.size)
        return bp

    def _generate_dungeon(
        self, prompt: str, blueprints: Optional[List[Blueprint]]
    ) -> Blueprint:
        """Generate a dungeon-type blueprint."""
        bp = Blueprint(
            name="generated_dungeon",
            theme=self._extract_theme(prompt) or "dungeon",
            category="dungeon",
            size=(20, 20),
            description=prompt,
            metadata=BlueprintMetadata(
                tags=["dungeon", "generated"],
                difficulty="medium",
            ),
        )
        bp.tiles = self._generate_tiles_for_size(bp.size)
        return bp

    def _generate_hybrid(
        self, prompt: str, blueprints: Optional[List[Blueprint]]
    ) -> Blueprint:
        """Generate a hybrid blueprint from prompt."""
        ratios = self._parse_ratios_from_prompt(prompt)
        if ratios and blueprints:
            return self.generate_hybrid(prompt, blueprints, ratios)
        return self._generate_dungeon(prompt, blueprints)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_level(prompt: str) -> int:
        """Extract level number from prompt."""
        import re

        levels = re.findall(r"\b(\d{2,4})\b", prompt)
        for lvl in levels:
            lvl_val = int(lvl)
            if 8 <= lvl_val <= 2000:
                return lvl_val
        return 300

    @staticmethod
    def _extract_theme(prompt: str) -> str:
        """Extract theme name from prompt."""
        known_themes = [
            "roshamuul",
            "soul war",
            "issavi",
            "falcon",
            "ferumbras",
            "library",
            "asylum",
            "catacomb",
            "ice",
            "fire",
            "death",
            "dungeon",
            "city",
            "forest",
            "desert",
            "swamp",
        ]
        prompt_lower = prompt.lower()
        for theme in known_themes:
            if theme in prompt_lower:
                return theme.replace(" ", "_")
        return ""

    @staticmethod
    def _calc_hunt_size(level: int) -> Tuple[int, int]:
        """Calculate hunt size based on level."""
        base = max(15, min(50, level // 10))
        return (base, base)

    @staticmethod
    def _generate_tiles_for_size(size: Tuple[int, int]) -> List[BlueprintTile]:
        """Generate a basic tile grid for a given size."""
        tiles: List[BlueprintTile] = []
        for x in range(size[0]):
            for y in range(size[1]):
                tiles.append(BlueprintTile(x=x, y=y, ground=100))
        return tiles

    @staticmethod
    def _parse_ratios_from_prompt(
        prompt: str,
    ) -> Dict[str, float]:
        """Parse style ratios from a prompt (e.g., '70% Roshamuul 30% Soul War')."""
        import re

        ratios: Dict[str, float] = {}
        pattern = r"(\d+)%\s*([A-Za-z\s]+?)(?=\s+\d+%|$)"
        matches = re.findall(pattern, prompt)
        for pct, name in matches:
            ratios[name.strip()] = float(pct) / 100.0
        return ratios
