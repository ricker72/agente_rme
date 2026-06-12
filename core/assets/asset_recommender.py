from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .asset_indexer import AssetIndexer, IndexedItem
from .asset_classifier import AssetClassifier
from .asset_similarity import AssetSimilarity


@dataclass
class Recommendation:
    """A single recommendation with explanation."""

    item: IndexedItem
    score: float
    reason: str
    category: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.item.id,
            "name": self.item.name,
            "score": round(self.score, 4),
            "category": self.category,
            "reason": self.reason,
        }


@dataclass
class RecommendationResult:
    """Complete result from a recommendation query."""

    query: str
    recommendations: List[Recommendation] = field(default_factory=list)
    total_results: int = 0
    interpretation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "interpretation": self.interpretation,
            "total_results": self.total_results,
            "recommendations": [r.to_dict() for r in self.recommendations[:15]],
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class AssetRecommender:
    """
    Intelligent asset recommendation engine for Tibia map creation.

    Answers natural-language questions about which items to use:
      - "¿Qué decoración combina con Issavi?"
      - "¿Qué paredes se parecen a Roshamuul?"
      - "Recomiéndame grounds para una ciudad jungla"
      - "¿Qué antorchas usar para un templo oscuro?"
      - "Monstruos para una hunt nivel 200 en Issavi"

    Uses the full asset intelligence stack:
      Indexer → Classifier → Similarity → Recommender
    """

    def __init__(
        self,
        indexer: Optional[AssetIndexer] = None,
        classifier: Optional[AssetClassifier] = None,
        similarity: Optional[AssetSimilarity] = None,
    ):
        self.indexer = indexer or AssetIndexer()
        self.classifier = classifier or AssetClassifier(self.indexer)
        self.similarity = similarity or AssetSimilarity(self.indexer, self.classifier)

        # Map common query intents to recommendation strategies
        self._intent_map = {
            "decoración": "decorate_for",
            "decoracion": "decorate_for",
            "decorations": "decorate_for",
            "decorar": "decorate_for",
            "combina": "decorate_for",
            "combinan": "decorate_for",
            "paredes": "walls_for",
            "pared": "walls_for",
            "walls": "walls_for",
            "grounds": "grounds_for",
            "suelo": "grounds_for",
            "suelos": "grounds_for",
            "floors": "grounds_for",
            "antorchas": "light_for",
            "luces": "light_for",
            "iluminación": "light_for",
            "light": "light_for",
            "monstruos": "monsters_for",
            "monsters": "monsters_for",
            "creaturas": "monsters_for",
            "hunt": "monsters_for",
            "alternativa": "alternatives_to",
            "alternativas": "alternatives_to",
            "alternatives": "alternatives_to",
            "similar": "similar_to",
            "parecen": "similar_to",
            "parece": "similar_to",
            "similar a": "similar_to",
            "parecido": "similar_to",
        }

    # ------------------------------------------------------------------
    # Public API - Natural language queries
    # ------------------------------------------------------------------

    def recommend(self, query: str, limit: int = 10) -> RecommendationResult:
        """
        Answer a natural language recommendation query.

        Examples:
            recommender.recommend("¿Qué decoración combina con Issavi?")
            recommender.recommend("¿Qué paredes se parecen a Roshamuul?")
            recommender.recommend("Recomiéndame grounds para una ciudad jungla")
        """
        query.lower()
        result = RecommendationResult(query=query)

        # Parse the query intent
        intent, target_theme, target_category = self._parse_query(query)

        if intent is None:
            result.interpretation = "Could not determine intent from query"
            return result

        theme_str = target_theme or "any"
        cat_str = target_category or "any"
        result.interpretation = (
            f"Intent: {intent}, Theme: {theme_str}, Category: {cat_str}"
        )

        # Execute the appropriate recommendation strategy
        strategies = {
            "decorate_for": self._recommend_decorations_for_theme,
            "walls_for": self._recommend_walls_for_theme,
            "grounds_for": self._recommend_grounds_for_theme,
            "light_for": self._recommend_lights_for_theme,
            "monsters_for": self._recommend_monsters_for_theme,
            "alternatives_to": self._recommend_alternatives,
            "similar_to": self._recommend_similar,
        }

        handler = strategies.get(intent, self._generic_recommend)
        recommendations = handler(target_theme, target_category, limit)

        result.recommendations = recommendations
        result.total_results = len(recommendations)

        return result

    # ------------------------------------------------------------------
    # Query parsing
    # ------------------------------------------------------------------

    def _parse_query(
        self, query: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Parse a query into (intent, theme, category).

        Returns:
            (intent_str, theme_str_or_None, category_str_or_None)
        """
        lower = query.lower()

        # Detect intent
        intent = None
        for keyword, intent_name in sorted(
            self._intent_map.items(), key=lambda x: -len(x[0])
        ):
            if keyword in lower:
                intent = intent_name
                break

        # Detect theme
        target_theme = None
        known_themes = list(self.classifier.THEME_NAME_PATTERNS.keys())
        for theme in known_themes:
            if theme in lower:
                target_theme = theme
                break

        # Detect category
        target_category = None
        cat_keywords = {
            "decoración": "decoration",
            "decoracion": "decoration",
            "paredes": "wall",
            "pared": "wall",
            "walls": "wall",
            "suelo": "ground",
            "suelos": "ground",
            "grounds": "ground",
            "piso": "ground",
            "luz": "light_source",
            "antorchas": "light_source",
            "antorcha": "light_source",
            "monstruos": None,
            "monsters": None,
            "hunt": None,
            "caza": None,
            "muebles": "furniture",
            "furniture": "furniture",
            "naturaleza": "nature",
            "nature": "nature",
            "plantas": "nature",
            "estatuas": "decoration",
            "statues": "decoration",
        }
        for keyword, cat in cat_keywords.items():
            if keyword in lower:
                target_category = cat
                break

        # If no explicit category, infer from intent
        if target_category is None:
            infer_map = {
                "decorate_for": "decoration",
                "walls_for": "wall",
                "grounds_for": "ground",
                "light_for": "light_source",
            }
            target_category = infer_map.get(intent, "decoration")

        return intent, target_theme, target_category

    # ------------------------------------------------------------------
    # Recommendation strategies
    # ------------------------------------------------------------------

    def _recommend_decorations_for_theme(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend decorations that match a given theme."""
        items = self.indexer.get_items_by_category("decoration")
        if not items:
            return []

        recs = []
        for item in items:
            score = 0.0
            reasons = []

            item_themes = self.classifier.get_theme_for_item(item)

            if theme and theme in item_themes:
                score += 0.5
                reasons.append(f"Belongs to theme '{theme}'")

            # Bonus for items with explicit theme tags from indexer
            if self.indexer and theme:
                idx_item = self.indexer.get_item(item.id)
                if idx_item and theme in idx_item.theme_tags:
                    score += 0.3

            # Decoration compatibility check
            classification = self.classifier.classify(item)
            if classification.primary_category == "decoration":
                score += 0.1
                reasons.append("Is a decoration item")

            if classification.confidence > 0.7:
                score += 0.05

            if score > 0:
                recs.append(
                    Recommendation(
                        item=item,
                        score=score,
                        reason="; ".join(reasons)
                        if reasons
                        else "General recommendation",
                        category="decoration",
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _recommend_walls_for_theme(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend wall items for a given theme."""
        items = self.indexer.get_items_by_category("wall")
        if not items:
            return []

        recs = []
        for item in items:
            score = 0.0
            reasons = []

            item_themes = self.classifier.get_theme_for_item(item)

            if theme and theme in item_themes:
                score += 0.6
                reasons.append(f"Belongs to theme '{theme}'")

            # Wall items with matching visual family bonus
            family = self.similarity._get_visual_family(item.id)
            if family:
                score += 0.2
                reasons.append(f"Visual family: {family}")

            # Check against ID ranges for the theme
            if theme:
                theme_ranges = self.classifier.THEME_ID_RANGES.get(theme, [])
                for lo, hi in theme_ranges:
                    if lo <= item.id <= hi:
                        score += 0.15
                        reasons.append(f"In {theme} ID range ({lo}-{hi})")
                        break

            if score > 0:
                recs.append(
                    Recommendation(
                        item=item,
                        score=score,
                        reason="; ".join(reasons)
                        if reasons
                        else "General wall recommendation",
                        category="wall",
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _recommend_grounds_for_theme(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend ground tiles for a given theme."""
        items = self.indexer.get_items_by_category("ground")
        if not items:
            return []

        recs = []
        for item in items:
            score = 0.0
            reasons = []

            item_themes = self.classifier.get_theme_for_item(item)

            if theme and theme in item_themes:
                score += 0.6
                reasons.append(f"Belongs to theme '{theme}'")

            # Prefer ground items with high confidence classification
            classification = self.classifier.classify(item)
            if classification.confidence >= 0.8:
                score += 0.15

            # ID range match
            if theme:
                theme_ranges = self.classifier.THEME_ID_RANGES.get(theme, [])
                for lo, hi in theme_ranges:
                    if lo <= item.id <= hi:
                        score += 0.15

            if score > 0:
                recs.append(
                    Recommendation(
                        item=item,
                        score=score,
                        reason="; ".join(reasons)
                        if reasons
                        else "General ground recommendation",
                        category="ground",
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _recommend_lights_for_theme(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend light sources for a given theme."""
        items = self.indexer.get_items_by_category("light_source")
        if not items:
            # Fallback: search in decoration for torch-like items
            items = [
                i
                for i in self.indexer.all_items
                if "torch" in i.name.lower()
                or "lamp" in i.name.lower()
                or "candle" in i.name.lower()
                or "brazier" in i.name.lower()
            ]

        recs = []
        for item in items:
            score = 0.0
            reasons = []

            item_themes = self.classifier.get_theme_for_item(item)

            if theme and theme in item_themes:
                score += 0.5
                reasons.append(f"Belongs to theme '{theme}'")

            # Known light item IDs (torches, lamps)
            known_lights = {2050, 2052, 2054, 2060, 2061, 2062, 2063, 2064, 2066, 1500}
            if item.id in known_lights:
                score += 0.3
                reasons.append("Known light source item")

            if score > 0:
                recs.append(
                    Recommendation(
                        item=item,
                        score=score,
                        reason="; ".join(reasons)
                        if reasons
                        else "General light recommendation",
                        category="light_source",
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _recommend_monsters_for_theme(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend monsters for a given theme."""
        monsters = self.indexer.all_monsters

        recs = []
        for monster in monsters:
            score = 0.0
            reasons = []

            if theme and theme in monster.theme_tags:
                score += 0.7
                reasons.append(f"Belongs to theme '{theme}'")

            if monster.experience > 0:
                score += 0.1
                reasons.append(f"Has {monster.experience} XP")

            if score > 0:
                # Create a synthetic IndexedItem for the recommendation
                item = IndexedItem(
                    id=monster.look_type,
                    name=monster.name,
                    category="monster",
                )
                item.theme_tags = monster.theme_tags
                recs.append(
                    Recommendation(
                        item=item,
                        score=score,
                        reason="; ".join(reasons),
                        category="monster",
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _recommend_alternatives(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend alternative items based on ID or name mentioned in query."""
        # Try to find a specific item mentioned in the query
        # This is a simpler version; the query parsing already happened
        if theme is None:
            return []

        # Search for items matching the theme name directly
        items = self.indexer.search_items(theme, limit=limit)
        recs = []
        for item in items:
            alternatives = self.similarity.find_alternatives(item.id, limit=3)
            for alt in alternatives:
                recs.append(
                    Recommendation(
                        item=alt,
                        score=0.7,
                        reason=f"Alternative to {item.name} (ID:{item.id})",
                        category=item.category,
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _recommend_similar(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Recommend items similar to items in a given theme."""
        if theme is None:
            # Try to find a specific item by the query words
            items = self.indexer.search_items(category or "", limit=5)
        else:
            items = self.indexer.get_items_by_theme(theme)[:5]

        recs = []
        for item in items:
            similar = self.similarity.find_similar(item, limit=3)
            for sim in similar.similar_items:
                recs.append(
                    Recommendation(
                        item=sim.item,
                        score=sim.similarity,
                        reason=f"Similar to {item.name}: {'; '.join(sim.match_reasons)}",
                        category=item.category,
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    def _generic_recommend(
        self, theme: Optional[str], category: Optional[str], limit: int
    ) -> List[Recommendation]:
        """Generic recommendation combining all strategies."""
        recs = []
        if theme:
            for item in self.indexer.get_items_by_theme(theme):
                recs.append(
                    Recommendation(
                        item=item,
                        score=0.5,
                        reason=f"Theme item: {theme}",
                        category=item.category,
                    )
                )

        recs.sort(key=lambda r: r.score, reverse=True)
        return recs[:limit]

    # ------------------------------------------------------------------
    # Convenience methods
    # ------------------------------------------------------------------

    def decorate_for(self, theme: str, limit: int = 10) -> List[Recommendation]:
        """Quick: recommend decorations for a theme."""
        return self._recommend_decorations_for_theme(theme, "decoration", limit)

    def walls_for(self, theme: str, limit: int = 10) -> List[Recommendation]:
        """Quick: recommend walls for a theme."""
        return self._recommend_walls_for_theme(theme, "wall", limit)

    def grounds_for(self, theme: str, limit: int = 10) -> List[Recommendation]:
        """Quick: recommend ground tiles for a theme."""
        return self._recommend_grounds_for_theme(theme, "ground", limit)

    def monsters_for(self, theme: str, limit: int = 10) -> List[Recommendation]:
        """Quick: recommend monsters for a theme."""
        return self._recommend_monsters_for_theme(theme, None, limit)

    def similar_to(self, item_name_or_id: str, limit: int = 10) -> List[Recommendation]:
        """Quick: find items similar to a given item."""
        item = self.indexer.get_item_by_name(item_name_or_id)
        if item is None:
            try:
                item = self.indexer.get_item(int(item_name_or_id))
            except ValueError:
                return []

        if item is None:
            return []

        result = self.similarity.find_similar(item, limit=limit)
        return [
            Recommendation(
                item=s.item,
                score=s.similarity,
                reason="; ".join(s.match_reasons),
                category=self.classifier.classify(s.item).primary_category,
            )
            for s in result.similar_items
        ]

    def full_theme_palette(self, theme: str) -> Dict[str, List[Recommendation]]:
        """
        Generate a complete palette recommendation for a theme.
        Returns dict with keys: grounds, walls, decorations, lights, monsters.
        """
        return {
            "grounds": self.grounds_for(theme),
            "walls": self.walls_for(theme),
            "decorations": self.decorate_for(theme),
            "lights": self._recommend_lights_for_theme(theme, "light_source", 5),
            "monsters": self.monsters_for(theme),
        }

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def load_templates(self, template_dir: str) -> int:
        """Load all JSON theme templates into the indexer."""
        from pathlib import Path

        count = 0
        for f in Path(template_dir).glob("*.json"):
            if f.name == "empty_map":
                continue
            self.indexer.index_template_file(str(f))
            count += 1
        return count
