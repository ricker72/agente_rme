from __future__ import annotations

import hashlib
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Any


class HierarchicalArchitecturalPlanner:
    """Expand semantic regions into original districts, parcels, buildings and rooms."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def enrich(self, plan: Any) -> dict[str, Any]:
        settlement = self._settlement_region(plan)
        if settlement is None:
            plan.architecture = {}
            return {"status": "NOT_REQUESTED", "reason": "settlement intent missing"}
        dimensions = self._building_dimensions()
        verticality = float(getattr(plan, "policies", {}).get("semantic_ai_verticality", 0.35))
        dimensions["floors"] = max(1, min(3, round(1 + verticality * 2)))
        priority_profiles = _priority_profiles(getattr(plan, "reference_style", {}))
        functions = self._requested_functions(plan.objective, settlement)
        districts = self._districts(settlement, functions)
        buildings = self._buildings(plan.objective, settlement, dimensions, functions)
        plan.architecture = {
            "world": {"objective": plan.objective, "biomes": sorted({region.style for region in plan.regions})},
            "settlements": [{
                "name": settlement.name,
                "districts": districts,
                "parcels": [building["parcel"] for building in buildings],
                "buildings": buildings,
            }],
            "hunts": [
                {"name": region.name, "style": region.style, "role": region.role, "terrain": region.terrain}
                for region in plan.regions if "hunt" in region.tags
            ],
            "priority_style_profiles": priority_profiles,
            "connectivity_contract": {
                "all_public_buildings_require_route_access": True,
                "temple_requires_door": False,
                "temple_safe_core_required": "temple" in functions,
                "routes": [
                    {"name": route.name, "role": route.role, "width": route.width}
                    for route in plan.routes
                    if route.role in {"city_route", "primary_route", "nature_route"}
                ],
            },
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
        try:
            with sqlite3.connect(path) as connection:
                rows = connection.execute(
                    "SELECT width, height, floors FROM town_structures "
                    "WHERE kind='building_or_house' AND width BETWEEN 5 AND 24 AND height BETWEEN 5 AND 24"
                ).fetchall()
        except sqlite3.Error:
            return defaults
        if not rows:
            return defaults
        rows.sort(key=lambda row: row[0] * row[1])
        width, height, floors = rows[len(rows) // 2]
        return {"width": int(width), "height": int(height), "floors": max(1, min(3, int(floors)))}

    @staticmethod
    def _settlement_region(plan: Any) -> Any | None:
        regions = list(getattr(plan, "regions", ()))
        city = next((region for region in regions if "city" in region.tags and "landmass" in region.tags), None)
        if city is not None:
            return city
        safe = next((region for region in regions if "safe_zone" == region.role or "temple" in region.tags), None)
        if safe is None and not _objective_requests_settlement(getattr(plan, "objective", "")):
            return None
        if safe is not None:
            containing = next(
                (region for region in regions if "landmass" in region.tags and region.contains(*safe.anchor)),
                None,
            )
            if containing is not None:
                return containing
        return next((region for region in regions if "landmass" in region.tags), None)

    @staticmethod
    def _requested_functions(objective: str, settlement: Any) -> tuple[str, ...]:
        tokens = _design_tokens(objective)
        functions: list[str] = []
        requested = (
            ("temple", {"temple", "templo"}),
            ("depot", {"depot", "deposito"}),
            ("shop", {"shop", "shops", "tienda", "tiendas"}),
            ("house", {"house", "houses", "casa", "casas"}),
            ("tavern", {"tavern", "taberna"}),
            ("workshop", {"workshop", "taller"}),
        )
        for function, aliases in requested:
            if tokens & aliases:
                functions.append(function)
        if "temple" in settlement.tags and "temple" not in functions:
            functions.insert(0, "temple")
        if tokens & {"town", "city", "ciudad", "pueblo"}:
            for function in ("temple", "depot", "shop", "house", "house"):
                if function == "house" or function not in functions:
                    functions.append(function)
        return tuple(functions or ("temple",))

    @staticmethod
    def _districts(settlement: Any, functions: tuple[str, ...]) -> list[dict[str, Any]]:
        x, y = settlement.anchor
        districts = [{"name": "civic_core", "role": "temple_safe_core", "center": [x, y], "radius": [12, 10]}]
        if any(function in functions for function in ("depot", "shop", "tavern", "workshop")):
            districts.append({"name": "service_lane", "role": "depot_shops_npcs", "center": [x - 20, y + 12], "radius": [18, 14]})
        if "house" in functions:
            districts.append({"name": "residential_edge", "role": "houses", "center": [x + 22, y + 14], "radius": [20, 16]})
        return districts

    @staticmethod
    def _buildings(
        objective: str,
        settlement: Any,
        dimensions: dict[str, int],
        functions: tuple[str, ...],
    ) -> list[dict[str, Any]]:
        offsets = _oriented_offsets(objective, len(functions))
        result = []
        for index, ((dx, dy), function) in enumerate(zip(offsets, functions)):
            compact_temple = len(functions) == 1 and function == "temple"
            width = 9 if compact_temple else max(7, dimensions["width"] + index % 3 - 1)
            height = 7 if compact_temple else max(7, dimensions["height"] - index % 2)
            floors = 2 if function in {"depot", "temple"} else dimensions["floors"]
            if compact_temple:
                floors = 1
            center = [settlement.anchor[0] + dx, settlement.anchor[1] + dy]
            result.append({
                "name": f"original_{function}_{index + 1}",
                "function": function,
                "center": center,
                "width": width,
                "height": height,
                "floors": floors,
                "exterior": settlement.style,
                "interior": "civic_stone" if function in {"depot", "temple"} else "timber",
                "parcel": {"center": center, "width": width + 4, "height": height + 4, "street_access": True},
                "rooms": _rooms(width, height, function),
            })
        return result


def _objective_requests_settlement(objective: str) -> bool:
    return bool(_design_tokens(objective) & {
        "city", "town", "ciudad", "pueblo", "temple", "templo", "depot",
        "shop", "shops", "tienda", "tiendas", "house", "houses", "casa", "casas",
    })


def _tokens(value: str) -> set[str]:
    normalized = unicodedata.normalize("NFKD", value.casefold()).encode("ascii", "ignore").decode("ascii")
    return {token for token in re.findall(r"[a-z0-9]+", normalized) if len(token) > 2}


def _design_tokens(value: str) -> set[str]:
    without_metadata = re.sub(
        r"\btown\s*(?:name)?\s*[:=]\s*[a-z][a-z0-9 _-]{0,39}?(?=\s+(?:x\s*[:=]|coordenadas?|coordinates?)|[,;]|$)",
        " ",
        value,
        flags=re.IGNORECASE,
    )
    return _tokens(without_metadata)


def _oriented_offsets(objective: str, count: int) -> tuple[tuple[int, int], ...]:
    base = ((0, 0), (-18, 10), (18, 11), (-20, -13), (20, -12), (0, 22), (0, -22), (28, 0))
    orientation = hashlib.sha256(objective.encode("utf-8")).digest()[0] % 4
    def rotate(point: tuple[int, int]) -> tuple[int, int]:
        x, y = point
        return ((x, y), (-y, x), (-x, -y), (y, -x))[orientation]
    return tuple(rotate(point) for point in base[:count])


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
