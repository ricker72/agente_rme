from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class SearchResult:
    """A single search result from the blueprint search."""

    blueprint: Dict[str, Any]
    relevance: float  # 0.0 to 1.0
    match_reasons: List[str] = field(default_factory=list)
    matched_keywords: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.blueprint.get("name", "unknown"),
            "category": self.blueprint.get("category", "unknown"),
            "theme": self.blueprint.get("theme", "unknown"),
            "relevance": self.relevance,
            "match_reasons": self.match_reasons,
            "matched_keywords": list(self.matched_keywords),
        }


@dataclass
class SearchQuery:
    """Parsed search query with extracted intent, categories, themes, and constraints."""

    raw: str
    categories: Set[str] = field(default_factory=set)
    themes: Set[str] = field(default_factory=set)
    size_keywords: Set[str] = field(default_factory=set)
    features: Set[str] = field(default_factory=set)
    negative: Set[str] = field(default_factory=set)
    keywords: List[str] = field(default_factory=list)


class BlueprintSearch:
    """
    Semantic search engine for blueprint library.

    Accepts natural language queries and returns ranked blueprint matches.

    Usage:
        search = BlueprintSearch()
        search.load_blueprints("data/blueprints/")
        results = search.search("Busca un templo Issavi grande")
        for r in results:
            print(r.blueprint["name"], r.relevance)
    """

    # Keyword → category mapping for Spanish and English
    CATEGORY_KEYWORDS = {
        # Spanish
        "ciudad": "city",
        "ciudades": "city",
        "city": "city",
        "templo": "temple",
        "templos": "temple",
        "temple": "temple",
        "depot": "depot",
        "depósito": "depot",
        "deposito": "depot",
        "locker": "depot",
        "mercado": "market",
        "market": "market",
        "plaza": "market",
        "comercio": "market",
        "camino": "road",
        "carretera": "road",
        "road": "road",
        "calle": "road",
        "puente": "bridge",
        "bridge": "bridge",
        "boss": "boss_room",
        "boss_room": "boss_room",
        "arena": "boss_room",
        "hunt": "hunt",
        "caza": "hunt",
        "hunting": "hunt",
        "cacería": "hunt",
        # Structure types
        "casa": "housing",
        "edificio": "housing",
        "building": "housing",
        "muralla": "wall",
        "wall": "wall",
        "muro": "wall",
        "torre": "tower",
        "tower": "tower",
        "puerta": "gate",
        "gate": "gate",
        "entrada": "gate",
    }

    # Size descriptors
    SIZE_KEYWORDS = {
        "grande",
        "large",
        "big",
        "enorme",
        "huge",
        "gigante",
        "pequeño",
        "pequeno",
        "small",
        "tiny",
        "chico",
        "mediano",
        "medium",
        "mid",
        "compacto",
        "compact",
    }

    # Theme/style keywords
    THEME_KEYWORDS = {
        "issavi": "issavi",
        "roshamuul": "roshamuul",
        "rosha": "roshamuul",
        "thais": "thais",
        "venore": "venore",
        "carlin": "carlin",
        "ankrahmun": "ankrahmun",
        "yalahar": "yalahar",
        "corruption": "corruption",
        "jungle": "jungle",
        "jungla": "jungle",
        "ice": "ice",
        "hielo": "ice",
        "oriental": "issavi",
        "desert": "ankrahmun",
        "desierto": "ankrahmun",
        "dark": "roshamuul",
        "oscuro": "roshamuul",
        "prison": "roshamuul",
        "prisión": "roshamuul",
        "bosque": "jungle",
        "forest": "jungle",
    }

    def __init__(self):
        self._blueprints: Dict[
            str, List[Dict[str, Any]]
        ] = {}  # category → [blueprints]
        self._all_blueprints: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load_blueprints(self, directory: str | Path) -> int:
        """Load all blueprint JSON files from a directory tree. Returns count loaded."""
        base = Path(directory)
        if not base.exists():
            return 0

        count = 0
        for f in base.rglob("*.json"):
            try:
                bp = json.loads(f.read_text(encoding="utf-8"))
                category = bp.get("category", "unknown").lower()
                self._blueprints.setdefault(category, []).append(bp)
                self._all_blueprints.append(bp)
                count += 1
            except (json.JSONDecodeError, KeyError):
                pass

        return count

    def register(self, blueprint: Dict[str, Any]) -> None:
        """Register a single blueprint programmatically."""
        category = blueprint.get("category", "unknown").lower()
        self._blueprints.setdefault(category, []).append(blueprint)
        self._all_blueprints.append(blueprint)

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Search blueprints using a natural language query.

        Examples:
            "Busca un templo Issavi grande"
            "Quiero un puente estilo roshamuul pequeño"
            "Mercado con NPCs"
            "boss room end game"
        """
        parsed = self._parse_query(query)
        candidates = self._get_candidates(parsed)
        results = self._rank(candidates, parsed)

        return results[:top_k]

    def search_by_category(
        self, category: str, theme: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Direct lookup by category, optionally filtered by theme."""
        bps = self._blueprints.get(category.lower(), [])
        if theme:
            bps = [bp for bp in bps if bp.get("theme", "").lower() == theme.lower()]
        return bps

    def list_categories(self) -> List[str]:
        """Return all known blueprint categories."""
        return sorted(self._blueprints.keys())

    def category_summary(self) -> Dict[str, int]:
        """Return count per category."""
        return {k: len(v) for k, v in self._blueprints.items()}

    # ------------------------------------------------------------------
    # Query parsing
    # ------------------------------------------------------------------

    def _parse_query(self, query: str) -> SearchQuery:
        """Parse a natural language query into structured search intent."""
        lower = query.lower()
        words = lower.split()

        result = SearchQuery(raw=query, keywords=words)

        # Extract categories
        for word in words:
            if word in self.CATEGORY_KEYWORDS:
                result.categories.add(self.CATEGORY_KEYWORDS[word])

        # Extract themes
        for word in words:
            if word in self.THEME_KEYWORDS:
                result.themes.add(self.THEME_KEYWORDS[word])

        # Extract size constraints
        result.size_keywords = {w for w in words if w in self.SIZE_KEYWORDS}

        # Extract features mentioned
        feature_words = {
            "npc",
            "npcs",
            "altar",
            "spawns",
            "chest",
            "cofre",
            "torch",
            "antorcha",
            "fountain",
            "fuente",
            "stairs",
            "escaleras",
            "balcón",
            "balcony",
            "reward",
            "recompensa",
        }
        result.features = {w for w in words if w in feature_words}

        # Extract negative constraints (words after "sin", "no")
        negative_flag = False
        for word in words:
            if word in ("sin", "no", "not"):
                negative_flag = True
                continue
            if negative_flag:
                result.negative.add(word)
                negative_flag = False

        return result

    # ------------------------------------------------------------------
    # Candidate selection
    # ------------------------------------------------------------------

    def _get_candidates(self, parsed: SearchQuery) -> List[Dict[str, Any]]:
        """Get candidate blueprints matching the parsed query."""
        candidates: List[Dict[str, Any]] = []

        # Priority: category-filtered first, then all
        if parsed.categories:
            for cat in parsed.categories:
                candidates.extend(self._blueprints.get(cat, []))
        else:
            candidates = list(self._all_blueprints)

        # Deduplicate
        seen = set()
        unique = []
        for bp in candidates:
            name = bp.get("name", id(bp))
            if name not in seen:
                seen.add(name)
                unique.append(bp)

        return unique

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def _rank(
        self, candidates: List[Dict[str, Any]], parsed: SearchQuery
    ) -> List[SearchResult]:
        """Rank candidates by relevance to the parsed query."""
        results: List[SearchResult] = []

        for bp in candidates:
            score = 0.0
            reasons: List[str] = []
            matched_keywords: Set[str] = set()

            name = bp.get("name", "").lower()
            category = bp.get("category", "").lower()
            theme = bp.get("theme", "").lower()
            description = bp.get("description", "").lower()
            tags = [t.lower() for t in bp.get("metadata", {}).get("tags", [])]
            bp.get("metadata", {})
            size = bp.get("size", [0, 0])

            # Category match (highest weight)
            if parsed.categories and category in parsed.categories:
                score += 0.35
                reasons.append(f"Categoría '{category}' coincide")
                matched_keywords.add(category)

            # Theme match
            if parsed.themes and theme in parsed.themes:
                score += 0.25
                reasons.append(f"Tema '{theme}' coincide")
                matched_keywords.add(theme)

            # Size analysis
            area = size[0] * size[1] if len(size) >= 2 else 0
            for sk in parsed.size_keywords:
                if (
                    sk in ("grande", "large", "big", "enorme", "huge", "gigante")
                    and area > 400
                ):
                    score += 0.12
                    reasons.append(f"Tamaño grande ({area} tiles²)")
                    matched_keywords.add(sk)
                elif (
                    sk in ("pequeño", "pequeno", "small", "tiny", "chico")
                    and area <= 200
                ):
                    score += 0.12
                    reasons.append(f"Tamaño pequeño ({area} tiles²)")
                    matched_keywords.add(sk)
                elif sk in ("mediano", "medium", "mid") and 200 < area <= 600:
                    score += 0.12
                    reasons.append(f"Tamaño mediano ({area} tiles²)")
                    matched_keywords.add(sk)

            # Keyword matching in name and description
            query_text = parsed.raw.lower()
            name_overlap = self._word_overlap(query_text, name)
            desc_overlap = self._word_overlap(query_text, description)
            tag_overlap = self._word_overlap(query_text, " ".join(tags))

            score += name_overlap * 0.15
            score += desc_overlap * 0.08
            score += tag_overlap * 0.05

            if name_overlap > 0:
                reasons.append(f"Nombre '{name}' relevante ({name_overlap:.0%})")
                matched_keywords.update(set(query_text.split()) & set(name.split()))

            # Feature matching
            for feat in parsed.features:
                if any(feat in t for t in tags) or feat in description:
                    score += 0.05
                    reasons.append(f"Feature '{feat}' encontrado")
                    matched_keywords.add(feat)

            # Negative filtering (reduce score)
            for neg in parsed.negative:
                if neg in name or neg in description or neg in tags:
                    score -= 0.20

            # Bonus for metadata relevance
            for kw in parsed.keywords:
                if kw in " ".join(tags):
                    score += 0.02

            # Clamp score
            score = max(0.0, min(1.0, score))

            results.append(
                SearchResult(
                    blueprint=bp,
                    relevance=round(score, 4),
                    match_reasons=reasons,
                    matched_keywords=matched_keywords,
                )
            )

        # Sort by relevance descending
        results.sort(key=lambda r: r.relevance, reverse=True)
        return results

    def _word_overlap(self, text: str, target: str) -> float:
        """Compute Jaccard-like word overlap between query text and target."""
        if not target:
            return 0.0
        text_words = set(text.split())
        target_words = set(target.split())
        intersection = text_words & target_words
        if not intersection:
            return 0.0
        return len(intersection) / max(len(text_words), 1)
