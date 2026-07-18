from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .asset_indexer import AssetIndexer, IndexedItem


@dataclass
class ClassificationResult:
    """Result of classifying an item into categories."""

    item: IndexedItem
    primary_category: str
    secondary_categories: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0
    reasoning: str = ""


class AssetClassifier:
    """
    Classifies Tibia items into semantic categories and theme affiliations.

    Categories:
      - ground, wall, decoration, nature, magic, library, furniture,
        container, light_source, tool, weapon, armor, consumable, key,
        quest, teleport, special

    Theme affiliations:
      - issavi, roshamuul, jungle, ice, desert, corruption, tibia_classic,
        darashia, venore, thais, carlin, ankrahmun, yalahar, etc.

    Uses a combination of:
      1. Explicit XML type field
      2. Item name keyword matching
      3. Item ID range heuristics
      4. Theme template cross-referencing
    """

    # ID ranges for quick classification
    ID_RANGES = {
        "ground": [(100, 500), (700, 800), (1200, 1350), (1400, 1550), (3500, 3700)],
        "wall": [(900, 1200), (1500, 1600), (3700, 3900)],
        "decoration": [(1300, 1400), (1600, 3000), (4000, 5000), (5100, 5200)],
        "nature": [(2100, 2300), (2700, 2800), (5000, 5150)],
        "magic": [(2200, 2600), (3100, 3300)],
    }

    # Theme-specific item ranges (approximate)
    THEME_ID_RANGES = {
        "issavi": [(390, 430), (1490, 1510), (2100, 2200), (1800, 1820)],
        "roshamuul": [(395, 410), (1540, 1550), (1730, 1780)],
        "jungle": [(100, 110), (1300, 1310), (2100, 2130), (2700, 2720)],
        "ice": [(700, 720), (780, 800)],
        "desert": [(230, 240), (1280, 1300)],
        "corruption": [(400, 410), (1000, 1010), (2050, 2070)],
    }

    # Theme-specific name patterns
    THEME_NAME_PATTERNS = {
        "issavi": [
            "crystal",
            "sphinx",
            "golden",
            "oriental",
            "temple",
            "marble",
            "holy",
            "sacred",
            "lion",
            "pharaoh",
        ],
        "roshamuul": [
            "prison",
            "dark",
            "grim",
            "corrupted",
            "dread",
            "shadow",
            "nightmare",
            "bone",
            "skull",
            "demon",
        ],
        "jungle": [
            "jungle",
            "tropical",
            "fern",
            "vine",
            "bamboo",
            "swamp",
            "bog",
            "marsh",
            "carnivorous",
            "liana",
        ],
        "ice": [
            "ice",
            "frozen",
            "frost",
            "snow",
            "glacier",
            "crystal ice",
            "winter",
            "arctic",
            "blizzard",
        ],
        "desert": [
            "desert",
            "sand",
            "dune",
            "oasis",
            "palm",
            "cactus",
            "arid",
            "pyramid",
            "mummy",
        ],
        "corruption": [
            "corrupt",
            "void",
            "chaos",
            "twisted",
            "warped",
            "abyssal",
            "nether",
            "cursed",
            "blighted",
            "tainted",
        ],
        "venore": [
            "swamp",
            "marsh",
            "bog",
            "reed",
            "peat",
            "damp",
            "mold",
            "fungus",
        ],
        "thais": [
            "stone",
            "cobble",
            "medieval",
            "castle",
            "fort",
            "knight",
            "armor",
            "sword",
            "shield",
        ],
    }

    # Furniture sub-classification
    FURNITURE_NAMES = {
        "table",
        "chair",
        "stool",
        "bench",
        "bed",
        "throne",
        "cabinet",
        "wardrobe",
        "dresser",
        "nightstand",
        "counter",
        "desk",
        "shelf",
        "rack",
        "drawer",
        "sofa",
        "couch",
        "armchair",
        "carpet",
        "rug",
    }

    LIGHT_SOURCE_NAMES = {
        "torch",
        "lamp",
        "lantern",
        "candle",
        "candelabra",
        "chandelier",
        "sconce",
        "brazier",
        "fire",
    }

    def __init__(self, indexer: Optional[AssetIndexer] = None):
        self.indexer = indexer

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, item: IndexedItem) -> ClassificationResult:
        """
        Classify a single item into categories and themes.

        Returns a ClassificationResult with primary/secondary categories.
        """
        name_lower = item.name.lower()
        type_name_lower = item.type_name.lower()

        # Determine primary category
        primary = self._determine_primary(item, name_lower, type_name_lower)
        secondaries = self._determine_secondary(item, name_lower, primary)

        confidence = self._compute_confidence(item, primary)

        reasoning = f"Classified as '{primary}' based on "
        if type_name_lower:
            reasoning += f"type='{item.type_name}', "
        reasoning += f"name patterns and ID={item.id}"

        return ClassificationResult(
            item=item,
            primary_category=primary,
            secondary_categories=secondaries,
            confidence=confidence,
            reasoning=reasoning,
        )

    def classify_batch(self, items: List[IndexedItem]) -> List[ClassificationResult]:
        """Classify multiple items."""
        return [self.classify(item) for item in items]

    def get_theme_for_item(self, item: IndexedItem) -> List[str]:
        """
        Determine which themes an item belongs to.

        Returns a list of theme names sorted by relevance.
        """
        themes: List[Tuple[str, float]] = []
        name_lower = item.name.lower()

        for theme, patterns in self.THEME_NAME_PATTERNS.items():
            score = 0.0
            for pattern in patterns:
                if pattern in name_lower:
                    score += 1.0
            if score > 0:
                themes.append((theme, score))

        # ID-range based
        for theme, ranges in self.THEME_ID_RANGES.items():
            for lo, hi in ranges:
                if lo <= item.id <= hi:
                    themes.append((theme, 0.5))
                    break

        # Use theme tags from indexer if available
        if self.indexer:
            idx_item = self.indexer.get_item(item.id)
            if idx_item and idx_item.theme_tags:
                for tag in idx_item.theme_tags:
                    themes.append((tag, 2.0))

        # Deduplicate and sort
        theme_scores: Dict[str, float] = {}
        for theme, score in themes:
            theme_scores[theme] = max(theme_scores.get(theme, 0), score)

        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        return [t for t, _ in sorted_themes]

    def get_items_by_theme(
        self, theme: str, category: Optional[str] = None
    ) -> List[int]:
        """
        Get item IDs that belong to a theme, optionally filtered by category.

        If an indexer is available, uses its theme data. Otherwise falls back
        to ID-range and name-pattern heuristics.
        """
        if self.indexer and theme in self.indexer._theme_items:
            ids = list(self.indexer._theme_items[theme])
            if category and self.indexer:
                ids = [
                    i
                    for i in ids
                    if self.indexer.get_item(i)
                    and self.indexer.get_item(i).category == category
                ]
            return ids

        # Fallback: ID ranges
        ids = set()
        ranges = self.THEME_ID_RANGES.get(theme, [])
        for lo, hi in ranges:
            ids.update(range(lo, hi + 1))

        if category and self.indexer:
            ids = {
                i
                for i in ids
                if self.indexer.get_item(i)
                and self.indexer.get_item(i).category == category
            }

        return sorted(ids)

    def similar_categories(self, category: str) -> List[str]:
        """
        Get categories that are compatible/complementary to the given one.

        Example:
            'ground' → ['nature', 'decoration']
            'wall' → ['decoration', 'light_source']
        """
        compat = {
            "ground": ["nature", "decoration", "ground"],
            "wall": ["decoration", "light_source", "wall", "ground"],
            "decoration": ["ground", "wall", "nature", "light_source", "furniture"],
            "nature": ["ground", "decoration", "nature"],
            "magic": ["decoration", "light_source", "magic"],
            "library": ["furniture", "decoration", "library"],
            "furniture": ["ground", "decoration", "wall", "furniture"],
            "light_source": ["wall", "ground", "decoration", "light_source"],
            "container": ["ground", "furniture", "decoration", "container"],
        }
        return compat.get(category, ["decoration", "ground"])

    # ------------------------------------------------------------------
    # Internal classification
    # ------------------------------------------------------------------

    def _determine_primary(
        self, item: IndexedItem, name_lower: str, type_lower: str
    ) -> str:
        """Determine the primary category for an item."""
        # 1. Explicit type from XML
        if type_lower == "ground":
            return "ground"
        if type_lower == "container":
            return "container"
        if type_lower == "key":
            return "key"
        if type_lower in ("magicfield", "rune"):
            return "magic"

        # 2. Weapon/Armor detection
        if item.weapon_type or item.attack_value > 0:
            return "weapon"
        if item.armor_value > 0:
            return "armor"

        # 3. Item name patterns
        if any(kw in name_lower for kw in self.indexer.GROUND_KEYWORDS if self.indexer):
            return "ground"
        if any(kw in name_lower for kw in self.indexer.WALL_KEYWORDS if self.indexer):
            return "wall"
        if any(kw in name_lower for kw in self.indexer.MAGIC_KEYWORDS if self.indexer):
            return "magic"
        if any(
            kw in name_lower for kw in self.indexer.LIBRARY_KEYWORDS if self.indexer
        ):
            return "library"
        if any(kw in name_lower for kw in self.indexer.NATURE_KEYWORDS if self.indexer):
            return "nature"

        # 4. Furniture
        if any(furn in name_lower for furn in self.FURNITURE_NAMES):
            return "furniture"

        # 5. Light sources
        if any(ls in name_lower for ls in self.LIGHT_SOURCE_NAMES):
            return "light_source"

        # 6. Consumables (potions, food)
        if "potion" in name_lower or "fluid" in type_lower:
            return "consumable"

        # 7. ID range fallback
        for category, ranges in self.ID_RANGES.items():
            for lo, hi in ranges:
                if lo <= item.id <= hi:
                    return category

        # 8. Type-based default
        if type_lower:
            return type_lower

        return "decoration"

    def _determine_secondary(
        self, item: IndexedItem, name_lower: str, primary: str
    ) -> List[str]:
        """Determine secondary categories for an item."""
        seconds = []

        # Decoration often overlaps with nature/furniture/light_source
        if primary != "nature" and any(
            kw in name_lower
            for kw in (self.indexer.NATURE_KEYWORDS if self.indexer else set())
        ):
            seconds.append("nature")
        if primary != "furniture" and any(
            f in name_lower for f in self.FURNITURE_NAMES
        ):
            seconds.append("furniture")
        if primary != "light_source" and any(
            ls in name_lower for ls in self.LIGHT_SOURCE_NAMES
        ):
            seconds.append("light_source")
        if primary != "magic" and any(
            kw in name_lower
            for kw in (self.indexer.MAGIC_KEYWORDS if self.indexer else set())
        ):
            seconds.append("magic")
        if primary != "decoration" and any(
            kw in name_lower
            for kw in (self.indexer.DECORATION_KEYWORDS if self.indexer else set())
        ):
            seconds.append("decoration")

        return seconds[:2]  # Cap at 2 secondary categories

    def _compute_confidence(self, item: IndexedItem, primary: str) -> float:
        """Compute classification confidence (0.0 to 1.0)."""
        # Higher confidence if the XML type explicitly matches
        type_lower = item.type_name.lower()
        if primary == type_lower:
            return 0.95

        # Weapon/armor detection is high confidence
        if primary in ("weapon", "armor") and (
            item.attack_value > 0 or item.armor_value > 0
        ):
            return 0.90

        # Ground detection by ID range is fairly reliable
        if primary == "ground" and 100 <= item.id <= 500:
            return 0.85

        # Name-based classification has moderate confidence
        name_lower = item.name.lower()
        if any(kw in name_lower for kw in self.GROUND_KEYWORD_LIST()):
            return 0.80

        # ID-range fallback has lower confidence
        for cat, ranges in self.ID_RANGES.items():
            if cat == primary:
                for lo, hi in ranges:
                    if lo <= item.id <= hi:
                        return 0.70

        return 0.60  # Default low confidence

    def GROUND_KEYWORD_LIST(self) -> Set[str]:
        if self.indexer:
            return self.indexer.GROUND_KEYWORDS
        return {"floor", "ground", "grass", "dirt", "sand", "stone"}

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def classification_summary(self, items: List[IndexedItem]) -> Dict[str, int]:
        """Generate a summary of classification counts."""
        counts: Dict[str, int] = {}
        for item in items:
            result = self.classify(item)
            counts[result.primary_category] = counts.get(result.primary_category, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def theme_affiliation_summary(self, items: List[IndexedItem]) -> Dict[str, int]:
        """Generate a summary of theme affiliations."""
        counts: Dict[str, int] = {}
        for item in items:
            themes = self.get_theme_for_item(item)
            for theme in themes:
                counts[theme] = counts.get(theme, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
