"""
Base Generator — abstract base class for all WorldModel generators.

All generators in this package inherit from BaseGenerator and implement
the `generate` method, which must return a WorldModel instance (or None).

Architecture:
  BaseGenerator
    ├── ThemeGenerator   — resolves theme strings into ThemeDefinition
    ├── SpawnGenerator   — places monster spawns on existing tiles
    ├── HuntGenerator    — generates complete hunt zones
    ├── CityGenerator    — generates city layouts
    ├── DungeonGenerator — generates dungeon layouts
    └── WorldGenerator   — orchestrates all generators from a prompt
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.world import WorldModel


class BaseGenerator(ABC):
    """
    Abstract base for all procedural generators.

    Every generator subclass must implement `generate()`, which
    receives a WorldModel to populate and a context dict for
    configuration parameters.
    """

    @abstractmethod
    def generate(
        self,
        world: WorldModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Populate a WorldModel with generated content.

        Args:
            world: A WorldModel instance to populate. Generators should
                   add tiles, structures, regions, and spawns to this object.
            context: Optional dictionary of configuration parameters
                     (e.g., theme, level range, density).

        Returns:
            The same WorldModel instance (mutated in place) for chaining.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement generate()"
        )
