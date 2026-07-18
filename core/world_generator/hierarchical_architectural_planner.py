from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


class HierarchicalArchitecturalPlanner:
    """Expand semantic regions into original districts, parcels, buildings and rooms."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def enrich(self, plan: Any) -> dict[str, Any]:
        city = next((region for region in plan.regions if "city" in region.tags and "landmass" in region.tags), None)
        if city is None:
            plan.architecture = {}
            return {"status": "BLOCKED", "reason": "city landmass missing"}
        dimensions = self._building_dimensions()
        verticality = float(getattr(plan, "policies", {}).get("semantic_ai_verticality", 0.35))
        dimensions["floors"] = max(1, min(3, round(1 + verticality * 2)))
        priority_profiles = _priority_profiles(getattr(plan, "reference_style", {}))
        districts = self._districts(city)
        buildings = self._buildings(city, dimensions)
        plan.architecture = {
            "world": {"objective": plan.objective, "biomes": sorted({region.style for region in plan.regions})},
            "settlements": [{
                "name": city.name,
                "districts": districts,
                "parcels": [building["parcel"] for building in buildings],
                "buildings": buildings,
            }],
            "hunts": [
                {"name": region.name, "style": region.style, "role": region.role, "terrain": region.terrain}
                for region in plan.regions if "hunt" in region.tags
            ],
            "priority_style_profiles": priority_profiles,
            "source_policy": "database dimensions guide scale only; all centers and geometry are newly generated",
        }
        return {
            "status": "PASS",
            "district_count": len(districts),
            "parcel_count": len(buildings),
            "building_count": len(buildings),
            "room_count": sum(len(building["rooms"]) for building in buildings),
            "dimension_profile": dimensions,
            "priority_profiles_used": sorted(priority_profiles),
        }

    def _building_dimensions(self) -> dict[str, int]:
        defaults = {"width": 10, "height": 9, "floors": 2}
        path = self.root / "exports" / "planner_knowledge" / "RME_PLANNER_KNOWLEDGE.sqlite3"
        if not path.is_file():
            return defaults
        with sqlite3.connect(path) as connection:
            rows = connection.execute(
                "SELECT width, height, floors FROM town_structures "
                "WHERE kind='building_or_house' AND width BETWEEN 5 AND 24 AND height BETWEEN 5 AND 24"
            ).fetchall()
        if not rows:
            return defaults
        rows.sort(key=lambda row: row[0] * row[1])
        width, height, floors = rows[len(rows) // 2]
        return {"width": int(width), "height": int(height), "floors": max(1, min(3, int(floors)))}

    @staticmethod
    def _districts(city: Any) -> list[dict[str, Any]]:
        x, y = city.anchor
        return [
            {"name": "civic_core", "role": "temple_depot_plaza", "center": [x, y], "radius": [24, 20]},
            {"name": "raised_market", "role": "shops_npcs", "center": [x - 34, y - 18], "radius": [25, 20]},
            {"name": "stilt_housing", "role": "houses", "center": [x + 35, y + 25], "radius": [30, 24]},
            {"name": "wet_docks", "role": "docks_boats", "center": [x - 66, y + 10], "radius": [22, 32]},
        ]

    @staticmethod
    def _buildings(city: Any, dimensions: dict[str, int]) -> list[dict[str, Any]]:
        offsets = ((-42, -27), (-15, -39), (18, -37), (43, -22), (-45, 27), (-14, 38), (18, 40), (46, 24))
        functions = ("shop", "house", "temple", "depot", "house", "tavern", "house", "workshop")
        result = []
        for index, ((dx, dy), function) in enumerate(zip(offsets, functions)):
            width = max(7, dimensions["width"] + index % 3 - 1)
            height = max(7, dimensions["height"] - index % 2)
            floors = 2 if function in {"depot", "temple"} else dimensions["floors"]
            center = [city.anchor[0] + dx, city.anchor[1] + dy]
            result.append({
                "name": f"original_{function}_{index + 1}",
                "function": function,
                "center": center,
                "width": width,
                "height": height,
                "floors": floors,
                "exterior": "wet_swamp_city",
                "interior": "civic_stone" if function in {"depot", "temple"} else "timber",
                "parcel": {"center": center, "width": width + 4, "height": height + 4, "street_access": True},
                "rooms": _rooms(width, height, function),
            })
        return result


def _rooms(width: int, height: int, function: str) -> list[dict[str, Any]]:
    if function in {"depot", "temple"}:
        return [
            {"role": "public_hall", "width": width - 2, "height": max(3, height // 2)},
            {"role": "service_room", "width": max(3, width // 2), "height": max(3, height // 3)},
        ]
    return [
        {"role": "main_room", "width": max(3, width - 2), "height": max(3, height // 2)},
        {"role": "private_room", "width": max(3, width // 2), "height": max(3, height // 3)},
    ]


def _priority_profiles(reference_style: dict[str, Any]) -> dict[str, dict[str, Any]]:
    profiles = reference_style.get("visual_memory", {}).get("profiles_by_tag", {})
    return {
        style: dict(profiles[tag])
        for style, tag in {
            "wet_swamp_city": "zone_venore",
            "dry_ruins": "zone_krailos",
            "dark_cavern": "zone_roshamuul",
        }.items()
        if tag in profiles
    }
