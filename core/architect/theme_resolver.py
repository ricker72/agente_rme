"""
HITO 15 — AI Architect: Theme Resolver
======================================

Resolves theme names into complete theme definitions including:
    - Grounds (floor tile IDs)
    - Walls (wall tile IDs)
    - Decorations (decorative item IDs)
    - Monsters (spawn pool)
    - Blueprints (compatible building structures)
    - Assets (from AssetRegistry when available)

This module is the "knowledge layer" of the AI Architect: it knows what
materials and creatures belong to each Tibia theme and provides them to
upstream zone/layout planners.

Architecture:
    Prompt
      ↓
    ThemeResolver.resolve("issavi")
      ↓
    ThemeAssets
        ├── grounds: [415, 393, ...]
        ├── walls:   [1495, 1496, ...]
        ├── decorations: [2153, 2117, ...]
        ├── monsters: ["Frazzlemaw", ...]
        ├── blueprints: {temple: {...}, depot: {...}}
        └── metadata: {biome, era, difficulty, ...}

Public API:
    ThemeResolver
    ThemeAssets
    resolve_theme(name) → ThemeAssets
    resolve_themes([...]) → [ThemeAssets, ...]
    merge_themes([...]) → ThemeAssets
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================================================================
# ThemeAssets — value object returned by the resolver
# =============================================================================

@dataclass
class ThemeAssets:
    """
    Complete asset palette for a single theme.

    Used by ZonePlanner / LayoutPlanner to know what tile IDs and creatures
    are valid for a given style.
    """
    name: str
    grounds: List[int] = field(default_factory=list)
    walls: List[int] = field(default_factory=list)
    decorations: List[int] = field(default_factory=list)
    monsters: List[str] = field(default_factory=list)
    blueprints: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def pick_ground(self, index: int = 0) -> int:
        if not self.grounds:
            return 396
        return self.grounds[index % len(self.grounds)]

    def pick_wall(self, index: int = 0) -> int:
        if not self.walls:
            return 1498
        return self.walls[index % len(self.walls)]

    def pick_decoration(self, index: int = 0) -> int:
        if not self.decorations:
            return 2148
        return self.decorations[index % len(self.decorations)]

    def pick_monster(self, level_hint: int = 0) -> str:
        if not self.monsters:
            return "Demon"
        return self.monsters[level_hint % len(self.monsters)]

    def blueprint_for(self, structure_type: str) -> Optional[Dict[str, Any]]:
        return self.blueprints.get(structure_type)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "grounds": self.grounds,
            "walls": self.walls,
            "decorations": self.decorations,
            "monsters": self.monsters,
            "blueprints": list(self.blueprints.keys()),
            "metadata": self.metadata,
        }


# =============================================================================
# Built-in theme knowledge (used as the last fallback if no JSON / registry)
# =============================================================================

BUILTIN_THEMES: Dict[str, Dict[str, Any]] = {
    "issavi": {
        "grounds": [415, 393, 421, 103, 102],
        "walls": [1495, 1496, 1497, 1498, 112],
        "decorations": [2153, 2117, 1803, 1700, 1703, 1810],
        "monsters": [
            "Frazzlemaw", "Sphinx", "Cloak Of Terror",
            "Crypt Warden", "Priestess", "Vexclaw", "Guzzlemaw",
        ],
        "metadata": {
            "biome": "desert",
            "era": "ancient",
            "difficulty": "hard",
            "level_range": [250, 600],
            "description": "Ancient Egyptian-inspired desert ruins with sandstone temples",
            "blueprint_quirks": ["wide plazas", "sandstone columns", "obelisks"],
        },
    },
    "roshamuul": {
        "grounds": [1053, 1056, 1057, 447, 231, 358],
        "walls": [1500, 1501, 1502, 1349, 1350, 1351, 118],
        "decorations": [2150, 2151, 2152, 2153, 2042, 1948, 1710, 1713],
        "monsters": [
            "Demon", "Nightmare", "Vampire", "Guzzlemaw",
            "Cloak Of Terror", "Crypt Warden", "Frazzlemaw",
        ],
        "metadata": {
            "biome": "nightmare",
            "era": "medieval",
            "difficulty": "hard",
            "level_range": [300, 700],
            "description": "Dark nightmare realm with twisted stone formations",
            "blueprint_quirks": ["dark ambiance", "lava veins", "twisted pillars"],
        },
    },
    "soul_war": {
        "grounds": [514, 513, 516, 517, 518],
        "walls": [1504, 1505, 1506, 1507],
        "decorations": [2155, 2156, 2157, 2158, 2159],
        "monsters": [
            "Lizard Dragon", "Dragon Lord", "Grim Reaper",
            "Demon", "Nightmare", "Shrieker",
        ],
        "metadata": {
            "biome": "nether",
            "era": "ancient",
            "difficulty": "epic",
            "level_range": [400, 800],
            "description": "Soul War contested battleground with hellish atmosphere",
            "blueprint_quirks": ["gothic arches", "soul wells", "battle remnants"],
        },
    },
    "soulwar": {
        "grounds": [514, 513, 516, 517, 518],
        "walls": [1504, 1505, 1506, 1507],
        "decorations": [2155, 2156, 2157, 2158, 2159],
        "monsters": [
            "Lizard Dragon", "Dragon Lord", "Grim Reaper",
            "Demon", "Nightmare", "Shrieker",
        ],
        "metadata": {
            "biome": "nether",
            "era": "ancient",
            "difficulty": "epic",
            "level_range": [400, 800],
            "description": "Soul War contested battleground",
            "blueprint_quirks": ["gothic arches", "soul wells"],
        },
    },
    "library": {
        "grounds": [396, 397, 398, 399, 400],
        "walls": [1498, 1499, 1503, 1510],
        "decorations": [2148, 2149, 2154, 2160, 2161],
        "monsters": [
            "Sphinx", "Gargoyle", "Hydra", "Demon",
            "Skeleton", "Crypt Warden", "Warlock",
        ],
        "metadata": {
            "biome": "arcane",
            "era": "medieval",
            "difficulty": "hard",
            "level_range": [200, 500],
            "description": "Arcane library with magical tomes and summoning circles",
            "blueprint_quirks": ["bookshelves", "scrolls", "teleporters"],
        },
    },
    "yalahar": {
        "grounds": [450, 451, 452, 453, 454],
        "walls": [1511, 1512, 1513, 1514],
        "decorations": [2162, 2163, 2164, 2165],
        "monsters": [
            "Gargoyle", "Lizard Dragon", "Warlock", "Demon",
            "Vampire", "Grim Reaper",
        ],
        "metadata": {
            "biome": "exotic_urban",
            "era": "modern",
            "difficulty": "extreme",
            "level_range": [350, 700],
            "description": "Exotic urban quarters with magical industry",
            "blueprint_quirks": ["tiled mosaics", "crystal lamps", "infrastructure"],
        },
    },
    "falcon": {
        "grounds": [428, 429, 430, 431, 432],
        "walls": [1507, 1508, 1509, 1515],
        "decorations": [2158, 2159, 2160, 2166, 2167],
        "monsters": [
            "Falcon", "Guzzlemaw", "Vexclaw", "Lizard Dragon",
            "Demon", "Hero",
        ],
        "metadata": {
            "biome": "mountain",
            "era": "medieval",
            "difficulty": "extreme",
            "level_range": [400, 700],
            "description": "Mountain fortress with eagle motifs",
            "blueprint_quirks": ["eagle statues", "stone battlements", "watchtowers"],
        },
    },
    "cobra": {
        "grounds": [514, 513, 516, 517, 518],
        "walls": [1504, 1505, 1506, 1507],
        "decorations": [2155, 2156, 2157, 2168, 2169],
        "monsters": [
            "Cobra", "Vexclaw", "Shrieker", "Snake",
            "Lizard Dragon", "Warlock",
        ],
        "metadata": {
            "biome": "swamp",
            "era": "medieval",
            "difficulty": "extreme",
            "level_range": [300, 600],
            "description": "Venomous cobra-themed dungeon with serpent motifs",
            "blueprint_quirks": ["serpent statues", "poison pools", "altar rooms"],
        },
    },
    "ice": {
        "grounds": [670, 671, 672, 673, 674],
        "walls": [1520, 1521, 1522],
        "decorations": [2170, 2171, 2172],
        "monsters": [
            "Frost Dragon", "Ice Witch", "Yeti",
            "Frost Giant", "Polar Bear",
        ],
        "metadata": {
            "biome": "arctic",
            "era": "modern",
            "difficulty": "extreme",
            "level_range": [300, 600],
            "description": "Frozen tundra with crystalline structures",
            "blueprint_quirks": ["ice walls", "frozen rivers", "auroras"],
        },
    },
    "jungle": {
        "grounds": [440, 441, 442, 443, 444],
        "walls": [1530, 1531, 1532],
        "decorations": [2180, 2181, 2182, 2183, 2184],
        "monsters": [
            "Corym", "Feverish Citizen", "Leaf Golem",
            "Tigrex", "Cave Rat", "Spider",
        ],
        "metadata": {
            "biome": "tropical",
            "era": "modern",
            "difficulty": "hard",
            "level_range": [200, 500],
            "description": "Lush jungle with hidden ruins",
            "blueprint_quirks": ["vegetation overgrowth", "stone ruins", "rope bridges"],
        },
    },
    "thais": {
        "grounds": [351, 352, 353, 354],
        "walls": [1085, 1086, 1087],
        "decorations": [2190, 2191, 2192],
        "monsters": [
            "Rat", "Cave Rat", "Spider", "Troll",
            "Cyclops", "Orc", "Minotaur",
        ],
        "metadata": {
            "biome": "temperate",
            "era": "medieval",
            "difficulty": "easy",
            "level_range": [1, 80],
            "description": "Human kingdom capital with classic medieval style",
            "blueprint_quirks": ["cobblestone roads", "thatched roofs", "plazas"],
        },
    },
    "venore": {
        "grounds": [360, 361, 362, 363],
        "walls": [1090, 1091, 1092],
        "decorations": [2195, 2196, 2197],
        "monsters": [
            "Troll", "Orc", "Cyclops", "Spider",
            "Dwarf", "Minotaur",
        ],
        "metadata": {
            "biome": "desert_city",
            "era": "medieval",
            "difficulty": "easy",
            "level_range": [1, 50],
            "description": "Trade capital with canals and merchant quarters",
            "blueprint_quirks": ["canals", "warehouses", "merchant stalls"],
        },
    },
    "ankrahmun": {
        "grounds": [480, 481, 482, 483],
        "walls": [1540, 1541, 1542],
        "decorations": [2200, 2201, 2202],
        "monsters": [
            "Crocodile", "Mummy", "Scarab",
            "Tomb Servant", "Ghoul", "Vampire",
        ],
        "metadata": {
            "biome": "desert_ruins",
            "era": "ancient",
            "difficulty": "medium",
            "level_range": [50, 200],
            "description": "Ancient Egyptian port-city with tombs",
            "blueprint_quirks": ["pyramids", "obelisks", "tombs"],
        },
    },
    "generic": {
        "grounds": [396],
        "walls": [1498],
        "decorations": [2148],
        "monsters": ["Demon", "Skeleton", "Crypt Warden"],
        "metadata": {
            "biome": "generic",
            "era": "modern",
            "difficulty": "medium",
            "level_range": [1, 200],
            "description": "Generic theme for unspecified maps",
            "blueprint_quirks": [],
        },
    },
}


# =============================================================================
# Theme knowledge container
# =============================================================================

# The default blueprint skeleton used when no BlueprintRegistry is wired in.
DEFAULT_BPRINT_SKELETON = {
    "temple": {
        "structure_type": "temple",
        "min_size": 8,
        "max_size": 14,
        "components": ["altar", "pillar", "blessing_zone"],
    },
    "depot": {
        "structure_type": "depot",
        "min_size": 6,
        "max_size": 10,
        "components": ["chest", "locker", "depot_chest"],
    },
    "market": {
        "structure_type": "market",
        "min_size": 8,
        "max_size": 12,
        "components": ["stall", "fountain", "vendor_npc"],
    },
    "residential": {
        "structure_type": "residential",
        "min_size": 6,
        "max_size": 10,
        "components": ["house_walls", "door", "bed", "table"],
    },
    "boss_room": {
        "structure_type": "boss_room",
        "min_size": 12,
        "max_size": 20,
        "components": ["boss_spawn", "altar", "ritual_circles", "loot_chest"],
    },
    "treasure_room": {
        "structure_type": "treasure_room",
        "min_size": 6,
        "max_size": 10,
        "components": ["chest", "rare_loot", "trap"],
    },
    "hunt_zone": {
        "structure_type": "hunt_zone",
        "min_size": 16,
        "max_size": 30,
        "components": ["spawn_points", "ground", "corridors"],
    },
    "quest_room": {
        "structure_type": "quest_room",
        "min_size": 6,
        "max_size": 10,
        "components": ["npc", "quest_marker", "reward"],
    },
}


# =============================================================================
# Theme Resolver
# =============================================================================

class ThemeResolver:
    """
    Resolves a theme name (or a list of theme names) to a complete ThemeAssets
    object ready to be consumed by the ZonePlanner.

    Priority when resolving a single theme:
        1. AssetRegistry overrides (if supplied)
        2. JSON template files in `templates_dir`
        3. Built-in registry
        4. Generic fallback

    When resolving multiple themes, all are merged into a single ThemeAssets
    (de-duplicated, with the harder difficulty preserved).

    Usage:
        resolver = ThemeResolver()
        theme = resolver.resolve("issavi")
        print(theme.grounds)
        print(theme.monsters)
    """

    # Theme alias normalization map
    _ALIASES: Dict[str, str] = {
        "soul war": "soul_war",
        "soulwar": "soul_war",
        "issavi temple": "issavi",
        "issavi_temple": "issavi",
        "roshamuul dungeon": "roshamuul",
        "roshamuul_dungeon": "roshamuul",
        "ankrahmun ruins": "ankrahmun",
        "carlin": "thais",
        "edron": "thais",
        "darashia": "ankrahmun",
        "port hope": "venore",
        "kazordoon": "thais",
        "ab'dendriel": "jungle",
        "ab dendriel": "jungle",
        "svargrond": "ice",
        "liberty bay": "thais",
    }

    def __init__(
        self,
        templates_dir: Optional[str] = None,
        asset_registry: Optional[Any] = None,
        blueprint_registry: Optional[Any] = None,
    ):
        """
        Args:
            templates_dir: Path to JSON templates directory. Defaults to
                           `templates/` at the project root.
            asset_registry: Optional AssetRegistry for cross-checking item IDs.
            blueprint_registry: Optional BlueprintRegistry for theme-specific
                                building templates.
        """
        if templates_dir is None:
            self.templates_dir = (
                Path(__file__).resolve().parent.parent.parent / "templates"
            )
        else:
            self.templates_dir = Path(templates_dir)
        self.asset_registry = asset_registry
        self.blueprint_registry = blueprint_registry
        self._cache: Dict[str, ThemeAssets] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(self, theme_name: str) -> ThemeAssets:
        """
        Resolve a single theme name to a ThemeAssets.

        Resolution priority:
            1. Cache
            2. JSON template (templates/<name>.json), merged with built-in metadata
            3. Built-in registry (BUILTIN_THEMES)
            4. Generic fallback
        """
        key = self._normalize(theme_name)
        if key in self._cache:
            return self._cache[key]

        # Try JSON template first; merge with built-in for missing fields
        json_data = self._load_json_data(key)
        builtin = BUILTIN_THEMES.get(key)
        if json_data is not None:
            # Start from the built-in (rich metadata) and overlay JSON data
            base = dict(builtin) if builtin else {"metadata": {}}
            merged = {**base, **json_data}
            # Ensure metadata from built-in is preserved if JSON lacks it
            if builtin and "metadata" in builtin and "metadata" not in json_data:
                merged["metadata"] = builtin["metadata"]
            theme_assets = self._from_builtin(key, merged)
        elif builtin is not None:
            theme_assets = self._from_builtin(key, builtin)
        else:
            # Last resort: generic theme, named after the input
            theme_assets = self._from_builtin(
                key, {**BUILTIN_THEMES["generic"], "metadata": {
                    **BUILTIN_THEMES["generic"]["metadata"],
                    "description": f"Auto-generated theme for '{theme_name}'",
                }},
            )

        # Cross-validate / augment with AssetRegistry
        if self.asset_registry is not None:
            theme_assets = self._augment_with_assets(theme_assets)

        # Attach blueprint skeleton (or theme-specific blueprints if available)
        theme_assets.blueprints = self._build_blueprints(key)

        self._cache[key] = theme_assets
        return theme_assets

    def resolve_all(self, theme_names: List[str]) -> List[ThemeAssets]:
        """Resolve multiple theme names; preserves order, de-duplicates aliases."""
        seen: Dict[str, ThemeAssets] = {}
        for name in theme_names:
            key = self._normalize(name)
            if key not in seen:
                seen[key] = self.resolve(name)
        return list(seen.values())

    def merge(self, theme_names: List[str]) -> ThemeAssets:
        """
        Merge multiple themes into a single ThemeAssets.

        The first theme in the list is treated as the "primary" theme.
        Grounds, walls, decorations, and monsters are de-duplicated while
        preserving order; the harder difficulty wins.
        """
        if not theme_names:
            return self.resolve("generic")
        if len(theme_names) == 1:
            return self.resolve(theme_names[0])

        primary = self.resolve(theme_names[0])
        rest = [self.resolve(n) for n in theme_names[1:]]

        merged_name = "+".join(self._normalize(n) for n in theme_names)
        merged_grounds: List[int] = []
        merged_walls: List[int] = []
        merged_decorations: List[int] = []
        merged_monsters: List[str] = []
        seen_g: set = set()
        seen_w: set = set()
        seen_d: set = set()
        seen_m: set = set()

        for theme in [primary] + rest:
            for g in theme.grounds:
                if g not in seen_g:
                    merged_grounds.append(g)
                    seen_g.add(g)
            for w in theme.walls:
                if w not in seen_w:
                    merged_walls.append(w)
                    seen_w.add(w)
            for d in theme.decorations:
                if d not in seen_d:
                    merged_decorations.append(d)
                    seen_d.add(d)
            for m in theme.monsters:
                if m not in seen_m:
                    merged_monsters.append(m)
                    seen_m.add(m)

        # Pick the harder difficulty
        hardest = self._hardest_difficulty([primary] + rest)

        # Combine metadata
        merged_meta: Dict[str, Any] = dict(primary.metadata)
        merged_meta["biome"] = "+".join(
            t.metadata.get("biome", "generic") for t in [primary] + rest
        )
        merged_meta["difficulty"] = hardest
        merged_meta["merged_from"] = [self._normalize(n) for n in theme_names]
        merged_meta["description"] = (
            f"Hybrid theme merging {', '.join(theme_names)}"
        )

        # Use the primary's level_range as a baseline, widen to the rest
        level_ranges = [t.metadata.get("level_range", [1, 200]) for t in [primary] + rest]
        if level_ranges:
            lo = min(r[0] for r in level_ranges)
            hi = max(r[1] for r in level_ranges)
            merged_meta["level_range"] = [lo, hi]

        merged = ThemeAssets(
            name=merged_name,
            grounds=merged_grounds,
            walls=merged_walls,
            decorations=merged_decorations,
            monsters=merged_monsters,
            blueprints=self._build_blueprints(merged_name),
            metadata=merged_meta,
        )

        return merged

    def list_known_themes(self) -> List[str]:
        """Return a sorted list of theme names known to the resolver."""
        return sorted(BUILTIN_THEMES.keys())

    def has_theme(self, theme_name: str) -> bool:
        """Check if a theme is known (alias-aware)."""
        return self._normalize(theme_name) in BUILTIN_THEMES

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    def _normalize(self, theme_name: str) -> str:
        """Normalize a theme string to the canonical key format."""
        if not theme_name:
            return "generic"
        name = theme_name.strip().lower()
        # Remove any city/dungeon/temple qualifiers
        name = re.sub(r"\s+(city|dungeon|temple|district|quarter|ruins)$", "", name)
        # Replace separators
        name = name.replace("-", "_").replace(" ", "_")
        # Apply alias map
        return self._ALIASES.get(name, name)

    def _load_json_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Try to load raw theme data from a JSON template file."""
        candidates = [
            self.templates_dir / f"{key}.json",
            self.templates_dir / f"{key.replace('_', '')}.json",
        ]
        candidates.append(self.templates_dir / f"{self._ALIASES.get(key, key)}.json")

        for json_path in candidates:
            if json_path.exists():
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError, OSError):
                    continue
        return None

    def _load_from_json(self, key: str) -> Optional[ThemeAssets]:
        """Try to load a theme definition from a JSON template file."""
        data = self._load_json_data(key)
        if data is None:
            return None
        return self._from_builtin(key, data)

    def _from_builtin(self, key: str, data: Dict[str, Any]) -> ThemeAssets:
        """Build a ThemeAssets object from a built-in / JSON data dict."""
        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        return ThemeAssets(
            name=key,
            grounds=list(data.get("grounds", [])),
            walls=list(data.get("walls", [])),
            decorations=list(data.get("decorations", [])),
            monsters=list(data.get("monsters", [])),
            blueprints={},  # filled later
            metadata=metadata,
        )

    def _augment_with_assets(self, theme: ThemeAssets) -> ThemeAssets:
        """
        Use the AssetRegistry to drop any item IDs that are not present
        in the loaded game data (best-effort validation).
        """
        if self.asset_registry is None:
            return theme

        try:
            known_items = set()
            for item_id in self.asset_registry.get_grounds():
                known_items.add(item_id)
            for item_id in self.asset_registry.get_walls():
                known_items.add(item_id)
            for item_id in self.asset_registry.get_decorations():
                known_items.add(item_id)
        except Exception:
            return theme

        if not known_items:
            return theme

        # Filter to only valid IDs; keep at least one for usability
        new_grounds = [g for g in theme.grounds if g in known_items] or theme.grounds[:1]
        new_walls = [w for w in theme.walls if w in known_items] or theme.walls[:1]
        new_decos = [d for d in theme.decorations if d in known_items] or theme.decorations[:1]

        theme.grounds = new_grounds
        theme.walls = new_walls
        theme.decorations = new_decos
        return theme

    def _build_blueprints(self, theme_key: str) -> Dict[str, Dict[str, Any]]:
        """
        Build the blueprint skeleton for this theme.

        If a BlueprintRegistry is wired in, we use any matching blueprints
        (theme-prefixed names like "issavi_temple" → structure_type "temple").
        """
        blueprints: Dict[str, Dict[str, Any]] = {}

        # Start with default skeleton
        for btype, spec in DEFAULT_BPRINT_SKELETON.items():
            blueprints[btype] = dict(spec)

        # Overlay theme-specific blueprints from registry
        if self.blueprint_registry is not None:
            try:
                for btype in list(blueprints.keys()):
                    themed_name = f"{theme_key}_{btype}"
                    bp = self.blueprint_registry.get_blueprint(btype, themed_name)
                    if bp is None:
                        bp = self.blueprint_registry.get_blueprint(btype)
                    if bp is not None:
                        # Merge: registry overrides defaults
                        merged = {**blueprints[btype], **dict(bp)}
                        blueprints[btype] = merged
            except Exception:
                pass

        return blueprints

    @staticmethod
    def _hardest_difficulty(themes: List[ThemeAssets]) -> str:
        order = {
            "easy": 0, "medium": 1, "hard": 2,
            "extreme": 3, "epic": 4, "legendary": 5,
        }
        return max(
            themes,
            key=lambda t: order.get(t.metadata.get("difficulty", "medium"), 1),
        ).metadata.get("difficulty", "medium")


# =============================================================================
# Module-level convenience functions
# =============================================================================

_DEFAULT_RESOLVER: Optional[ThemeResolver] = None


def get_default_resolver() -> ThemeResolver:
    """Return a process-wide default resolver (lazy initialization)."""
    global _DEFAULT_RESOLVER
    if _DEFAULT_RESOLVER is None:
        _DEFAULT_RESOLVER = ThemeResolver()
    return _DEFAULT_RESOLVER


def resolve_theme(name: str) -> ThemeAssets:
    """Shortcut: resolve a theme using the default resolver."""
    return get_default_resolver().resolve(name)


def resolve_themes(names: List[str]) -> List[ThemeAssets]:
    """Shortcut: resolve multiple themes using the default resolver."""
    return get_default_resolver().resolve_all(names)


def merge_themes(names: List[str]) -> ThemeAssets:
    """Shortcut: merge themes using the default resolver."""
    return get_default_resolver().merge(names)
