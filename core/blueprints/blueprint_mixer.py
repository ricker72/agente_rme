from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class MixResult:
    """Result of mixing two blueprints into a new hybrid."""

    mixed_blueprint: Dict[str, Any]
    blueprint_a: Dict[str, Any]
    blueprint_b: Dict[str, Any]
    mix_ratio: Tuple[float, float]  # e.g., (0.6, 0.4) → 60% A, 40% B
    merged_features: List[str] = field(default_factory=list)
    conflicts_resolved: List[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mixed_name": self.mixed_blueprint.get("name", "unknown"),
            "mixed_theme": self.mixed_blueprint.get("theme", "hybrid"),
            "source_a": self.blueprint_a.get("name", "unknown"),
            "source_b": self.blueprint_b.get("name", "unknown"),
            "mix_ratio": f"{self.mix_ratio[0] * 100:.0f}%/{self.mix_ratio[1] * 100:.0f}%",
            "merged_features": self.merged_features,
            "conflicts_resolved": self.conflicts_resolved,
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class BlueprintMixer:
    """
    Mixes two blueprints into a new hybrid blueprint.

    Given two blueprints (e.g., Temple Issavi + Corruption Roshamuul),
    produces a new blueprint that inherits properties from both.

    Usage:
        mixer = BlueprintMixer()
        result = mixer.mix(temple_issavi, roshamuul_corruption)
        print(result.summary)
    """

    # Rules for mixing different categories
    MIX_RULES = {
        # (category_a, category_b): strategy
        ("temple", "temple"): "merge_layouts",
        ("temple", "boss_room"): "boss_in_temple",
        ("hunt", "temple"): "temple_in_hunt",
        ("city", "city"): "merge_layouts",
        ("bridge", "road"): "merge_layouts",
    }

    # Theme grounding rules: what changes when a theme is overlaid
    THEME_GROUNDING = {
        "issavi": {
            "grounds": [415, 393, 421],
            "walls": [1495, 1496, 1497],
            "decorations": [2153, 2117, 1803, 1510, 1545],
            "lighting": "bright",
            "palette": "golden_warm",
        },
        "roshamuul": {
            "grounds": [398, 400, 401],
            "walls": [1545, 1000],
            "decorations": [1304, 1775, 1738, 2050],
            "lighting": "dim",
            "palette": "dark_gray",
        },
        "corruption": {
            "grounds": [402, 403, 404],
            "walls": [1002, 1003],
            "decorations": [2052, 2060, 2064],
            "lighting": "eerie",
            "palette": "purple_dark",
        },
        "jungle": {
            "grounds": [103, 102, 104],
            "walls": [1000, 398],
            "decorations": [2705, 2104, 1499, 1507],
            "lighting": "natural",
            "palette": "green_earth",
        },
        "ice": {
            "grounds": [700, 701, 702],
            "walls": [703, 704],
            "decorations": [705, 706, 707],
            "lighting": "cold",
            "palette": "blue_white",
        },
        "ankrahmun": {
            "grounds": [231, 232, 233],
            "walls": [1000, 234],
            "decorations": [1510, 235, 236],
            "lighting": "warm",
            "palette": "desert_sand",
        },
    }

    def __init__(self):
        self._mix_count = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def mix(
        self,
        blueprint_a: Dict[str, Any],
        blueprint_b: Dict[str, Any],
        ratio: Tuple[float, float] = (0.5, 0.5),
    ) -> MixResult:
        """
        Mix two blueprints into a new hybrid.

        Args:
            blueprint_a: Primary blueprint (e.g., Temple Issavi).
            blueprint_b: Secondary blueprint (e.g., Corruption Roshamuul).
            ratio: Weight ratio (a_weight, b_weight). Default (0.5, 0.5) = equal mix.

        Returns:
            MixResult with the new hybrid blueprint and metadata.
        """
        self._mix_count += 1

        ra, rb = ratio
        result = MixResult(
            mixed_blueprint={},
            blueprint_a=blueprint_a,
            blueprint_b=blueprint_b,
            mix_ratio=ratio,
        )

        # Determine strategy
        cat_a = blueprint_a.get("category", "unknown")
        cat_b = blueprint_b.get("category", "unknown")
        strategy = self._get_strategy(cat_a, cat_b)

        # Build the hybrid
        hybrid = self._build_hybrid(blueprint_a, blueprint_b, ra, rb, strategy, result)

        result.mixed_blueprint = hybrid
        result.summary = (
            f"Mix #{self._mix_count}: {blueprint_a.get('name', 'A')} "
            f"({ra * 100:.0f}%) + {blueprint_b.get('name', 'B')} "
            f"({rb * 100:.0f}%) -> {hybrid.get('name', 'hybrid')} "
            f"[{hybrid.get('theme', 'hybrid')}]"
        )

        return result

    def mix_themes(
        self, base_category: str, theme_a: str, theme_b: str, name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new blueprint by blending two themes for a given category.

        Args:
            base_category: The category to create (e.g., 'temple').
            theme_a: Primary theme (e.g., 'issavi').
            theme_b: Secondary theme (e.g., 'corruption').
            name: Optional name for the new blueprint.

        Returns:
            A new blueprint dict with blended theme properties.
        """
        grounding_a = self.THEME_GROUNDING.get(theme_a, {})
        grounding_b = self.THEME_GROUNDING.get(theme_b, {})

        hybrid_name = name or f"{theme_a}_{theme_b}_{base_category}"

        # Blend grounds: 60% theme A, 40% theme B
        grounds_a = grounding_a.get("grounds", [])
        grounds_b = grounding_b.get("grounds", [])
        blended_grounds = self._blend_list(grounds_a, grounds_b, 0.6, 0.4)

        # Blend decorations
        dec_a = grounding_a.get("decorations", [])
        dec_b = grounding_b.get("decorations", [])
        blended_decor = self._blend_list(dec_a, dec_b, 0.5, 0.5)

        # Blend walls
        walls_a = grounding_a.get("walls", [])
        walls_b = grounding_b.get("walls", [])
        blended_walls = self._blend_list(walls_a, walls_b, 0.6, 0.4)

        hybrid = {
            "name": hybrid_name,
            "category": base_category,
            "theme": f"{theme_a}_{theme_b}",
            "version": "1.0.0",
            "size": [20, 20],
            "description": (
                f"Blueprint híbrido: {base_category} con tema {theme_a} fusionado con {theme_b}"
            ),
            "grounds": blended_grounds,
            "walls_items": blended_walls,
            "decorations": blended_decor,
            "metadata": {
                "style": f"{theme_a}_{theme_b}",
                "source_themes": [theme_a, theme_b],
                "era": "modern",
                "hybrid": True,
                "tags": [theme_a, theme_b, base_category, "hybrid", "mixed"],
                "lighting_a": grounding_a.get("lighting", "neutral"),
                "lighting_b": grounding_b.get("lighting", "neutral"),
                "palette_a": grounding_a.get("palette", "neutral"),
                "palette_b": grounding_b.get("palette", "neutral"),
            },
        }

        return hybrid

    # ------------------------------------------------------------------
    # Strategy selection
    # ------------------------------------------------------------------

    def _get_strategy(self, cat_a: str, cat_b: str) -> str:
        """Determine the mixing strategy based on blueprint categories."""
        key = (cat_a, cat_b)
        if key in self.MIX_RULES:
            return self.MIX_RULES[key]
        key_rev = (cat_b, cat_a)
        if key_rev in self.MIX_RULES:
            return self.MIX_RULES[key_rev]
        # Default: overlay — B's theme layered onto A's structure
        return "overlay_theme"

    # ------------------------------------------------------------------
    # Hybrid builder
    # ------------------------------------------------------------------

    def _build_hybrid(
        self,
        bp_a: Dict[str, Any],
        bp_b: Dict[str, Any],
        ra: float,
        rb: float,
        strategy: str,
        result: MixResult,
    ) -> Dict[str, Any]:
        """Build the hybrid blueprint based on the selected strategy."""
        name_a = bp_a.get("name", "blueprint_a")
        name_b = bp_b.get("name", "blueprint_b")
        theme_a = bp_a.get("theme", "unknown")
        theme_b = bp_b.get("theme", "unknown")

        hybrid_name = f"{name_a}_x_{name_b}"

        # Base structure from A
        hybrid = copy.deepcopy(bp_a)
        hybrid["name"] = hybrid_name
        hybrid["theme"] = f"{theme_a}_{theme_b}"

        if strategy == "merge_layouts":
            self._merge_layouts(hybrid, bp_b, ra, rb, result)
        elif strategy == "overlay_theme":
            self._overlay_theme(hybrid, bp_b, ra, rb, result)
        elif strategy == "boss_in_temple":
            self._boss_in_temple(hybrid, bp_b, result)
        elif strategy == "temple_in_hunt":
            self._temple_in_hunt(hybrid, bp_b, result)

        # Always blend item palettes
        self._blend_items(hybrid, bp_a, bp_b, ra, rb, result)

        # Update metadata
        self._update_metadata(hybrid, bp_a, bp_b, ra, rb)
        result.merged_features.append(f"theme_{theme_a}_{theme_b}")

        return hybrid

    # ------------------------------------------------------------------
    # Strategy implementations
    # ------------------------------------------------------------------

    def _merge_layouts(
        self,
        hybrid: Dict[str, Any],
        bp_b: Dict[str, Any],
        ra: float,
        rb: float,
        result: MixResult,
    ) -> None:
        """Merge layouts: blend zones, rooms, roads from both blueprints."""
        zones_a = hybrid.get("zones", [])
        zones_b = bp_b.get("zones", [])
        if zones_b:
            # Offset B's zones to avoid overlap
            offset_x = (
                max((z.get("position", [0, 0])[0] for z in zones_a), default=0) + 10
            )
            for zone in zones_b:
                shifted = copy.deepcopy(zone)
                pos = shifted.get("position", [0, 0])
                shifted["position"] = [pos[0] + offset_x, pos[1]]
                zones_a.append(shifted)
            hybrid["zones"] = zones_a
            result.merged_features.append("merged_zones")
            result.conflicts_resolved.append(
                f"Offset B zones by +{offset_x}X to avoid overlap"
            )

        # Merge rooms
        rooms_a = hybrid.get("rooms", [])
        rooms_b = bp_b.get("rooms", [])
        if rooms_b:
            for room in rooms_b[: len(rooms_b) // 2]:
                rooms_a.append(copy.deepcopy(room))
            hybrid["rooms"] = rooms_a
            result.merged_features.append("merged_rooms")

        # Merge roads
        roads_a = hybrid.get("roads", [])
        roads_b = bp_b.get("roads", [])
        if roads_b:
            roads_a.extend(copy.deepcopy(roads_b[:1]))
            hybrid["roads"] = roads_a
            result.merged_features.append("merged_roads")

        # Expand size
        size_a = hybrid.get("size", [20, 20])
        size_b = bp_b.get("size", [20, 20])
        hybrid["size"] = [
            max(size_a[0], size_b[0]) * 2,
            max(size_a[1], size_b[1]),
        ]

    def _overlay_theme(
        self,
        hybrid: Dict[str, Any],
        bp_b: Dict[str, Any],
        ra: float,
        rb: float,
        result: MixResult,
    ) -> None:
        """Overlay B's theme properties onto A's structure."""
        theme_b = bp_b.get("theme", "unknown")
        grounding = self.THEME_GROUNDING.get(theme_b, {})

        # Blend grounds: keep some from A, add some from B
        grounds_a = hybrid.get("grounds", [])
        grounds_b = bp_b.get("grounds", grounding.get("grounds", []))
        hybrid["grounds"] = self._blend_list(grounds_a, grounds_b, 0.6, 0.4)
        result.merged_features.append("blended_grounds")

        # Blend decorations
        dec_a = hybrid.get("decorations", [])
        dec_b = bp_b.get("decorations", grounding.get("decorations", []))
        hybrid["decorations"] = self._blend_list(dec_a, dec_b, 0.5, 0.5)
        result.merged_features.append("blended_decorations")

        # Update description
        hybrid["description"] = (
            f"{hybrid.get('description', '')} | Infused with {theme_b} elements"
        )

    def _boss_in_temple(
        self, hybrid: Dict[str, Any], bp_b: Dict[str, Any], result: MixResult
    ) -> None:
        """Embed a boss room inside a temple blueprint."""
        # Place boss spawn in the altar room
        rooms = hybrid.get("rooms", [])
        altar_room = None
        for room in rooms:
            if room.get("type") == "altar_room" or "sanctum" in room.get("name", ""):
                altar_room = room
                break

        if altar_room:
            boss_spawns = bp_b.get("spawns", bp_b.get("features", []))
            hybrid.setdefault("embedded_boss", {})
            hybrid["embedded_boss"] = {
                "room": altar_room["name"],
                "boss": boss_spawns[0].get("monster", "Unknown")
                if boss_spawns
                else "Unknown",
                "position": altar_room.get("position", [0, 0]),
            }
            result.merged_features.append("embedded_boss_room")

        # Merge features
        features = hybrid.get("features", [])
        boss_features = bp_b.get("features", [])
        features.extend(copy.deepcopy(boss_features[:3]))
        hybrid["features"] = features
        result.merged_features.append("merged_boss_features")

    def _temple_in_hunt(
        self, hybrid: Dict[str, Any], bp_b: Dict[str, Any], result: MixResult
    ) -> None:
        """Embed a temple/rez point inside a hunt area."""
        temple_features = bp_b.get("features", [])
        altar_features = [
            f for f in temple_features if "altar" in str(f.get("type", "")).lower()
        ]
        hybrid.setdefault("embedded_temple", {})
        hybrid["embedded_temple"] = {
            "position": [2, 2],
            "features": altar_features[:2] if altar_features else [],
        }
        result.merged_features.append("embedded_temple")

    # ------------------------------------------------------------------
    # Item blending
    # ------------------------------------------------------------------

    def _blend_items(
        self,
        hybrid: Dict[str, Any],
        bp_a: Dict[str, Any],
        bp_b: Dict[str, Any],
        ra: float,
        rb: float,
        result: MixResult,
    ) -> None:
        """Blend item palettes (grounds, walls, decorations)."""
        # Grounds
        ga = bp_a.get("grounds", [])
        gb = bp_b.get("grounds", [])
        hybrid["grounds"] = self._blend_list(ga, gb, ra, rb)

        # Walls
        wa = bp_a.get("walls_items", bp_a.get("walls", []))
        wb = bp_b.get("walls_items", bp_b.get("walls", []))
        if isinstance(wa, dict):
            wa = [wa] if wa else []
        if isinstance(wb, dict):
            wb = [wb] if wb else []
        hybrid["walls_items"] = self._blend_list(wa, wb, ra, rb)

        # Decorations
        da = bp_a.get("decorations", [])
        db = bp_b.get("decorations", [])
        hybrid["decorations"] = self._blend_list(da, db, ra, rb)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _update_metadata(
        self,
        hybrid: Dict[str, Any],
        bp_a: Dict[str, Any],
        bp_b: Dict[str, Any],
        ra: float,
        rb: float,
    ) -> None:
        """Update metadata to reflect the hybrid nature."""
        meta = hybrid.setdefault("metadata", {})
        meta["hybrid"] = True
        meta["source_a"] = bp_a.get("name", "unknown")
        meta["source_b"] = bp_b.get("name", "unknown")
        meta["mix_ratio"] = f"{ra * 100:.0f}/{rb * 100:.0f}"
        meta["source_themes"] = [
            bp_a.get("theme", "unknown"),
            bp_b.get("theme", "unknown"),
        ]

        # Combine tags
        tags_a = meta.get("tags", [])
        tags_b = bp_b.get("metadata", {}).get("tags", [])
        meta["tags"] = list(set(tags_a + tags_b + ["hybrid", "mixed"]))

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def _blend_list(
        self, list_a: List, list_b: List, weight_a: float, weight_b: float
    ) -> List:
        """Blend two lists, taking more from the heavier-weighted side."""
        if not list_a and not list_b:
            return []
        if not list_a:
            return list(list_b)
        if not list_b:
            return list(list_a)

        # Determine how many items to take from each
        total = max(2, min(len(list_a) + len(list_b), 6))
        count_a = max(1, int(total * weight_a))
        count_b = max(1, total - count_a)

        result = []
        result.extend(list_a[:count_a])
        result.extend(list_b[:count_b])

        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for item in result:
            if item not in seen:
                seen.add(item)
                deduped.append(item)

        return deduped
