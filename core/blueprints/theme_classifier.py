"""
HITO 13 — Theme Classifier: clasifica el tema/estilo de un mapa
a partir de la distribucion de tiles, items y estructuras.

Analiza:
  - Tipos de suelo (ground) para determinar el bioma base
  - Tipos de muros y decoraciones para refinar el tema
  - Spawns para detectar tema de hunting
  - Casas/edificios para confirmar tema urbano/ciudad

Soporta temas:
  - issavi (desert/sandstone temple complex)
  - roshamuul (volcanic/wild terrain)
  - temple (religious structures)
  - dungeon (underground maze)
  - city (urban settlement)
  - hunt (spawn-heavy area)
  - yalahar (exotic urban)
  - hybrid (mixed themes)
  - generic (fallback)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ThemeClassifier:
    """Clasifica el tema predominante de un mapa basado en sus tiles e items."""

    # ----------------------------------------------------------------
    # Firmas de temas: mapean tipos de suelo -> tema
    # ----------------------------------------------------------------
    GROUND_SIGNATURES: Dict[str, List[str]] = {
        "issavi": [
            "sandstone_floor",
            "sandstone",
            "sand_floor",
            "desert_ground",
            "sand",
            "dried_earth",
        ],
        "roshamuul": [
            "roshamuul_floor",
            "roshamuul_stone",
            "volcanic_floor",
            "lava_ground",
            "ash_floor",
            "charred_earth",
        ],
        "yalahar": [
            "yalahar_floor",
            "yalahar_stone",
            "exotic_floor",
            "mosaic_floor",
            "patterned_stone",
        ],
        "temple": [
            "polished_stone",
            "marble_floor",
            "temple_floor",
            "holy_ground",
            "sanctuary_floor",
        ],
        "dungeon": [
            "mossy_stone",
            "dungeon_floor",
            "cave_floor",
            "stone_floor",
            "rough_stone",
        ],
        "city": [
            "polished_stone",
            "cobblestone",
            "paved_road",
            "city_floor",
            "urban_ground",
        ],
        "jungle": [
            "jungle_floor",
            "grass_floor",
            "mud_floor",
            "swamp_ground",
            "forest_floor",
        ],
        "ice": [
            "ice_floor",
            "snow_floor",
            "frozen_ground",
            "glacier_floor",
            "frost_ground",
        ],
    }

    # ----------------------------------------------------------------
    # IDs de items por tema (wall IDs, decoration IDs)
    # ----------------------------------------------------------------
    ITEM_SIGNATURES: Dict[str, List[int]] = {
        "temple": [1000, 1001, 1002, 1003, 1004, 1005, 2100, 2101],
        "dungeon": [101, 102, 103, 104, 105, 106, 107],
        "city": [108, 109, 110, 1006, 1007, 1008, 1009],
        "issavi": [2100, 2101, 2102, 2103],
        "roshamuul": [2104, 2105, 1053, 1056],
    }

    # ----------------------------------------------------------------
    # Marcadores de zona (spawn types)
    # ----------------------------------------------------------------
    HUNT_MONSTER_INDICATORS = [
        "dragon",
        "demon",
        "behemoth",
        "hydra",
        "serpent",
        "spider",
        "ghoul",
        "skeleton",
        "vampire",
        "lich",
        "rotworm",
        "troll",
        "ork",
        "minotaur",
        "cyclops",
        "wyrm",
        "warlock",
        "hero",
        "hunter",
        "monk",
        "crypt",
        "necromancer",
        "dragon_lord",
        "frost",
        "fiery",
        "blightwalker",
        "gazer",
        "wyvern",
    ]

    def classify(
        self,
        tiles: Dict[str, int],
        items: Optional[Dict[str, int]] = None,
        spawns: Optional[List[Dict[str, Any]]] = None,
        houses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Clasifica el tema de un mapa.

        Args:
            tiles: Dict {tile_name: count} de la distribucion de tiles.
            items: Dict {item_key: count} de items detectados.
            spawns: Lista de spawns con clave "monster".
            houses: Lista de houses/edificios.

        Returns:
            Dict con:
                - primary_theme: tema principal
                - confidence: 0.0 - 1.0
                - theme_scores: {theme: score} detallado
                - secondary_themes: temas secundarios detectados
                - is_hunt_area: bool
                - is_urban: bool
                - recommended_era: era sugerida
        """
        items = items or {}
        spawns = spawns or []
        houses = houses or []

        scores: Dict[str, float] = {}

        # 1. Puntuar por suelo (ground)
        ground_scores = self._score_grounds(tiles)
        for theme, score in ground_scores.items():
            scores[theme] = scores.get(theme, 0.0) + score

        # 2. Puntuar por items (muros, decoraciones)
        item_scores = self._score_items(items)
        for theme, score in item_scores.items():
            scores[theme] = scores.get(theme, 0.0) + score * 0.5

        # 3. Puntuar por spawns (hunting)
        if spawns:
            hunt_score = self._score_hunt_spawns(spawns)
            scores["hunt"] = scores.get("hunt", 0.0) + hunt_score

        # 4. Puntuar por houses (urbanidad)
        if houses:
            urban_score = min(len(houses) * 5.0, 40.0)
            scores["city"] = scores.get("city", 0.0) + urban_score * 0.3

        # 5. Determinar tema primario
        if not scores:
            return {
                "primary_theme": "generic",
                "confidence": 0.0,
                "theme_scores": {},
                "secondary_themes": [],
                "is_hunt_area": False,
                "is_urban": False,
                "recommended_era": "modern",
            }

        # Normalizar scores
        max_score = max(scores.values()) if scores else 1.0
        normalized = {
            theme: round(min(score / max(max_score, 1.0), 1.0), 3)
            for theme, score in scores.items()
        }

        # Tema primario
        primary = max(normalized, key=normalized.get)
        confidence = normalized[primary]

        # Temas secundarios (confianza > 0.2)
        secondary = sorted(
            [t for t, c in normalized.items() if t != primary and c > 0.2],
            key=lambda t: normalized[t],
            reverse=True,
        )[:3]

        # Determinar si es area de hunt
        is_hunt = (
            normalized.get("hunt", 0.0) > 0.4
            or len(spawns) > 10
            or (len(spawns) > 0 and len(houses) == 0)
        )

        # Determinar si es urbano
        is_urban = (
            normalized.get("city", 0.0) > 0.3
            or normalized.get("yalahar", 0.0) > 0.3
            or len(houses) >= 3
        )

        # Era recomendada
        if is_urban and confidence > 0.6:
            era = "modern"
        elif normalized.get("temple", 0.0) > 0.4:
            era = "ancient"
        elif normalized.get("dungeon", 0.0) > 0.4:
            era = "medieval"
        else:
            era = "modern"

        return {
            "primary_theme": primary,
            "confidence": confidence,
            "theme_scores": normalized,
            "secondary_themes": secondary,
            "is_hunt_area": is_hunt,
            "is_urban": is_urban,
            "recommended_era": era,
        }

    # ----------------------------------------------------------------
    # Scoring methods
    # ----------------------------------------------------------------

    def _score_grounds(self, tiles: Dict[str, int]) -> Dict[str, float]:
        """Puntua temas basado en tipos de suelo."""
        scores: Dict[str, float] = {}
        total = sum(tiles.values())

        if total == 0:
            return scores

        for theme, signatures in self.GROUND_SIGNATURES.items():
            theme_count = 0
            for tile_name, count in tiles.items():
                clean = tile_name.replace("ground_", "").replace("tile_", "").lower()
                for sig in signatures:
                    if sig.lower() in clean or clean in sig.lower():
                        theme_count += count
                        break

            if theme_count > 0:
                pct = theme_count / total
                scores[theme] = pct * 100.0

        return scores

    def _score_items(self, items: Dict[str, int]) -> Dict[str, float]:
        """Puntua temas basado en items (muros, decoraciones)."""
        scores: Dict[str, float] = {}
        total = sum(items.values())

        if total == 0:
            return scores

        for theme, signatures in self.ITEM_SIGNATURES.items():
            theme_count = 0
            for item_key, count in items.items():
                try:
                    item_id = int(item_key.replace("item_", ""))
                except (ValueError, AttributeError):
                    continue
                if item_id in signatures:
                    theme_count += count

            if theme_count > 0:
                pct = theme_count / total
                scores[theme] = pct * 100.0

        return scores

    def _score_hunt_spawns(self, spawns: List[Dict[str, Any]]) -> float:
        """Puntua si el area es de hunting basado en los monstruos."""
        if not spawns:
            return 0.0

        hunt_count = 0
        for spawn in spawns:
            monster = str(spawn.get("monster", "")).lower().replace(" ", "_")
            for indicator in self.HUNT_MONSTER_INDICATORS:
                if indicator in monster:
                    hunt_count += 1
                    break

        ratio = hunt_count / max(len(spawns), 1)
        return ratio * 50.0 + min(len(spawns) * 1.0, 30.0)

    # ----------------------------------------------------------------
    # Clasificacion rapida (atajo)
    # ----------------------------------------------------------------

    def quick_classify(self, style: Optional[str]) -> str:
        """
        Clasificacion rapida desde el string de estilo del MapAnalyzer.

        Args:
            style: String de estilo (e.g., "issavi", "roshamuul_dungeon").

        Returns:
            Tema normalizado.
        """
        if not style:
            return "generic"

        style_lower = style.lower()

        theme_map = {
            "issavi": "issavi",
            "roshamuul": "roshamuul",
            "temple": "temple",
            "dungeon": "dungeon",
            "city": "city",
            "yalahar": "yalahar",
            "hunt": "hunt",
            "jungle": "jungle",
            "ice": "ice",
            "hybrid": "hybrid",
        }

        for key, theme in theme_map.items():
            if key in style_lower:
                return theme

        return "generic"

    # ----------------------------------------------------------------
    # Metadatos extendidos
    # ----------------------------------------------------------------

    def classify_with_metadata(
        self,
        tiles: Dict[str, int],
        items: Optional[Dict[str, int]] = None,
        spawns: Optional[List[Dict[str, Any]]] = None,
        houses: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Clasificacion completa con metadatos adicionales para BlueprintMetadata.

        Returns:
            Dict compatible con BlueprintMetadata (style, era, difficulty, tags, hybrid).
        """
        result = self.classify(tiles, items, spawns, houses)

        # Determinar dificultad basada en spawns
        if result["is_hunt_area"]:
            if len(spawns or []) > 20:
                difficulty = "dangerous"
            elif len(spawns or []) > 10:
                difficulty = "hard"
            else:
                difficulty = "normal"
        else:
            difficulty = "safe"

        # Generar tags
        tags = [result["primary_theme"]]
        tags.extend(result["secondary_themes"])
        if result["is_hunt_area"]:
            tags.append("hunt")
        if result["is_urban"]:
            tags.append("urban")

        # Hybrid detection
        hybrid = len(result["secondary_themes"]) >= 2

        return {
            "style": result["primary_theme"],
            "era": result["recommended_era"],
            "difficulty": difficulty,
            "tags": tags,
            "capacity": self._estimate_capacity(tiles, spawns or [], houses or []),
            "hybrid": hybrid,
        }

    @staticmethod
    def _estimate_capacity(
        tiles: Dict[str, int],
        spawns: List[Dict[str, Any]],
        houses: List[Dict[str, Any]],
    ) -> str:
        """Estima la capacidad del area (small, medium, large, massive)."""
        total_tiles = sum(tiles.values())
        total_entities = len(spawns) + len(houses) * 3

        if total_tiles > 100000 or total_entities > 200:
            return "massive"
        elif total_tiles > 25000 or total_entities > 100:
            return "large"
        elif total_tiles > 5000 or total_entities > 20:
            return "medium"
        else:
            return "small"
