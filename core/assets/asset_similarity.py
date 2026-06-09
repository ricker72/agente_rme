from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from .asset_indexer import AssetIndexer, IndexedItem
from .asset_classifier import AssetClassifier


@dataclass
class SimilarItem:
    """A similar item match with a relevance score."""
    item: IndexedItem
    similarity: float  # 0.0 to 1.0
    match_reasons: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return f"{self.item.name} (ID:{self.item.id}) [{self.similarity:.2f}]"


@dataclass
class SimilarityResult:
    """Full similarity search result for a query item."""
    query_item: IndexedItem
    similar_items: List[SimilarItem] = field(default_factory=list)
    query_time_ms: float = 0.0

    def top(self, k: int = 5) -> List[IndexedItem]:
        return [s.item for s in self.similar_items[:k]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": {"id": self.query_item.id, "name": self.query_item.name},
            "results": [
                {
                    "id": s.item.id,
                    "name": s.item.name,
                    "similarity": round(s.similarity, 4),
                    "reasons": s.match_reasons,
                }
                for s in self.similar_items[:10]
            ],
        }


class AssetSimilarity:
    """
    Computes similarity between Tibia items using multiple dimensions.

    Dimensions:
      1. Category match (ground→ground, wall→wall, etc.)
      2. Same theme affiliation
      3. Proximity of item IDs in the same range
      4. Name semantic similarity
      5. Shared attributes (weight, stackable, weapon type)
      6. Visual compatibility (same sprite family)

    Used to answer:
      - "What items are similar to this one?"
      - "What decoration goes well with this wall?"
      - "Find alternatives for item X"
    """

    # Weight factors for each similarity dimension
    WEIGHTS = {
        "category": 0.30,
        "theme": 0.25,
        "id_proximity": 0.10,
        "name_similarity": 0.15,
        "attribute_match": 0.10,
        "visual_family": 0.10,
    }

    # Groups of items that visually belong together
    VISUAL_FAMILIES = {
        "marble": {(390, 430), (1490, 1510)},
        "stone": {(1000, 1200), (1280, 1350)},
        "wood": {(400, 450), (1000, 1010), (1700, 1800)},
        "crystal": {(2100, 2200), (1800, 1850)},
        "dark": {(395, 410), (1540, 1560), (1000, 1005)},
        "nature": {(100, 150), (2100, 2300), (2700, 2800)},
        "metal": {(2400, 2600), (3100, 3300)},
    }

    # Compatible category pairs (decoration that goes with each category)
    COMPATIBLE_DECOR = {
        "ground": ["nature", "decoration", "light_source"],
        "wall": ["light_source", "decoration", "wall"],
        "decoration": ["ground", "wall", "decoration", "light_source", "furniture"],
        "nature": ["nature", "decoration", "ground"],
        "furniture": ["decoration", "light_source", "ground", "furniture"],
        "light_source": ["wall", "ground", "decoration"],
        "library": ["furniture", "decoration", "library"],
    }

    def __init__(self, indexer: Optional[AssetIndexer] = None,
                 classifier: Optional[AssetClassifier] = None):
        self.indexer = indexer or AssetIndexer()
        self.classifier = classifier or AssetClassifier(self.indexer)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_similar(self, item: IndexedItem, limit: int = 20) -> SimilarityResult:
        """
        Find items similar to the given item.

        Args:
            item: The query item.
            limit: Maximum number of results.

        Returns:
            SimilarityResult with ranked similar items.
        """
        import time
        start = time.time()

        candidates = self._get_candidates(item)
        results = []

        for candidate in candidates:
            if candidate.id == item.id:
                continue
            similarity, reasons = self._compute_similarity(item, candidate)
            if similarity > 0.1:  # Minimum threshold
                results.append(SimilarItem(
                    item=candidate,
                    similarity=similarity,
                    match_reasons=reasons,
                ))

        results.sort(key=lambda r: r.similarity, reverse=True)
        elapsed = (time.time() - start) * 1000

        return SimilarityResult(
            query_item=item,
            similar_items=results[:limit],
            query_time_ms=elapsed,
        )

    def find_similar_by_name(self, item_name: str, limit: int = 20) -> Optional[SimilarityResult]:
        """Find items similar to one identified by name."""
        item = self.indexer.get_item_by_name(item_name)
        if item is None:
            return None
        return self.find_similar(item, limit)

    def find_similar_by_id(self, item_id: int, limit: int = 20) -> Optional[SimilarityResult]:
        """Find items similar to one identified by ID."""
        item = self.indexer.get_item(item_id)
        if item is None:
            return None
        return self.find_similar(item, limit)

    def find_compatible(self, item: IndexedItem, category: str, limit: int = 15) -> List[IndexedItem]:
        """
        Find items compatible with this item for a given use.

        Example:
            find_compatible(stone_wall, "decoration") → torches, banners, etc.
        """
        compatible_cats = self.COMPATIBLE_DECOR.get(category, ["decoration"])
        candidates = []
        for cat in compatible_cats:
            candidates.extend(self.indexer.get_items_by_category(cat))

        # Score by theme overlap and visual family
        scored = []
        query_themes = set(self.classifier.get_theme_for_item(item))
        query_family = self._get_visual_family(item.id)

        for c in candidates:
            if c.id == item.id:
                continue
            score = 0.0
            c_themes = set(self.classifier.get_theme_for_item(c))
            c_family = self._get_visual_family(c.id)

            if query_themes & c_themes:
                score += 0.4
            if query_family and query_family == c_family:
                score += 0.3
            if category in (self.classifier.classify(c).primary_category,
                           *self.classifier.classify(c).secondary_categories):
                score += 0.3

            if score > 0:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    def find_alternatives(self, item_id: int, limit: int = 10) -> List[IndexedItem]:
        """
        Find alternative items that can replace the given item.
        Same category, different ID but similar purpose.
        """
        item = self.indexer.get_item(item_id)
        if item is None:
            return []

        classification = self.classifier.classify(item)
        same_category = self.indexer.get_items_by_category(classification.primary_category)

        # Exclude the query item itself
        alternatives = [i for i in same_category if i.id != item_id]

        # Score by theme and visual similarity
        scored = []
        query_themes = set(self.classifier.get_theme_for_item(item))

        for alt in alternatives:
            score = 0.0
            alt_themes = set(self.classifier.get_theme_for_item(alt))

            # Same theme is preferred
            theme_overlap = len(query_themes & alt_themes) / max(len(query_themes | alt_themes), 1)
            score += theme_overlap * 0.6

            # Same visual family
            if self._get_visual_family(item.id) == self._get_visual_family(alt.id):
                score += 0.3

            # ID proximity bonus (items in same range tend to be similar)
            if abs(item.id - alt.id) < 50:
                score += 0.1

            if score > 0:
                scored.append((score, alt))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:limit]]

    # ------------------------------------------------------------------
    # Similarity computation
    # ------------------------------------------------------------------

    def _compute_similarity(self, a: IndexedItem, b: IndexedItem) -> Tuple[float, List[str]]:
        """Compute similarity score between two items. Returns (score, reasons)."""
        reasons: List[str] = []

        # Category similarity
        cat_a = self.classifier.classify(a).primary_category
        cat_b = self.classifier.classify(b).primary_category
        cat_score = 1.0 if cat_a == cat_b else (0.3 if cat_b in self.COMPATIBLE_DECOR.get(cat_a, []) else 0.0)

        # Theme similarity
        themes_a = set(self.classifier.get_theme_for_item(a))
        themes_b = set(self.classifier.get_theme_for_item(b))
        if themes_a and themes_b:
            theme_overlap = len(themes_a & themes_b) / max(len(themes_a | themes_b), 1)
        else:
            theme_overlap = 0.0

        # ID proximity
        id_dist = abs(a.id - b.id)
        id_score = max(0.0, 1.0 - id_dist / 500)  # Decay over 500 IDs

        # Name similarity (simple word overlap)
        words_a = set(a.name.lower().split())
        words_b = set(b.name.lower().split())
        if words_a and words_b:
            name_overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        else:
            name_overlap = 0.0

        # Attribute match
        attr_score = 0.0
        attr_count = 0
        if a.stackable == b.stackable:
            attr_score += 1.0
            attr_count += 1
        if a.weapon_type == b.weapon_type and a.weapon_type:
            attr_score += 1.0
            attr_count += 1
        if a.category == b.category:
            attr_score += 1.0
            attr_count += 1
        attr_score = attr_score / max(attr_count, 1)

        # Visual family
        family_a = self._get_visual_family(a.id)
        family_b = self._get_visual_family(b.id)
        visual_score = 1.0 if (family_a and family_a == family_b) else 0.0

        # Weighted total
        total = (
            cat_score * self.WEIGHTS["category"] +
            theme_overlap * self.WEIGHTS["theme"] +
            id_score * self.WEIGHTS["id_proximity"] +
            name_overlap * self.WEIGHTS["name_similarity"] +
            attr_score * self.WEIGHTS["attribute_match"] +
            visual_score * self.WEIGHTS["visual_family"]
        )

        # Collect reasons
        if cat_score > 0.8:
            reasons.append(f"Misma categoria: {cat_a}")
        elif cat_score > 0:
            reasons.append(f"Categoria compatible: {cat_a} <-> {cat_b}")
        if theme_overlap > 0.3:
            reasons.append(f"Temas compartidos: {themes_a & themes_b}")
        if id_score > 0.8:
            reasons.append(f"IDs cercanos ({a.id} ~ {b.id})")
        if name_overlap > 0.3:
            reasons.append(f"Nombres similares")
        if visual_score > 0:
            reasons.append(f"Misma familia visual: {family_a}")
        if attr_score > 0.5:
            reasons.append(f"Atributos similares")

        return round(total, 4), reasons

    def _get_candidates(self, item: IndexedItem) -> List[IndexedItem]:
        """Get candidate items for similarity comparison."""
        candidates = []

        # Same category first
        classification = self.classifier.classify(item)
        candidates.extend(self.indexer.get_items_by_category(classification.primary_category))

        # Same themes
        themes = self.classifier.get_theme_for_item(item)
        for theme in themes:
            for iid in self.classifier.get_items_by_theme(theme):
                if (c := self.indexer.get_item(iid)) and c not in candidates:
                    candidates.append(c)

        # Similar visual family
        family = self._get_visual_family(item.id)
        if family:
            for other_family, ranges in self.VISUAL_FAMILIES.items():
                if other_family != family:
                    continue
                for lo, hi in ranges:
                    for iid in range(lo, hi + 1):
                        if (c := self.indexer.get_item(iid)) and c not in candidates:
                            candidates.append(c)

        # Nearby IDs
        for offset in range(-50, 51):
            iid = item.id + offset
            if iid > 0 and iid != item.id:
                if (c := self.indexer.get_item(iid)) and c not in candidates:
                    candidates.append(c)

        return candidates[:200]  # Cap candidates for performance

    def _get_visual_family(self, item_id: int) -> Optional[str]:
        """Determine which visual family an item ID belongs to."""
        for family, ranges in self.VISUAL_FAMILIES.items():
            for lo, hi in ranges:
                if lo <= item_id <= hi:
                    return family
        return None

    # ------------------------------------------------------------------
    # Bulk analysis
    # ------------------------------------------------------------------

    def cross_similarity_matrix(self, items: List[IndexedItem],
                                top_k: int = 5) -> Dict[int, List[SimilarItem]]:
        """
        Compute a similarity matrix for a set of items.
        Returns {item_id: [SimilarItem, ...]}.
        """
        matrix: Dict[int, List[SimilarItem]] = {}
        for item in items:
            result = self.find_similar(item, limit=top_k)
            matrix[item.id] = result.similar_items
        return matrix

    def cluster_by_similarity(self, items: List[IndexedItem],
                              threshold: float = 0.5) -> List[List[IndexedItem]]:
        """
        Group items into clusters based on similarity threshold.
        Uses a simple greedy clustering approach.
        """
        remaining = set(item.id for item in items)
        clusters: List[List[IndexedItem]] = []

        while remaining:
            seed_id = remaining.pop()
            seed = self.indexer.get_item(seed_id)
            if seed is None:
                continue

            cluster = [seed]
            result = self.find_similar(seed, limit=len(remaining))
            for sim in result.similar_items:
                if sim.item.id in remaining and sim.similarity >= threshold:
                    remaining.discard(sim.item.id)
                    cluster.append(sim.item)

            clusters.append(cluster)

        return clusters