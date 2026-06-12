"""
Spawn Generator — places monster spawns into a WorldModel.

Uses the existing core.spawn.SpawnGenerator for the underlying
monster selection logic, but places spawns directly into
WorldModel tiles rather than returning spawn plans.
"""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, List, Optional

from .base_generator import BaseGenerator
from .theme_generator import ThemeDefinition
from core.world import WorldModel, Tile, Spawn

logger = logging.getLogger(__name__)


class SpawnGenerator(BaseGenerator):
    """
    Places monster spawns into a WorldModel based on theme and level range.

    Usage:
        sg = SpawnGenerator()
        world = sg.generate(world, {
            "theme_def": theme_definition,
            "level_min": 300,
            "level_max": 500,
            "density": "medium",
        })
    """

    # Map density string to spawns-per-tile ratio
    DENSITY_RATIOS = {
        "low": 0.02,
        "medium": 0.05,
        "high": 0.10,
    }

    # Difficulty-based monster pools (fallback if theme has no defined monsters)
    MONSTER_TIERS = {
        "easy": [
            "Crypt Warden",
            "Skeleton",
            "Demon Skeleton",
            "Priestess",
            "Death Priest",
        ],
        "medium": [
            "Frazzlemaw",
            "Sphinx",
            "Cloak Of Terror",
            "Crypt Warden",
            "Vexclaw",
        ],
        "hard": [
            "Frazzlemaw",
            "Guzzlemaw",
            "Cloak Of Terror",
            "Sphinx",
            "Vexclaw",
            "Shrieker",
        ],
        "extreme": [
            "Guzzlemaw",
            "Cloak Of Terror",
            "Vexclaw",
            "Shrieker",
            "Frazzlemaw",
        ],
    }

    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        world: WorldModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Add monster spawns to a WorldModel.

        Context parameters:
            - theme_def: ThemeDefinition (with monster pool)
            - level_min: int (default 1)
            - level_max: int (default 9999)
            - density: str, one of 'low', 'medium', 'high' (default 'medium')
            - area: tuple (x1, y1, x2, y2) — restrict spawns to this area
            - spawn_chance: float 0.0-1.0 override for per-tile spawn chance

        Returns:
            WorldModel with spawns added to tiles.
        """
        if context is None:
            context = {}

        theme_def: Optional[ThemeDefinition] = context.get("theme_def")
        level_min = context.get("level_min", 1)
        level_max = context.get("level_max", 9999)
        density = context.get("density", "medium")
        area = context.get("area")

        # Determine spawn density
        spawn_ratio = self.DENSITY_RATIOS.get(density, 0.05)
        spawn_ratio = context.get("spawn_chance", spawn_ratio)

        # Determine monster pool
        monsters = self._get_monster_pool(theme_def, level_min, level_max)

        if not monsters:
            logger.warning("No monsters available for spawn generation")
            return world

        # Get candidate tiles
        tiles_to_process = list(world.tiles.values())
        if area:
            x1, y1, x2, y2 = area
            tiles_to_process = [
                t for t in tiles_to_process if x1 <= t.x <= x2 and y1 <= t.y <= y2
            ]

        # Place spawns randomly across eligible tiles
        for tile in tiles_to_process:
            if self._rng.random() < spawn_ratio:
                monster_name = self._rng.choice(monsters)
                tile.spawn = Spawn(
                    monster=monster_name,
                    respawn=60,
                    radius=5,
                )

        logger.info(
            f"SpawnGenerator: placed spawns on {sum(1 for t in tiles_to_process if t.spawn is not None)} tiles"
        )

        return world

    def generate_tile(
        self,
        tile: Tile,
        monster_pool: List[str],
        is_boss: bool = False,
    ) -> Tile:
        """
        Add a single spawn to a specific tile.

        Args:
            tile: Tile to place the spawn on.
            monster_pool: List of monster names to choose from.
            is_boss: If True, use boss respawn time (120s).

        Returns:
            The same tile with spawn added.
        """
        if not monster_pool:
            return tile

        monster_name = self._rng.choice(monster_pool)
        tile.spawn = Spawn(
            monster=monster_name,
            respawn=120 if is_boss else 60,
            radius=5,
        )
        return tile

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_monster_pool(
        self,
        theme_def: Optional[ThemeDefinition],
        level_min: int,
        level_max: int,
    ) -> List[str]:
        """Get the appropriate monster pool for the given theme and level range."""
        monsters: List[str] = []

        if theme_def and theme_def.monsters:
            monsters.extend(theme_def.monsters)

        # If theme has no monsters, use difficulty tier
        if not monsters:
            avg_level = (level_min + level_max) / 2
            tier = self._difficulty_tier(avg_level)
            monsters = list(self.MONSTER_TIERS.get(tier, self.MONSTER_TIERS["medium"]))

        return monsters

    @staticmethod
    def _difficulty_tier(avg_level: float) -> str:
        """Map average level to difficulty tier."""
        if avg_level < 200:
            return "easy"
        elif avg_level < 400:
            return "medium"
        elif avg_level < 600:
            return "hard"
        else:
            return "extreme"
