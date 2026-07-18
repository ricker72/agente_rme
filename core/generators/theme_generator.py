"""
Theme Generator — resolves theme strings into ThemeDefinition objects.

Supported themes:
    Issavi, Roshamuul, Soul War, Library, Falcon, Cobra
    (case-insensitive, spaces/hyphens normalized)

Each ThemeDefinition contains:
    - theme name
    - ground tile IDs
    - wall tile IDs
    - decoration tile IDs
    - monster pool (for spawn placement)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base_generator import BaseGenerator
from core.world import WorldModel


@dataclass
class ThemeDefinition:
    """Resolved definition for a visual/monster theme."""

    theme: str
    grounds: List[int] = field(default_factory=list)
    walls: List[int] = field(default_factory=list)
    decorations: List[int] = field(default_factory=list)
    monsters: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme": self.theme,
            "grounds": self.grounds,
            "walls": self.walls,
            "decorations": self.decorations,
            "monsters": self.monsters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ThemeDefinition:
        return cls(
            theme=data.get("theme", "generic"),
            grounds=data.get("grounds", data.get("ground", [])),
            walls=data.get("walls", []),
            decorations=data.get("decorations", []),
            monsters=data.get("monsters", []),
        )


# -- Built-in theme definitions (fallback if JSON templates not found) --
BUILTIN_THEMES: Dict[str, Dict[str, Any]] = {
    "issavi": {
        "theme": "issavi",
        "grounds": [415, 393, 421],
        "walls": [1495, 1496, 1497],
        "decorations": [2153, 2117, 1803],
        "monsters": ["Frazzlemaw", "Sphinx", "Cloak Of Terror"],
    },
    "roshamuul": {
        "theme": "roshamuul",
        "grounds": [1053, 1056, 1057],
        "walls": [1500, 1501, 1502],
        "decorations": [2150, 2151, 2152],
        "monsters": ["Demon", "Nightmare", "Vampire"],
    },
    "soul_war": {
        "theme": "soul_war",
        "grounds": [514, 513, 516],
        "walls": [1504, 1505, 1506],
        "decorations": [2155, 2156, 2157],
        "monsters": ["Soul War", "Nightmare", "Shrieker"],
    },
    "library": {
        "theme": "library",
        "grounds": [396, 397, 398],
        "walls": [1498, 1499, 1503],
        "decorations": [2148, 2149, 2154],
        "monsters": ["Sphinx", "Gargoyle", "Hydra"],
    },
    "falcon": {
        "theme": "falcon",
        "grounds": [428, 429, 430],
        "walls": [1507, 1508, 1509],
        "decorations": [2158, 2159, 2160],
        "monsters": ["Falcon", "Guzzlemaw", "Vexclaw"],
    },
    "cobra": {
        "theme": "cobra",
        "grounds": [514, 513, 516],
        "walls": [1504, 1505, 1506],
        "decorations": [2155, 2156, 2157],
        "monsters": ["Cobra", "Vexclaw", "Shrieker"],
    },
}


def _normalize_theme(name: str) -> str:
    """Normalize a theme string to internal key format.

    Examples:
        'Issavi'          -> 'issavi'
        'Soul War'        -> 'soul_war'
        'soul-war'        -> 'soul_war'
        'Roshamuul'       -> 'roshamuul'
        'Issavi+Roshamuul' -> 'issavi+roshamuul'
    """
    name = name.strip().lower().replace("-", "_").replace(" ", "_")
    return name


class ThemeGenerator(BaseGenerator):
    """
    Resolves theme strings into ThemeDefinition objects.

    Loads definitions from JSON template files (templates/*.json)
    and falls back to built-in definitions.

    Usage:
        tg = ThemeGenerator()
        theme_def = tg.resolve("Issavi")
        print(theme_def.grounds)  # [415, 393, 421]
    """

    def __init__(self, template_dir: Optional[str] = None):
        """
        Args:
            template_dir: Path to template JSON files directory.
                          Defaults to "templates/" relative to project root.
        """
        if template_dir is None:
            # Auto-detect relative to this file's location
            here = Path(__file__).resolve().parent
            # Navigate up to project root and into templates/
            template_dir = str(here.parent.parent / "templates")
        self._template_dir = Path(template_dir)
        self._cache: Dict[str, ThemeDefinition] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, theme_name: str) -> ThemeDefinition:
        """
        Resolve a theme name to a ThemeDefinition.

        Args:
            theme_name: Theme name (e.g., 'Issavi', 'Soul War', 'Library').

        Returns:
            ThemeDefinition with ground/wall/deco IDs and monster pool.
        """
        key = _normalize_theme(theme_name)

        # Check cache first
        if key in self._cache:
            return self._cache[key]

        # Try loading from template JSON
        theme_def = self._load_from_json(key)

        # Fall back to built-in
        if theme_def is None and key in BUILTIN_THEMES:
            theme_def = ThemeDefinition.from_dict(BUILTIN_THEMES[key])

        # Absolute fallback: generic
        if theme_def is None:
            theme_def = ThemeDefinition(
                theme=theme_name,
                grounds=[396],
                walls=[1498],
                decorations=[2148],
                monsters=["Demon", "Skeleton", "Crypt Warden"],
            )

        self._cache[key] = theme_def
        return theme_def

    def resolve_multi(self, theme_names: List[str]) -> ThemeDefinition:
        """
        Resolve multiple theme names and merge their definitions.

        This is used for hybrid themes like "Issavi + Roshamuul".

        Args:
            theme_names: List of theme names to merge.

        Returns:
            Merged ThemeDefinition.
        """
        combined = ThemeDefinition(
            theme="+".join(t.lower().replace(" ", "_") for t in theme_names),
            grounds=[],
            walls=[],
            decorations=[],
            monsters=[],
        )

        for name in theme_names:
            td = self.resolve(name)
            # Deduplicate while preserving order
            for g in td.grounds:
                if g not in combined.grounds:
                    combined.grounds.append(g)
            for w in td.walls:
                if w not in combined.walls:
                    combined.walls.append(w)
            for d in td.decorations:
                if d not in combined.decorations:
                    combined.decorations.append(d)
            for m in td.monsters:
                if m not in combined.monsters:
                    combined.monsters.append(m)

        return combined

    # ------------------------------------------------------------------
    # BaseGenerator interface
    # ------------------------------------------------------------------

    def generate(
        self,
        world: WorldModel,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorldModel:
        """
        Resolve theme from context and add a region to the world.

        Args:
            world: WorldModel to populate (adds a Region).
            context: Must contain 'theme' key. Optional 'x', 'y', 'z'.

        Returns:
            WorldModel with a region added.
        """
        if context is None:
            context = {}
        theme_name = context.get("theme", "generic")
        theme_def = self.resolve(theme_name)

        # Add a region to the world for this theme
        region_name = context.get("region_name", f"region_{theme_def.theme}")
        from core.world import Region

        region = Region(
            name=region_name,
            theme=theme_def.theme,
            min_level=context.get("min_level", 1),
            max_level=context.get("max_level", 9999),
        )
        world.add_region(region)

        # Store theme definition in context so downstream generators can use it
        context["theme_def"] = theme_def
        return world

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_from_json(self, key: str) -> Optional[ThemeDefinition]:
        """Try to load a theme definition from a JSON template file."""
        # Normalize key to filename: 'soul_war' -> 'soulwar'
        filename_key = key.replace("_", "")
        json_path = self._template_dir / f"{filename_key}.json"

        if not json_path.exists():
            # Also try the key as-is
            json_path = self._template_dir / f"{key}.json"

        if not json_path.exists():
            return None

        try:
            import json

            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return ThemeDefinition.from_dict(data)
        except (json.JSONDecodeError, IOError):
            return None
