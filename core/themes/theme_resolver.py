"""
MVP V0.1 — Theme Resolver
Resolves theme names to complete ThemeData structures with grounds, walls, decorations, and monsters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import json


@dataclass
class ThemeData:
    name: str
    grounds: List[int] = field(default_factory=list)
    walls: List[int] = field(default_factory=list)
    decorations: List[int] = field(default_factory=list)
    monsters: List[str] = field(default_factory=list)
    difficulty: str = "medium"
    metadata: Dict = field(default_factory=dict)


class ThemeResolver:
    """
    Resolves theme names to full theme configurations.

    Built-in themes (IssaviTheme, RoshamuulTheme) are backed by template JSON files
    and also provide fallback data if the JSON is unavailable.
    """

    # Fallback built-in theme data (used when JSON files are not available)
    BUILTIN_THEMES: Dict[str, ThemeData] = {
        "issavi": ThemeData(
            name="issavi",
            grounds=[415, 393, 421, 103, 102],
            walls=[1495, 1496, 1497, 112],
            decorations=[2153, 2117, 1803, 1700, 1703],
            monsters=["Frazzlemaw", "Sphinx", "Cloak Of Terror", "Crypt Warden", "Priestess"],
            difficulty="medium",
            metadata={
                "biome": "desert",
                "description": "Ancient Egyptian-inspired desert ruins with sandstone temples",
                "level_range": [250, 600],
                "colors": {"primary": "#D4A574", "secondary": "#E8D5B7", "accent": "#C49000"},
            },
        ),
        "roshamuul": ThemeData(
            name="roshamuul",
            grounds=[447, 231, 358, 105, 106],
            walls=[1349, 1350, 1351, 118],
            decorations=[2153, 2042, 1948, 1710, 1713],
            monsters=["Frazzlemaw", "Cloak Of Terror", "Crypt Warden", "Guzzlemaw"],
            difficulty="hard",
            metadata={
                "biome": "nightmare",
                "description": "Dark nightmare realm with twisted stone formations",
                "level_range": [300, 700],
                "colors": {"primary": "#3A3A4A", "secondary": "#5A4A6A", "accent": "#7A0090"},
            },
        ),
    }

    def __init__(self, templates_dir: Optional[str] = None):
        if templates_dir:
            self.templates_dir = Path(templates_dir)
        else:
            self.templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"

    def resolve(self, theme_name: str) -> ThemeData:
        """
        Resolve a theme name to its full ThemeData.

        Priority: JSON template > Built-in fallback > empty theme
        """
        name = theme_name.lower().strip()

        # Try loading from JSON template
        json_data = self._load_json(name)
        if json_data:
            return self._from_json(name, json_data)

        # Fall back to built-in
        if name in self.BUILTIN_THEMES:
            return self.BUILTIN_THEMES[name]

        # Return empty theme as last resort
        return ThemeData(name=name)

    def resolve_all(self, theme_names: List[str]) -> List[ThemeData]:
        """Resolve multiple theme names."""
        return [self.resolve(name) for name in theme_names]

    def merge_themes(self, themes: List[ThemeData]) -> ThemeData:
        """
        Merge multiple themes into a single hybrid theme.
        Combines grounds, walls, decorations, and monsters from all themes.
        """
        if not themes:
            return ThemeData(name="empty")

        if len(themes) == 1:
            return themes[0]

        merged = ThemeData(
            name="+".join(t.name for t in themes),
            difficulty=self._hardest_difficulty(themes),
        )

        seen_grounds = set()
        seen_walls = set()
        seen_decorations = set()
        seen_monsters = set()

        for theme in themes:
            merged.grounds.extend([g for g in theme.grounds if g not in seen_grounds])
            seen_grounds.update(theme.grounds)

            merged.walls.extend([w for w in theme.walls if w not in seen_walls])
            seen_walls.update(theme.walls)

            merged.decorations.extend([d for d in theme.decorations if d not in seen_decorations])
            seen_decorations.update(theme.decorations)

            merged.monsters.extend([m for m in theme.monsters if m not in seen_monsters])
            seen_monsters.update(theme.monsters)

        # Merge metadata
        merged.metadata = {
            "themes": [t.name for t in themes],
            "biomes": [t.metadata.get("biome", "unknown") for t in themes],
        }

        return merged

    def _hardest_difficulty(self, themes: List[ThemeData]) -> str:
        order = {"easy": 0, "medium": 1, "hard": 2, "extreme": 3}
        return max(themes, key=lambda t: order.get(t.difficulty, 0)).difficulty

    def _load_json(self, theme_name: str) -> Optional[Dict]:
        path = self.templates_dir / f"{theme_name}.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return None

    def _from_json(self, name: str, data: Dict) -> ThemeData:
        return ThemeData(
            name=data.get("theme", name),
            grounds=data.get("grounds", []),
            walls=data.get("walls", []),
            decorations=data.get("decorations", []),
            monsters=data.get("monsters", []),
            difficulty=data.get("metadata", {}).get("difficulty", "medium") if isinstance(data.get("metadata"), dict) else "medium",
            metadata=data.get("metadata", {}),
        )