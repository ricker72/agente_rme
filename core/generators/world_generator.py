"""
World Generator — main orchestrator for all generators.

Converts a natural language prompt string (or structured config dict) into
a fully populated WorldModel by coordinating ThemeGenerator, HuntGenerator,
CityGenerator, DungeonGenerator, and SpawnGenerator.

Architecture:
    Prompt string
        ↓
    Theme Resolver  ─→ ThemeDefinition
        ↓
    Generator       ─→ WorldModel
        ↓
    Validator       ─→ Validated WorldModel

Usage:
    generator = WorldGenerator()
    world = generator.generate("Generate Issavi hunt level 300")
    print(len(world.tiles))  # > 0
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional, Union

from .base_generator import BaseGenerator
from .theme_generator import ThemeGenerator
from .hunt_generator import HuntGenerator
from .city_generator import CityGenerator
from .dungeon_generator import DungeonGenerator
from .spawn_generator import SpawnGenerator
from core.world import WorldModel, WorldValidator

logger = logging.getLogger(__name__)


class WorldGenerator(BaseGenerator):
    """
    Orchestrator that converts prompts into WorldModel instances.

    Interprets natural language prompts to determine:
        - Generator type (hunt, city, dungeon)
        - Theme(s)
        - Level range
        - Density

    Then delegates to the appropriate generator and validates the result.
    """

    # Keywords for each generator type
    HUNT_KEYWORDS = {"hunt", "hunting", "spawn", "monster", "grind", "kill"}
    CITY_KEYWORDS = {"city", "town", "village", "settlement"}
    DUNGEON_KEYWORDS = {"dungeon", "underground", "cave", "tunnel", "crypt", "vault"}

    # Theme keywords
    THEME_KEYWORDS = {
        "issavi": {"issavi", "desert", "sphinx", "frazzle"},
        "roshamuul": {"roshamuul", "demon", "nightmare"},
        "soul_war": {"soul", "war", "soulwar", "soul war"},
        "library": {"library", "book", "arcane"},
        "falcon": {"falcon", "bastia", "eagle"},
        "cobra": {"cobra", "snake", "venom"},
    }

    # Supported theme names (canonical)
    SUPPORTED_THEMES = {"issavi", "roshamuul", "soul_war", "library", "falcon", "cobra"}

    def __init__(self, seed: Optional[int] = None):
        self._seed = seed
        self._theme_gen = ThemeGenerator()
        self._hunt_gen = HuntGenerator(seed=seed)
        self._city_gen = CityGenerator(seed=seed)
        self._dungeon_gen = DungeonGenerator(seed=seed)
        self._spawn_gen = SpawnGenerator(seed=seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        world: Optional[WorldModel] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Generate a WorldModel from a configuration dict or string prompt.

        Args:
            world: Optional WorldModel to populate. Can also be a string prompt
                   if context is not provided (for convenience).
            context: Can be:
                - A dict with keys like 'prompt', 'theme', 'level_min', etc.
                - A string prompt (e.g., "Generate Issavi hunt level 300")
                - None (world is used as context if it's a string/dict)

        Returns:
            Populated WorldModel.

        Examples:
            # Via string prompt (world parameter used as prompt)
            generator = WorldGenerator()
            world = generator.generate("Generate Issavi hunt level 300")

            # Via config dict (world parameter used as config)
            world = generator.generate({
                "type": "hunt",
                "theme": "issavi",
                "level_min": 300,
                "level_max": 500,
            })

            # With explicit world and context
            world = generator.generate(WorldModel(), {
                "type": "hunt", "theme": "issavi",
            })
        """
        # --- Dispatch for convenience: if 'world' is a string or dict, treat as context ---
        if isinstance(world, (str, dict)):
            # No separate world or context provided; use world as the config
            config = world if isinstance(world, dict) else self._parse_prompt(world)
            world = WorldModel()
        elif context is None:
            config = {}
        elif isinstance(context, str):
            config = self._parse_prompt(context)
        elif isinstance(context, dict):
            config = dict(context)  # shallow copy
        else:
            config = {}

        # Resolve themes (may be a combined theme like "issavi_roshamuul")
        theme_name = config.get("theme", "generic")
        if "+" in theme_name:
            themes = [t.strip() for t in theme_name.split("+")]
            theme_def = self._theme_gen.resolve_multi(themes)
        elif "_" in theme_name and theme_name not in self.SUPPORTED_THEMES:
            # Try splitting combined theme names: "issavi_roshamuul"
            parts = theme_name.split("_")
            valid_parts = [p for p in parts if p in self.SUPPORTED_THEMES]
            if len(valid_parts) > 1:
                theme_def = self._theme_gen.resolve_multi(valid_parts)
            else:
                theme_def = self._theme_gen.resolve(theme_name)
        else:
            theme_def = self._theme_gen.resolve(theme_name)

        config["theme_def"] = theme_def
        config["theme"] = theme_def.theme

        # Determine generator type
        gen_type = config.get("type", self._detect_type(config))

        # Delegate to specific generator
        if gen_type == "city":
            world = self._city_gen.generate(world, config)
        elif gen_type == "dungeon":
            world = self._dungeon_gen.generate(world, config)
        else:  # default: hunt
            world = self._hunt_gen.generate(world, config)

        # Validate the result
        self._validate_result(world)

        logger.info(
            f"WorldGenerator: generated {gen_type} world ({theme_def.theme}) with {world.tile_count()} tiles"
        )
        return world

    # ------------------------------------------------------------------
    # Prompt parsing
    # ------------------------------------------------------------------

    def _parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parse a natural language prompt into a configuration dict.

        Example:
            "Generate Issavi hunt level 300" →
            {"type": "hunt", "theme": "issavi", "level_min": 280, "level_max": 320}
        """
        config: Dict[str, Any] = {}
        prompt_lower = prompt.lower()

        # Extract level
        level_match = re.search(r"level\s*(\d+)", prompt_lower)
        if level_match:
            level = int(level_match.group(1))
            config["level_min"] = max(1, level - 20)
            config["level_max"] = level + 20
        else:
            # Try range: "level 300-500"
            range_match = re.search(r"level\s*(\d+)\s*[-–]\s*(\d+)", prompt_lower)
            if range_match:
                config["level_min"] = int(range_match.group(1))
                config["level_max"] = int(range_match.group(2))

        # Extract theme
        theme = self._extract_theme(prompt_lower)
        if theme:
            config["theme"] = theme

        # Detect type
        config["type"] = self._detect_type(prompt_lower)

        return config

    def _extract_theme(self, text: str) -> Optional[str]:
        """Extract theme name from prompt text."""
        # Check for combined themes (e.g., "Issavi + Roshamuul")
        theme_mentions = []
        for canonical, keywords in self.THEME_KEYWORDS.items():
            for kw in keywords:
                if kw in text:
                    theme_mentions.append(canonical)
                    break

        if len(theme_mentions) > 1:
            return "+".join(theme_mentions)
        elif len(theme_mentions) == 1:
            return theme_mentions[0]

        return None

    def _detect_type(self, config: Union[str, Dict[str, Any]]) -> str:
        """Detect the generator type from config or prompt text."""
        if isinstance(config, str):
            text = config.lower()
            if any(kw in text for kw in self.DUNGEON_KEYWORDS):
                return "dungeon"
            if any(kw in text for kw in self.CITY_KEYWORDS):
                return "city"
            return "hunt"

        # Dict mode: check explicit type or fall back to hunt
        type_str = config.get("type", "hunt").lower()
        if type_str in ("city", "dungeon"):
            return type_str
        return "hunt"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_result(self, world: WorldModel) -> None:
        """Run the WorldValidator on the result and log warnings."""
        validator = WorldValidator()
        result = validator.validate(world)

        if not result.passed:
            logger.warning(f"WorldGenerator: validation failed:\n{result.summary()}")
        if result.warnings:
            for w in result.warnings:
                logger.debug(f"WorldGenerator validation warning: {w}")
