"""
HITO 12 — Architecture Analyzer: analyzes map architecture:
structure distribution, cities, zones, construction patterns.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Dict, List


class ArchitectureAnalyzer:
    """Analyze map architecture and structure."""

    # Ground IDs by structural type
    STRUCTURAL_GROUNDS = {
        "sandstone_floor": "natural",
        "polished_stone": "urban",
        "yalahar_floor": "urban",
        "mossy_stone": "dungeon",
        "roshamuul_floor": "wild",
        "roshamuul_stone": "wild",
    }

    # Known structural item IDs
    WALL_ITEM_IDS = {
        101,
        102,
        103,
        104,
        105,
        106,
        107,
        108,
        109,
        110,
        1000,
        1001,
        1002,
        1003,
        1004,
        1005,
        1006,
        1007,
        1008,
        1009,
        2100,
        2101,
        2102,
        2103,
        2104,
        2105,
    }

    DOOR_ITEM_IDS = {
        1209,
        1210,
        1211,
        1212,
        1213,
        1214,
        1215,
        1216,
        1217,
        1220,
        1221,
        1222,
        1223,
        1224,
        1225,
        5000,
        5001,
        5002,
        5003,
        5004,
        5005,
        5006,
    }

    def analyze(
        self,
        tiles: Dict[str, int],
        items: Dict[str, int],
        houses: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
        waypoints: List[Dict[str, object]],
        map_size: Dict[str, int],
    ) -> Dict[str, object]:
        """Analyze the complete map architecture.

        Args:
            tiles: Dict {tile_type: count}.
            items: Dict {item_type: count}.
            houses: List of houses/towns.
            spawns: List of spawns.
            waypoints: List of waypoints.
            map_size: Dict {"width": w, "height": h}.

        Returns:
            Dict with architectural analysis.
        """
        return {
            "structural_composition": self._analyze_structural_composition(tiles),
            "urban_zones": self._detect_urban_zones(tiles, houses),
            "wall_analysis": self._analyze_walls(items),
            "door_analysis": self._analyze_doors(items),
            "building_category": self._classify_building(houses, spawns, map_size),
            "infrastructure_score": self._compute_infrastructure_score(
                tiles, items, houses, waypoints, map_size
            ),
            "zone_classification": self._classify_zones(tiles, items, houses, spawns),
            "complexity_metrics": self._compute_complexity(
                tiles, items, houses, spawns, waypoints
            ),
        }

    # ------------------------------------------------------------------
    # Structural composition
    # ------------------------------------------------------------------

    @staticmethod
    def _analyze_structural_composition(tiles: Dict[str, int]) -> Dict[str, object]:
        """Analyze ground type composition."""
        if not tiles:
            return {"categories": {}, "dominant": "unknown"}

        categories = defaultdict(int)
        for tile_name, count in tiles.items():
            # Clean the tile name
            clean = tile_name.replace("ground_", "").replace("tile_", "")
            category = ArchitectureAnalyzer.STRUCTURAL_GROUNDS.get(clean, "misc")
            categories[category] += count

        total = sum(categories.values())
        categories_pct = {
            cat: round(100 * cnt / max(total, 1), 1) for cat, cnt in categories.items()
        }

        dominant = max(categories, key=categories.get) if categories else "unknown"

        return {
            "categories": categories_pct,
            "total_tiles": total,
            "dominant_category": dominant,
            "is_urban": categories.get("urban", 0) > categories.get("natural", 0),
            "is_dungeon": categories.get("dungeon", 0) > total * 0.3,
        }

    # ------------------------------------------------------------------
    # Urban zones
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_urban_zones(
        tiles: Dict[str, int],
        houses: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Detect urban zones based on houses and urban tiles."""
        urban_tiles = tiles.get("polished_stone", 0) + tiles.get("yalahar_floor", 0)
        house_count = len(houses)

        if house_count == 0:
            return {
                "zone_type": "wilderness" if urban_tiles < 500 else "outpost",
                "house_count": 0,
                "urban_tile_count": urban_tiles,
            }

        if house_count >= 10:
            zone_type = "city"
        elif house_count >= 5:
            zone_type = "town"
        elif house_count >= 2:
            zone_type = "village"
        else:
            zone_type = "camp"

        return {
            "zone_type": zone_type,
            "house_count": house_count,
            "urban_tile_count": urban_tiles,
            "estimated_population": house_count * 5,
            "city_names": [h.get("name", "") for h in houses if h.get("name")],
        }

    # ------------------------------------------------------------------
    # Wall analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _analyze_walls(items: Dict[str, int]) -> Dict[str, object]:
        """Analyze wall distribution."""
        wall_count = 0
        wall_types = {}

        for item_key, count in items.items():
            try:
                item_id = int(item_key.replace("item_", ""))
            except ValueError:
                continue
            if item_id in ArchitectureAnalyzer.WALL_ITEM_IDS:
                wall_count += count
                wall_types[str(item_id)] = count

        return {
            "total_walls": wall_count,
            "wall_types": len(wall_types),
            "wall_distribution": dict(
                sorted(wall_types.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }

    # ------------------------------------------------------------------
    # Door analysis
    # ------------------------------------------------------------------

    @staticmethod
    def _analyze_doors(items: Dict[str, int]) -> Dict[str, object]:
        """Analyze door distribution."""
        door_count = 0
        door_types = {}

        for item_key, count in items.items():
            try:
                item_id = int(item_key.replace("item_", ""))
            except ValueError:
                continue
            if item_id in ArchitectureAnalyzer.DOOR_ITEM_IDS:
                door_count += count
                door_types[str(item_id)] = count

        return {
            "total_doors": door_count,
            "door_types": len(door_types),
            "door_distribution": dict(
                sorted(door_types.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
        }

    # ------------------------------------------------------------------
    # Building classification
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_building(
        houses: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
        map_size: Dict[str, int],
    ) -> Dict[str, object]:
        """Classify the map construction type."""
        width = map_size.get("width", 100)
        height = map_size.get("height", 100)

        spawn_density = len(spawns) / max(width * height / 100, 1)
        house_density = len(houses) / max(width * height / 10000, 1)

        if house_density > 5:
            building_type = "metropolis"
        elif house_density > 2:
            building_type = "city"
        elif house_density > 0.5:
            building_type = "town"
        elif spawn_density > 10:
            building_type = "hunting_ground"
        elif houses:
            building_type = "outpost"
        else:
            building_type = "wilderness"

        return {
            "building_type": building_type,
            "house_density_per_10ksq": round(house_density, 2),
            "spawn_density_per_100sq": round(spawn_density, 2),
            "has_temple": any(
                h.get("name", "").lower() == "temple"
                or "temple" in str(h.get("name", "")).lower()
                for h in houses
            ),
        }

    # ------------------------------------------------------------------
    # Infrastructure score
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_infrastructure_score(
        tiles: Dict[str, int],
        items: Dict[str, int],
        houses: List[Dict[str, object]],
        waypoints: List[Dict[str, object]],
        map_size: Dict[str, int],
    ) -> Dict[str, object]:
        """Calculate infrastructure score (0-100)."""
        width = map_size.get("width", 100)
        height = map_size.get("height", 100)
        area = max(width * height, 1)

        urban_tiles = tiles.get("polished_stone", 0) + tiles.get("yalahar_floor", 0)
        house_score = min(len(houses) * 10 / max(area / 10000, 1), 35)
        road_score = min(urban_tiles / max(area / 10, 1), 30)
        waypoint_score = min(len(waypoints) * 5, 15)
        item_score = min(sum(items.values()) / max(area / 10, 1), 20)

        total = round(house_score + road_score + waypoint_score + item_score, 1)

        return {
            "total_score": total,
            "infrastructure_level": (
                "excellent"
                if total >= 80
                else (
                    "good"
                    if total >= 60
                    else "moderate"
                    if total >= 40
                    else "basic"
                    if total >= 20
                    else "minimal"
                )
            ),
            "breakdown": {
                "house_score": round(house_score, 1),
                "road_score": round(road_score, 1),
                "waypoint_score": round(waypoint_score, 1),
                "item_score": round(item_score, 1),
            },
        }

    # ------------------------------------------------------------------
    # Zone classification
    # ------------------------------------------------------------------

    @staticmethod
    def _classify_zones(
        tiles: Dict[str, int],
        items: Dict[str, int],
        houses: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
    ) -> List[Dict[str, object]]:
        """Classify map zones into categories."""
        zones = []

        # Urban zone
        if houses:
            urban_tiles = tiles.get("polished_stone", 0)
            zones.append(
                {
                    "zone": "urban",
                    "house_count": len(houses),
                    "tile_count": urban_tiles,
                    "description": f"Urban zone with {len(houses)} buildings",
                }
            )

        # Hunting zone
        if spawns:
            zones.append(
                {
                    "zone": "hunting",
                    "spawn_count": len(spawns),
                    "unique_monsters": len(set(sp.get("monster", "") for sp in spawns)),
                    "description": f"Hunting zone with {len(spawns)} spawns",
                }
            )

        # Natural zone
        natural = tiles.get("sandstone_floor", 0)
        if natural > 500:
            zones.append(
                {
                    "zone": "natural",
                    "tile_count": natural,
                    "description": "Natural terrain area",
                }
            )

        return zones

    # ------------------------------------------------------------------
    # Complexity metrics
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_complexity(
        tiles: Dict[str, int],
        items: Dict[str, int],
        houses: List[Dict[str, object]],
        spawns: List[Dict[str, object]],
        waypoints: List[Dict[str, object]],
    ) -> Dict[str, object]:
        """Calculate map complexity metrics."""
        unique_tiles = len(tiles)
        unique_items = len(items)

        complexity_score = (
            min(unique_tiles, 100) * 0.3
            + min(unique_items, 200) * 0.2
            + min(len(houses) * 5, 30)
            + min(len(spawns) * 0.5, 20)
            + min(len(waypoints) * 3, 10)
        )

        return {
            "complexity_score": round(complexity_score, 1),
            "complexity_level": (
                "very_high"
                if complexity_score >= 80
                else (
                    "high"
                    if complexity_score >= 60
                    else (
                        "medium"
                        if complexity_score >= 40
                        else "low"
                        if complexity_score >= 20
                        else "minimal"
                    )
                )
            ),
            "components": {
                "unique_tile_types": unique_tiles,
                "unique_item_types": unique_items,
                "structures": len(houses),
                "spawn_variety": len(set(sp.get("monster", "") for sp in spawns)),
                "waypoint_count": len(waypoints),
            },
        }
