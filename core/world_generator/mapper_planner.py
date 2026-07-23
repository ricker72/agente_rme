from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any

from core.world_generator.semantic_color_blueprint import (
    BlueprintLayer,
    SemanticColorBlueprint,
)
from core.world_generator.contextual_ground_selector import ContextualGroundBrushSelector, GroundContext


Point = tuple[int, int]


@dataclass(frozen=True)
class MapperPlannedRegion:
    name: str
    role: str
    style: str
    anchor: Point
    radius: tuple[int, int]
    terrain: str
    tags: tuple[str, ...] = ()

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        rx, ry = self.radius
        return self.anchor[0] - rx, self.anchor[1] - ry, self.anchor[0] + rx, self.anchor[1] + ry

    def contains(self, x: int, y: int) -> bool:
        rx, ry = max(1, self.radius[0]), max(1, self.radius[1])
        wave = math.sin((x + len(self.name)) / 11.0) * 0.09 + math.cos((y - len(self.style)) / 15.0) * 0.08
        ellipse = ((x - self.anchor[0]) / rx) ** 2 + ((y - self.anchor[1]) / ry) ** 2
        if ellipse > 1.0 + wave:
            return False
        if "hunt" in self.tags:
            erosion = (
                math.sin((x - self.anchor[0]) / 7.0)
                + math.cos((y - self.anchor[1]) / 9.0)
                + math.sin((x + y + len(self.name)) / 13.0)
            )
            if ellipse > 0.42 and erosion < -0.52:
                return False
        return True


@dataclass(frozen=True)
class MapperPlannedRoute:
    name: str
    role: str
    points: tuple[Point, ...]
    width: int
    terrain: str
    tags: tuple[str, ...] = ()


@dataclass
class MapperPlan:
    objective: str
    regions: list[MapperPlannedRegion] = field(default_factory=list)
    routes: list[MapperPlannedRoute] = field(default_factory=list)
    policies: dict[str, Any] = field(default_factory=dict)
    reference_style: dict[str, Any] = field(default_factory=dict)
    architecture: dict[str, Any] = field(default_factory=dict)

    def contains_land(self, x: int, y: int) -> bool:
        if any(region.contains(x, y) for region in self.regions if "landmass" in region.tags):
            return True
        for route in self.routes:
            if "land_connector" in route.tags and distance_to_polyline(x, y, route.points) <= route.width + 8:
                return True
        return False

    def to_report(self) -> dict[str, Any]:
        return {
            "stage": "Mapper Planner",
            "status": "PASS" if self.regions and self.routes else "BLOCKED",
            "objective": self.objective,
            "contract": {
                "runs_before": "Mapper Scene Graph",
                "generates_raw_item_ids": False,
                "writes_otbm_directly": False,
                "output": "semantic geometry, routes, biome intent and mapper policies",
            },
            "policies": self.policies,
            "reference_style": self.reference_style,
            "architecture": self.architecture,
            "regions": [
                {
                    "name": region.name,
                    "role": region.role,
                    "style": region.style,
                    "anchor": list(region.anchor),
                    "radius": list(region.radius),
                    "terrain": region.terrain,
                    "bounds": list(region.bounds),
                    "tags": list(region.tags),
                }
                for region in self.regions
            ],
            "routes": [
                {
                    "name": route.name,
                    "role": route.role,
                    "points": [list(point) for point in route.points],
                    "width": route.width,
                    "terrain": route.terrain,
                    "tags": list(route.tags),
                }
                for route in self.routes
            ],
        }


def build_mapper_plan(
    *,
    city_blueprint: dict[str, Any],
    hunt_blueprint: dict[str, Any],
    semantic_plan: Any | None,
    otmapgen_reference_report: dict[str, Any] | None = None,
    world_style_profile: Any | None = None,
    experience_guidance: dict[str, Any] | None = None,
    semantic_ai_guidance: dict[str, Any] | None = None,
) -> MapperPlan:
    objective = getattr(
        semantic_plan,
        "objective",
        "NECRO original playable OpenTibia map with city, hunts, water envelope and RME brush output.",
    )
    objective_anchor = _objective_anchor(objective)
    objective_town = _objective_town_name(objective)
    plan = MapperPlan(
        objective=objective,
        policies={
            "z7_foundation_order": ["sea_canvas", "landmass", "biome_ground", "roads", "structures", "doodads"],
            "open_water_ground": "sea",
            "no_teleports": True,
            "city_center": list(objective_anchor),
            "town_name": objective_town,
            "minimum_hunt_routes": 3,
            "reference_policy": "world.otbm/OTMapGen provide abstract proportions only, never copied tile chunks",
            "otmapgen_reference_ready": (otmapgen_reference_report or {}).get("status") == "PASS",
        },
        reference_style=(world_style_profile.to_dict() if hasattr(world_style_profile, "to_dict") else dict(world_style_profile or {})),
    )
    guidance = dict(experience_guidance or {})
    if guidance:
        plan.reference_style["experience_learning"] = guidance
        plan.policies["learned_positive_rule_count"] = len(guidance.get("positive_rules", ()))
        plan.policies["learned_negative_constraint_count"] = len(guidance.get("negative_constraints", ()))
        plan.policies["experience_rules_are_abstract"] = bool(
            not guidance.get("stores_source_geometry", True)
        )
    compact_kind = _compact_objective_kind(objective)
    if compact_kind:
        _populate_compact_plan(plan, compact_kind, objective_anchor)
    else:
        plan.regions.extend(
            [
            MapperPlannedRegion("main_swamp_island", "landmass", "wet_swamp_city", (1000, 1002), (145, 118), "grass", ("landmass", "city")),
            MapperPlannedRegion("krailos_ruins_plateau", "landmass", "dry_ruins", (1172, 1008), (84, 58), "transition", ("landmass", "hunt")),
            MapperPlannedRegion("roshamuul_depths_landmass", "landmass", "dark_cavern", (1174, 1090), (96, 72), "roshamuul_dark", ("landmass", "hunt")),
            MapperPlannedRegion("boss_islet", "landmass", "ancient_boss_chamber", (1248, 1016), (34, 28), "boss_chamber", ("landmass", "boss")),
            MapperPlannedRegion("western_swamp_water", "water", "swamp_inlet", (920, 1012), (34, 62), "water", ("water_cut", "dock_relation")),
            MapperPlannedRegion("city_safe_core", "safe_zone", "pz_city_core", (1000, 1000), (42, 36), "plaza", ("pz", "depot", "temple")),
            ]
        )
        plan.routes.extend(
            [
            MapperPlannedRoute("dock_to_plaza", "city_route", ((925, 1006), (952, 1004), (980, 1001), (1000, 1000)), 2, "road", ("safe_return", "land_connector")),
            MapperPlannedRoute("plaza_to_hunts", "primary_route", ((1000, 1000), (1026, 996), (1068, 1002), (1115, 1006)), 3, "road", ("readable_path", "land_connector")),
            MapperPlannedRoute("northwest_housing_loop", "city_route", ((1000, 1000), (996, 980), (985, 964), (960, 952), (948, 956)), 2, "road", ("npc_walk", "land_connector")),
            MapperPlannedRoute("southern_house_loop", "city_route", ((1000, 1000), (1014, 1018), (1028, 1038), (1010, 1052), (972, 1056)), 2, "road", ("npc_walk", "land_connector")),
            MapperPlannedRoute("krailos_branch", "hunt_route", ((1115, 1006), (1145, 1008), (1180, 1006), (1232, 1016)), 3, "hunt_corridor", ("kite_route", "land_connector")),
            MapperPlannedRoute("roshamuul_branch", "hunt_route", ((1140, 1030), (1134, 1068), (1175, 1090), (1220, 1106)), 3, "hunt_corridor", ("danger_route", "land_connector")),
            MapperPlannedRoute("transition_branch", "hunt_route", ((1115, 1006), (1118, 1038), (1138, 1058), (1168, 1078)), 3, "hunt_corridor", ("alternate_route", "land_connector")),
            ]
        )
    _apply_validated_experience_guidance(plan, guidance)
    _apply_semantic_ai_guidance(plan, semantic_ai_guidance or {})
    return plan


def _compact_objective_kind(objective: str) -> str:
    normalized = "".join(
        char for char in unicodedata.normalize("NFKD", objective.casefold())
        if not unicodedata.combining(char)
    )
    explicit_compact = any(feature in normalized for feature in (
        "pequena", "pequeno", "small", "compacta", "compacto", "isla", "island",
    ))
    if explicit_compact and "krailos" in normalized:
        return "krailos_island"
    large_features = (
        "ciudad", "city", "town", "hunt", "depot", "temple", "templo",
        "quest", "boss", "casas", "houses", "necro", "vertical slice",
    )
    if not explicit_compact and any(feature in normalized for feature in large_features):
        return ""
    if any(feature in normalized for feature in ("rio", "river", "lago", "lake", "playa", "beach")):
        return "river_nature"
    if any(feature in normalized for feature in ("isla", "island", "naturaleza", "nature", "bosque", "forest")):
        return "nature_island"
    return ""


def _objective_anchor(objective: str) -> tuple[int, int, int]:
    """Read an explicit RME position while keeping the canonical center as fallback."""
    match = re.search(
        r"x\s*[:=]\s*(\d+)\D{0,20}y\s*[:=]\s*(\d+)\D{0,20}(?:z\s*[:=]\s*)?(\d{1,2})",
        objective,
        flags=re.IGNORECASE,
    )
    if match is None:
        return 1000, 1000, 7
    x, y, z = (int(value) for value in match.groups())
    if not (0 <= x <= 0xFFFF and 0 <= y <= 0xFFFF and 0 <= z <= 15):
        raise ValueError(f"Objective contains an invalid OTBM position: {x},{y},{z}")
    return x, y, z


def _objective_town_name(objective: str) -> str:
    match = re.search(
        r"\btown(?:\s+name)?\s*(?::|=)?\s*([A-Za-z][A-Za-z0-9 _-]{0,39}?)(?=\s+(?:x\s*[:=]|coordenadas?|coordinates?)|[,;]|$)",
        objective,
        flags=re.IGNORECASE,
    )
    return match.group(1).strip() if match else "AI Generated Area"


def _populate_compact_plan(
    plan: MapperPlan,
    kind: str,
    anchor: tuple[int, int, int],
) -> None:
    """Build original test-sized geometry without inheriting NECRO city/hunt masks."""
    plan.policies.update({
        "plan_scale": "compact",
        "compact_objective_kind": kind,
        "minimum_hunt_routes": 0,
        "semantic_ai_water_margin": 18,
        "semantic_ai_nature_density": 0.78,
    })
    cx, cy, _z = anchor
    if kind == "krailos_island":
        plan.policies.update({
            "recommended_level": 300,
            "official_autoborder_required": True,
            "material_safety_qa_required": True,
            "playability_qa_required": True,
            "minimum_hunt_routes": 3,
        })
        plan.regions.extend([
            MapperPlannedRegion(
                "ikaro_krailos_island", "landmass", "krailos_dry_hunt", (cx, cy),
                (45, 37), "transition", ("landmass", "nature", "hunt"),
            ),
            MapperPlannedRegion(
                "ikaro_oasis", "landmass", "krailos_oasis", (cx - 17, cy + 13),
                (16, 12), "krailos grass", ("landmass", "nature"),
            ),
            MapperPlannedRegion(
                "ikaro_mountain", "landmass", "krailos_rock_plateau", (cx + 20, cy - 15),
                (19, 14), "mountain", ("landmass", "mountain"),
            ),
            MapperPlannedRegion(
                "ika_temple_safe_core", "safe_zone", "krailos_pz_temple", (cx, cy),
                (6, 5), "civic_floor", ("pz", "temple"),
            ),
        ])
        plan.routes.extend([
            MapperPlannedRoute(
                "ika_temple_approach", "city_route",
                ((cx, cy + 4), (cx - 4, cy + 11), (cx - 15, cy + 18)),
                2, "krailos dirt", ("safe_return", "readable_path"),
            ),
            MapperPlannedRoute(
                "ikaro_west_kite_loop", "hunt_route",
                ((cx - 15, cy + 18), (cx - 31, cy + 12), (cx - 34, cy - 8), (cx - 20, cy - 23)),
                3, "krailos dirt", ("kite_route", "alternate_route"),
            ),
            MapperPlannedRoute(
                "ikaro_mountain_route", "hunt_route",
                ((cx - 20, cy - 23), (cx, cy - 27), (cx + 20, cy - 18), (cx + 30, cy - 4)),
                3, "rock soil", ("danger_route", "mountain_access"),
            ),
            MapperPlannedRoute(
                "ikaro_east_return", "hunt_route",
                ((cx + 30, cy - 4), (cx + 32, cy + 17), (cx + 14, cy + 27), (cx - 15, cy + 18)),
                3, "krailos dirt", ("kite_route", "safe_return"),
            ),
        ])
        return
    plan.regions.append(
        MapperPlannedRegion(
            "original_nature_island", "landmass", "humid_nature", (cx, cy),
            (34, 26), "grass", ("landmass", "nature"),
        )
    )
    plan.regions.append(
        MapperPlannedRegion(
            "small_original_beach", "landmass", "natural_beach", (cx + 22, cy + 8),
            (15, 11), "sand", ("landmass", "beach"),
        )
    )
    if kind == "river_nature":
        plan.routes.append(
            MapperPlannedRoute(
                "meandering_river", "water_route",
                ((cx - 30, cy - 14), (cx - 18, cy - 7), (cx - 6, cy - 3), (cx + 5, cy + 4), (cx + 17, cy + 9), (cx + 31, cy + 15)),
                4, "water", ("water_cut",),
            )
        )
    else:
        plan.routes.append(
            MapperPlannedRoute(
                "nature_walk", "nature_route", ((cx - 22, cy + 8), (cx - 8, cy + 1), (cx + 8, cy - 6), (cx + 22, cy - 2)),
                1, "road", ("readable_path",),
            )
        )


def _apply_validated_experience_guidance(plan: MapperPlan, guidance: dict[str, Any]) -> None:
    """Apply promoted abstract lessons through a small, auditable policy allowlist."""
    applied: list[dict[str, Any]] = []
    for polarity, key in (("positive", "positive_rules"), ("negative", "negative_constraints")):
        for entry in list(guidance.get(key, ()))[:24]:
            if not isinstance(entry, dict) or float(entry.get("confidence", 0.0)) < 0.65:
                continue
            category = str(entry.get("category", "")).casefold()
            text = _abstract_rule_text(entry.get("rule")).casefold()
            corpus = f"{category} {text}"
            effects: list[str] = []
            if any(token in corpus for token in ("nature", "vegetation", "doodad", "plant")):
                density = 0.075
                if any(token in corpus for token in ("dense", "high density", "abundant", "cluster")):
                    density = 0.11
                elif any(token in corpus for token in ("sparse", "low density", "light vegetation")):
                    density = 0.045
                if polarity == "positive":
                    plan.reference_style["nature_per_ground_tile"] = density
                    effects.append(f"nature_density={density}")
            if any(token in corpus for token in ("route", "connect", "kite", "return path")):
                plan.policies["minimum_hunt_routes"] = max(
                    3, int(plan.policies.get("minimum_hunt_routes", 3))
                )
                plan.policies["connectivity_qa_required"] = True
                effects.append("connectivity_qa_required")
            if any(token in corpus for token in ("stairs", "ramp", "vertical", "multi-floor", "multifloor")):
                plan.policies["vertical_connectivity_qa_required"] = True
                effects.append("vertical_connectivity_qa_required")
            if "border" in corpus:
                plan.policies["official_autoborder_required"] = True
                effects.append("official_autoborder_required")
            if any(token in corpus for token in ("wall", "door", "window")):
                plan.policies["wall_alignment_qa_required"] = True
                effects.append("wall_alignment_qa_required")
            if any(token in corpus for token in ("ground", "floor", "material safety")):
                plan.policies["material_safety_qa_required"] = True
                effects.append("material_safety_qa_required")
            if any(token in corpus for token in ("black tile", "missing sprite", "placeholder")):
                plan.policies["sprite_backed_visual_qa_required"] = True
                effects.append("sprite_backed_visual_qa_required")
            if any(token in corpus for token in ("copy", "similarity", "source geometry")):
                plan.policies["similarity_guard_required"] = True
                effects.append("similarity_guard_required")
            if "teleport" in corpus and polarity == "negative":
                plan.policies["no_teleports"] = True
                effects.append("no_teleports")
            if effects:
                applied.append({
                    "rule_id": str(entry.get("id", "")),
                    "polarity": polarity,
                    "category": category,
                    "confidence": round(float(entry.get("confidence", 0.0)), 6),
                    "effects": sorted(set(effects)),
                })
    plan.policies["validated_experience_applied"] = bool(applied)
    plan.policies["validated_experience_effects"] = applied
    plan.policies["validated_experience_accepts_raw_ids"] = False
    plan.policies["validated_experience_accepts_source_coordinates"] = False


def _abstract_rule_text(value: Any) -> str:
    if isinstance(value, str):
        return value[:2000]
    if isinstance(value, dict):
        return " ".join(
            _abstract_rule_text(item)
            for key, item in sorted(value.items())
            if str(key).casefold() not in {"x", "y", "z", "position", "coordinates", "item_id", "id"}
        )[:2000]
    if isinstance(value, (list, tuple)):
        return " ".join(_abstract_rule_text(item) for item in value[:32])[:2000]
    return str(value)[:500]


def _apply_semantic_ai_guidance(plan: MapperPlan, guidance: dict[str, Any]) -> None:
    """Apply bounded geometry and certified material intents, never raw IDs."""
    parameters = guidance.get("parameters", {}) if isinstance(guidance, dict) else {}
    if not isinstance(parameters, dict) or not parameters:
        plan.policies["semantic_ai_applied"] = False
        return
    city_scale = max(0.75, min(1.25, float(parameters.get("city_scale", 1.0))))
    hunt_scale = max(0.75, min(1.25, float(parameters.get("hunt_scale", 1.0))))
    route_width = max(2, min(4, int(parameters.get("route_width", 3))))
    scaled_regions: list[MapperPlannedRegion] = []
    for region in plan.regions:
        scale = city_scale if "city" in region.tags else hunt_scale if "hunt" in region.tags else 1.0
        scaled_regions.append(MapperPlannedRegion(
            region.name, region.role, region.style, region.anchor,
            (max(8, round(region.radius[0] * scale)), max(8, round(region.radius[1] * scale))),
            region.terrain, region.tags,
        ))
    plan.regions = scaled_regions
    plan.routes = [MapperPlannedRoute(route.name, route.role, route.points, route_width if route.role == "hunt_route" else max(2, min(route.width, route_width)), route.terrain, route.tags) for route in plan.routes]
    plan.policies.update({
        "semantic_ai_applied": True,
        "semantic_ai_water_margin": max(18, min(40, int(parameters.get("water_margin", 18)))),
        "semantic_ai_nature_density": max(0.10, min(0.90, float(parameters.get("nature_density", 0.45)))),
        "semantic_ai_terrain_irregularity": max(0.10, min(0.90, float(parameters.get("terrain_irregularity", 0.45)))),
        "semantic_ai_verticality": max(0.0, min(1.0, float(parameters.get("verticality", 0.35)))),
        "semantic_ai_material_authority": False,
        "semantic_ai_material_intents_are_allowlisted": True,
    })
    plan.reference_style["semantic_ai"] = {
        "summary": str(guidance.get("summary", ""))[:500],
        "architecture_rules": list(guidance.get("architecture_rules", ()))[:12],
        "biome_rules": list(guidance.get("biome_rules", ()))[:12],
        "negative_constraints": list(guidance.get("negative_constraints", ()))[:12],
        "qa_intent": list(guidance.get("qa_intent", ()))[:12],
        "material_intents": [
            {
                "zone_role": str(intent.get("zone_role", ""))[:80],
                "ground_key": str(intent.get("ground_key", ""))[:120],
                "wall_key": str(intent.get("wall_key", ""))[:120],
                "doodad_keys": [str(key)[:120] for key in list(intent.get("doodad_keys", ()))[:8]],
                "density": max(0.0, min(1.0, float(intent.get("density", 0.5)))),
                "reason": str(intent.get("reason", ""))[:240],
            }
            for intent in list(guidance.get("material_intents", ()))[:16]
            if isinstance(intent, dict)
        ],
        "material_resolution": "Contextual Material Resolver -> certified RME Brush Engine",
    }


def apply_mapper_plan_to_blueprints(
    city_blueprint: dict[str, Any],
    hunt_blueprint: dict[str, Any],
    plan: MapperPlan,
) -> tuple[dict[str, Any], dict[str, Any]]:
    city = dict(city_blueprint)
    hunt = dict(hunt_blueprint)
    city["mapper_planner"] = plan.to_report()
    hunt["mapper_planner"] = {
        "region_names": [region.name for region in plan.regions if "hunt" in region.tags or "boss" in region.tags],
        "route_names": [route.name for route in plan.routes if route.role == "hunt_route"],
        "minimum_hunt_routes": plan.policies["minimum_hunt_routes"],
    }
    city["road_graph"] = [[list(point) for point in route.points] for route in plan.routes if route.role in {"city_route", "primary_route"}]
    hunt["corridors"] = [[list(point) for point in route.points] for route in plan.routes if route.role == "hunt_route"]
    return city, hunt


def mapper_plan_to_color_blueprint(
    plan: MapperPlan,
    *,
    z: int = 7,
    water_margin: int = 18,
    name: str = "mapper-plan",
) -> SemanticColorBlueprint:
    """Rasterize semantic geometry into inspectable RME color submasks."""
    land_regions = [region for region in plan.regions if "landmass" in region.tags]
    if not land_regions:
        raise ValueError("Mapper plan has no landmass regions")
    visual_memory = plan.reference_style.get("visual_memory", {})
    water_target = float(visual_memory.get("water_envelope_target", 0.0))
    ai_water_margin = int(plan.policies.get("semantic_ai_water_margin", water_margin))
    effective_water_margin = max(ai_water_margin, min(40, round(10 + water_target * 80)))
    min_x = min(region.bounds[0] for region in land_regions) - effective_water_margin
    min_y = min(region.bounds[1] for region in land_regions) - effective_water_margin
    max_x = max(region.bounds[2] for region in land_regions) + effective_water_margin
    max_y = max(region.bounds[3] for region in land_regions) + effective_water_margin
    blueprint = SemanticColorBlueprint(
        name=name,
        prompt=plan.objective,
        metadata={
            "source": "MapperPlanner",
            "construction_order": [layer.name for layer in BlueprintLayer],
            "reference_policy": plan.policies.get("reference_policy", ""),
            "reference_style": _safe_reference_summary(plan.reference_style),
            "effective_water_margin": effective_water_margin,
            "plan_scale": plan.policies.get("plan_scale", "full"),
        },
    )
    sea = ((x, y, z) for x in range(min_x, max_x + 1) for y in range(min_y, max_y + 1))
    blueprint.paint(BlueprintLayer.SEA_FOUNDATION, sea, "sea")

    for region in plan.regions:
        if "landmass" not in region.tags:
            continue
        token = _terrain_token(region.terrain)
        x1, y1, x2, y2 = region.bounds
        cells = (
            (x, y, z)
            for x in range(x1, x2 + 1)
            for y in range(y1, y2 + 1)
            if region.contains(x, y)
        )
        blueprint.paint(BlueprintLayer.TERRAIN, cells, token)
        if token == "mountain":
            edge = (
                (x, y, z)
                for x in range(x1, x2 + 1)
                for y in range(y1, y2 + 1)
                if region.contains(x, y)
                and any(not region.contains(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            )
            blueprint.paint(BlueprintLayer.TERRAIN_BORDER, edge, "terrain_border")

    _paint_compact_krailos_ground_mix(blueprint, plan, z)

    terrain_mask = blueprint.mask(BlueprintLayer.TERRAIN)
    for region in (value for value in plan.regions if "water_cut" in value.tags):
        x1, y1, x2, y2 = region.bounds
        terrain_mask.erase(
            (x, y, z)
            for x in range(x1, x2 + 1)
            for y in range(y1, y2 + 1)
            if region.contains(x, y)
        )
    for route in (value for value in plan.routes if "water_cut" in value.tags):
        x1 = min(point[0] for point in route.points) - route.width
        y1 = min(point[1] for point in route.points) - route.width
        x2 = max(point[0] for point in route.points) + route.width
        y2 = max(point[1] for point in route.points) + route.width
        terrain_mask.erase(
            (x, y, z)
            for x in range(x1, x2 + 1)
            for y in range(y1, y2 + 1)
            if distance_to_polyline(x, y, route.points) <= route.width
        )

    ground_selector = ContextualGroundBrushSelector()
    for route in plan.routes:
        if "water_cut" in route.tags:
            continue
        x1 = min(point[0] for point in route.points) - route.width
        y1 = min(point[1] for point in route.points) - route.width
        x2 = max(point[0] for point in route.points) + route.width
        y2 = max(point[1] for point in route.points) + route.width
        cells = (
            (x, y, z)
            for x in range(x1, x2 + 1)
            for y in range(y1, y2 + 1)
            if distance_to_polyline(x, y, route.points) <= route.width
        )
        nearby = min(
            plan.regions,
            key=lambda region: math.hypot(region.anchor[0] - route.points[-1][0], region.anchor[1] - route.points[-1][1]),
        )
        route_token = ground_selector.route_token(
            GroundContext(route.role, route.terrain, route.name, nearby.style)
        )
        blueprint.paint(BlueprintLayer.ROAD, cells, route_token)

    for region in plan.regions:
        if "pz" in region.tags:
            blueprint.paint(BlueprintLayer.GAMEPLAY, [(region.anchor[0], region.anchor[1], z)], "spawn")
    _paint_compact_temple(blueprint, plan, z)
    _paint_original_structures(blueprint, plan, z)
    _paint_hunt_geometry(blueprint, plan, z)
    _paint_multilevel_geometry(blueprint, plan, z)
    _paint_nature_and_decorations(blueprint, plan, z)
    _paint_compact_krailos_landmarks(blueprint, plan, z)
    _paint_vertical_connectors(blueprint, plan, z)
    return blueprint


def _paint_compact_temple(
    blueprint: SemanticColorBlueprint,
    plan: MapperPlan,
    z: int,
) -> None:
    """Paint one small RME-valid temple and preserve its complete PZ interior."""
    temple = next((region for region in plan.regions if "temple" in region.tags), None)
    if temple is None or plan.policies.get("plan_scale") != "compact":
        return
    cx, cy = temple.anchor
    x1, x2, y1, y2 = cx - 5, cx + 5, cy - 4, cy + 4
    footprint = {
        (x, y, z)
        for x in range(x1, x2 + 1)
        for y in range(y1, y2 + 1)
    }
    terrain = set(blueprint.mask(BlueprintLayer.TERRAIN).cells)
    if not footprint.issubset(terrain):
        raise ValueError("Compact temple footprint is outside the planned landmass")
    interior = {
        (x, y, z)
        for x in range(x1 + 1, x2)
        for y in range(y1 + 1, y2)
    }
    perimeter = footprint - interior
    entrance = {(cx + dx, y2, z) for dx in (-1, 0, 1)}
    perimeter.difference_update(entrance)
    blueprint.paint(BlueprintLayer.STRUCTURE_GROUND, footprint, "krailos_temple_floor")
    blueprint.paint(BlueprintLayer.WALL, perimeter, "krailos_temple_wall")
    # Krailos temples use a broad open threshold. A DoorBrush here would make
    # the safe return less readable and contradict the certified reference.
    ornaments = {
        (cx - 3, cy - 2, z): "krailos_banner",
        (cx + 3, cy - 2, z): "krailos_banner",
        (cx - 3, cy + 2, z): "krailos_pot",
        (cx + 3, cy + 2, z): "krailos_pot",
        (cx, cy - 3, z): "krailos_totem",
    }
    for position, token in ornaments.items():
        blueprint.paint(BlueprintLayer.DECORATION, [position], token)
    blueprint.paint(BlueprintLayer.GAMEPLAY, interior, "spawn")
    blueprint.metadata["protection_zone_tiles"] = [list(position) for position in sorted(interior)]
    blueprint.metadata["town"] = {
        "name": str(plan.policies.get("town_name", "AI Generated Area")),
        "temple": [cx, cy, z],
    }
    blueprint.metadata["temple"] = {
        "footprint_tiles": len(footprint),
        "protection_zone_tiles": len(interior),
        "door": None,
        "open_entrance": [list(position) for position in sorted(entrance)],
        "decorations": len(ornaments),
        "spawn": [cx, cy, z],
    }


def _paint_compact_krailos_ground_mix(
    blueprint: SemanticColorBlueprint,
    plan: MapperPlan,
    z: int,
) -> None:
    """Add original organic Krailos ground regions before roads and structures."""
    if plan.policies.get("compact_objective_kind") != "krailos_island":
        return
    island = next((region for region in plan.regions if region.name == "ikaro_krailos_island"), None)
    if island is None:
        return
    cx, cy = island.anchor
    patches = (
        (-23, -10, 12, 7, "krailos_grass"),
        (-15, 17, 10, 6, "krailos_orange"),
        (4, -18, 14, 6, "krailos_grass"),
        (21, -6, 8, 12, "rock_soil"),
        (19, 17, 13, 7, "krailos_yellow"),
        (-3, 20, 9, 5, "rock_soil"),
        (-29, 4, 7, 5, "krailos_purple"),
        (8, 11, 6, 4, "krailos_orange"),
    )
    terrain = blueprint.mask(BlueprintLayer.TERRAIN)
    for ox, oy, radius_x, radius_y, token in patches:
        center_x, center_y = cx + ox, cy + oy
        cells = []
        for x in range(center_x - radius_x, center_x + radius_x + 1):
            for y in range(center_y - radius_y, center_y + radius_y + 1):
                position = (x, y, z)
                if not island.contains(x, y) or terrain.cells.get(position) != "sand":
                    continue
                dx = (x - center_x) / max(1, radius_x)
                dy = (y - center_y) / max(1, radius_y)
                wobble = ((_stable_geometry_hash(x // 3, y // 3, token) % 17) - 8) / 80.0
                if dx * dx + dy * dy + wobble <= 1.0:
                    cells.append(position)
        blueprint.paint(BlueprintLayer.TERRAIN, cells, token)


def _paint_compact_krailos_landmarks(
    blueprint: SemanticColorBlueprint,
    plan: MapperPlan,
    z: int,
) -> None:
    """Place small original Krailos camps from official brush families."""
    if plan.policies.get("compact_objective_kind") != "krailos_island":
        return
    island = next((region for region in plan.regions if region.name == "ikaro_krailos_island"), None)
    if island is None:
        return
    cx, cy = island.anchor
    terrain = set(blueprint.mask(BlueprintLayer.TERRAIN).cells)
    roads = set(blueprint.mask(BlueprintLayer.ROAD).cells)
    structures = set(blueprint.mask(BlueprintLayer.STRUCTURE_GROUND).cells)

    decorations = {
        (cx - 27, cy - 9, z): "krailos_hut",
        (cx - 25, cy - 7, z): "krailos_roof_end",
        (cx + 27, cy + 12, z): "krailos_hut",
        (cx + 25, cy + 10, z): "krailos_roof",
        (cx - 24, cy - 4, z): "krailos_structure_1",
        (cx - 21, cy - 6, z): "krailos_structure_2",
        (cx + 23, cy + 14, z): "krailos_structure_3",
        (cx + 27, cy + 16, z): "krailos_structure_4",
        (cx - 31, cy + 7, z): "krailos_blood",
        (cx + 31, cy - 2, z): "krailos_blood",
    }
    available = terrain - roads - structures
    occupied: set[tuple[int, int, int]] = set()
    painted_decorations = 0
    for requested, token in decorations.items():
        position = _nearest_available_position(requested, available - occupied)
        if position is not None:
            blueprint.paint(BlueprintLayer.DECORATION, [position], token)
            occupied.add(position)
            painted_decorations += 1

    # Two short defensive fragments give WallBrush enough neighbours to choose
    # horizontal, vertical, corner and pole pieces without sealing a route.
    wall_fragments = {
        "krailos_spikes_1": ((cx - 30, cy - 3, z), (1, 0, 0)),
        "krailos_spikes_2": ((cx + 29, cy + 5, z), (0, 1, 0)),
    }
    painted_walls = 0
    for token, (requested, direction) in wall_fragments.items():
        positions = _nearest_available_fragment(requested, direction, available - occupied, length=5)
        blueprint.paint(BlueprintLayer.WALL, positions, token)
        occupied.update(positions)
        painted_walls += len(positions)
    blueprint.metadata["krailos_landmarks"] = {
        "decoration_anchors": painted_decorations,
        "wall_fragment_tiles": painted_walls,
        "families": sorted(set(decorations.values()) | set(wall_fragments)),
        "policy": "original anchors; official RME brush families; no reference geometry copied",
    }


def _nearest_available_position(
    requested: tuple[int, int, int],
    available: set[tuple[int, int, int]],
    radius: int = 10,
) -> tuple[int, int, int] | None:
    x, y, z = requested
    candidates = (
        position for position in available
        if position[2] == z and abs(position[0] - x) <= radius and abs(position[1] - y) <= radius
    )
    return min(
        candidates,
        key=lambda position: (
            abs(position[0] - x) + abs(position[1] - y),
            position[1],
            position[0],
        ),
        default=None,
    )


def _nearest_available_fragment(
    requested: tuple[int, int, int],
    direction: tuple[int, int, int],
    available: set[tuple[int, int, int]],
    *,
    length: int,
    radius: int = 12,
) -> set[tuple[int, int, int]]:
    x, y, z = requested
    dx, dy, dz = direction
    starts = sorted(
        (
            position for position in available
            if position[2] == z and abs(position[0] - x) <= radius and abs(position[1] - y) <= radius
        ),
        key=lambda position: (
            abs(position[0] - x) + abs(position[1] - y),
            position[1],
            position[0],
        ),
    )
    for start in starts:
        fragment = {
            (start[0] + dx * offset, start[1] + dy * offset, start[2] + dz * offset)
            for offset in range(length)
        }
        if fragment <= available:
            return fragment
    return set()


def _terrain_token(terrain: str) -> str:
    normalized = terrain.lower()
    if "krailos grass" in normalized or "krailos oasis" in normalized:
        return "krailos_grass"
    if "krailos orange" in normalized:
        return "krailos_orange"
    if "krailos yellow" in normalized:
        return "krailos_yellow"
    if "krailos purple" in normalized:
        return "krailos_purple"
    if "krailos dirt" in normalized or "krailos dry" in normalized:
        return "krailos_dirt"
    if "swamp" in normalized or "water" in normalized:
        return "swamp"
    if "dark" in normalized or "mountain" in normalized or "rock" in normalized:
        return "mountain"
    if "dry" in normalized or "sand" in normalized or "transition" in normalized:
        return "sand"
    return "grass"


def _paint_original_structures(blueprint: SemanticColorBlueprint, plan: MapperPlan, z: int) -> None:
    city = next((region for region in plan.regions if "city" in region.tags and "landmass" in region.tags), None)
    settlements = list(plan.architecture.get("settlements", ()))
    if city is None and not settlements:
        return
    reference_tiles = int(plan.reference_style.get("median_house_component_tiles", 0) or 0)
    side = max(6, min(13, int(math.sqrt(reference_tiles)) if reference_tiles else 9))
    planned_buildings = [
        building
        for settlement in settlements
        for building in settlement.get("buildings", ())
        if not (
            plan.policies.get("plan_scale") == "compact"
            and str(building.get("function", "")) == "temple"
            and any("temple" in region.tags for region in plan.regions)
        )
    ]
    offsets = ((-48, -30), (-22, -42), (18, -40), (48, -26), (-50, 25), (-20, 40), (20, 42), (50, 24))
    terrain = set(blueprint.mask(BlueprintLayer.TERRAIN).cells)
    occupied: set[tuple[int, int, int]] = set()
    generated_house_count = 0
    candidates = planned_buildings
    if not candidates and city is not None:
        candidates = [
            {"center": [city.anchor[0] + dx, city.anchor[1] + dy], "width": side + index % 3 - 1, "height": max(6, side - index % 2), "floors": 1}
            for index, (dx, dy) in enumerate(offsets)
        ]
    for index, building in enumerate(candidates):
        width = int(building["width"])
        height = int(building["height"])
        x1 = int(building["center"][0]) - width // 2
        y1 = int(building["center"][1]) - height // 2
        x2, y2 = x1 + width - 1, y1 + height - 1
        interior = {(x, y, z) for x in range(x1 + 1, x2) for y in range(y1 + 1, y2)}
        walls = {
            (x, y, z)
            for x in range(x1, x2 + 1)
            for y in range(y1, y2 + 1)
            if x in (x1, x2) or y in (y1, y2)
        }
        function = str(building.get("function", "house"))
        doorway = ((x1 + x2) // 2, y2, z)
        footprint = interior | walls | {doorway}
        if not footprint.issubset(terrain):
            continue
        walls.discard(doorway)
        blueprint.paint(BlueprintLayer.STRUCTURE_GROUND, interior | walls, "interior")
        blueprint.paint(BlueprintLayer.WALL, walls, "wall")
        if function != "temple":
            blueprint.paint(BlueprintLayer.DOOR_WINDOW, [doorway], "door")
        occupied.update(footprint)
        generated_house_count += 1
    blueprint.metadata["generated_structure_tiles"] = len(occupied)
    blueprint.metadata["generated_house_count"] = generated_house_count


def _paint_nature_and_decorations(blueprint: SemanticColorBlueprint, plan: MapperPlan, z: int) -> None:
    terrain = blueprint.mask(BlueprintLayer.TERRAIN).cells
    roads = set(blueprint.mask(BlueprintLayer.ROAD).cells)
    structures = set(blueprint.mask(BlueprintLayer.STRUCTURE_GROUND).cells)
    learned_density = float(plan.reference_style.get("nature_per_ground_tile", 0.075))
    semantic_density = float(plan.policies.get("semantic_ai_nature_density", 0.45))
    semantic_density = 0.035 + max(0.10, min(0.90, semantic_density)) * 0.125
    nature_density = max(0.035, min(0.16, (learned_density * 0.65) + (semantic_density * 0.35)))
    decoration_density = max(0.012, min(0.09, float(plan.reference_style.get("decoration_per_ground_tile", 0.035))))
    nature_mod = max(6, round(1 / nature_density))
    decoration_mod = max(11, round(1 / decoration_density))
    visual_grammar = plan.reference_style.get("visual_grammar", {})
    visual_memory = plan.reference_style.get("visual_memory", {})
    mean_nature_neighbors = float(visual_grammar.get("mean_nature_neighbors", 0.0))
    memory_cluster_bias = float(visual_memory.get("nature_cluster_bias", 0.0))
    grammar_cluster_cells = round(mean_nature_neighbors) + 2
    memory_cluster_cells = round(memory_cluster_bias * 10) if memory_cluster_bias else grammar_cluster_cells
    cluster_cells = max(2, min(7, round((grammar_cluster_cells + memory_cluster_cells) / 2)))
    family_cursor: dict[str, int] = {}
    for position, token in terrain.items():
        if position[2] != z or position in roads or position in structures:
            continue
        x, y, _ = position
        cluster_seed = _stable_geometry_hash(x // 7, y // 7, plan.objective + "nature-cluster") % 10
        clustered_mod = max(3, nature_mod // 3) if cluster_seed < cluster_cells else nature_mod * 4
        terrain_density = 1 if token in {"grass", "swamp", "krailos_grass"} else 2 if token in {"sand", "krailos_dirt", "krailos_orange", "krailos_yellow", "krailos_purple"} else 3
        supported_nature = {"grass", "swamp", "sand", "mountain", "krailos_dirt", "krailos_grass", "krailos_orange", "krailos_yellow", "krailos_purple", "rock_soil"}
        if token in supported_nature and _stable_geometry_hash(
            x, y, plan.objective + "nature"
        ) % (clustered_mod * terrain_density) == 0:
            nature_tokens = {
                "grass": ("nature", "forest_shrub", "swamp_plant"),
                "swamp": ("swamp_tree", "swamp_plant", "forest_shrub"),
                "sand": ("krailos_rocks", "krailos_plant", "dry_rock_detail"),
                "mountain": ("dry_rock_detail", "dark_fungi"),
                "krailos_dirt": ("krailos_rocks", "krailos_plant"),
                "krailos_grass": ("krailos_plant", "krailos_rocks", "forest_shrub"),
                "krailos_orange": ("krailos_rocks", "krailos_plant"),
                "krailos_yellow": ("krailos_rocks", "krailos_plant", "krailos_mountains"),
                "krailos_purple": ("krailos_rocks", "krailos_plant", "krailos_tanned_skin"),
                "rock_soil": ("krailos_rocks", "dry_rock_detail"),
            }.get(token, ("nature",))
            cursor = family_cursor.get(token)
            if cursor is None:
                cursor = (_stable_geometry_hash(x, y, plan.objective + "nature-family") >> 7)
            selected = nature_tokens[cursor % len(nature_tokens)]
            family_cursor[token] = cursor + 1
            blueprint.paint(BlueprintLayer.NATURE, [position], selected)
        elif _stable_geometry_hash(x // 4, y // 4, plan.objective + "decoration-cluster") % 7 < 2 and _stable_geometry_hash(x, y, plan.objective + "decoration") % decoration_mod == 0:
            if plan.policies.get("compact_objective_kind") == "krailos_island":
                families = ("krailos_fence", "krailos_tanned_skin", "krailos_thing", "krailos_totem_skull")
                token_id = families[_stable_geometry_hash(x, y, plan.objective + "krailos-detail") % len(families)]
            else:
                token_id = "decoration"
            blueprint.paint(BlueprintLayer.DECORATION, [position], token_id)


def _paint_hunt_geometry(blueprint: SemanticColorBlueprint, plan: MapperPlan, z: int) -> None:
    terrain = set(blueprint.mask(BlueprintLayer.TERRAIN).cells)
    routes = set(blueprint.mask(BlueprintLayer.ROAD).cells)
    complexes = 0
    chamber_tiles = 0
    for region in (value for value in plan.regions if "hunt" in value.tags):
        if "dry" in region.style or "krailos" in region.name:
            created, painted = _paint_krailos_ruins(blueprint, region, terrain, routes, z)
        else:
            created, painted = _paint_dark_chambers(blueprint, region, terrain, routes, z)
        complexes += created
        chamber_tiles += painted
    blueprint.metadata["generated_hunt_complexes"] = complexes
    blueprint.metadata["generated_hunt_chamber_tiles"] = chamber_tiles


def _paint_krailos_ruins(
    blueprint: SemanticColorBlueprint,
    region: MapperPlannedRegion,
    terrain: set[tuple[int, int, int]],
    routes: set[tuple[int, int, int]],
    z: int,
) -> tuple[int, int]:
    offsets = ((-38, -24), (18, -22), (34, 20), (-20, 24))
    created = painted = 0
    for index, (dx, dy) in enumerate(offsets):
        width = 15 + (index % 2) * 4
        height = 11 + ((index + 1) % 2) * 4
        cx, cy = region.anchor[0] + dx, region.anchor[1] + dy
        x1, x2 = cx - width // 2, cx + width // 2
        y1, y2 = cy - height // 2, cy + height // 2
        footprint = {
            (x, y, z)
            for x in range(x1, x2 + 1)
            for y in range(y1, y2 + 1)
        }
        if not footprint.issubset(terrain):
            continue
        perimeter = {
            position
            for position in footprint
            if position[0] in (x1, x2) or position[1] in (y1, y2)
        }
        # Broken walls create several valid entrances and avoid sealed decorative boxes.
        walls = {
            position
            for position in perimeter
            if _stable_geometry_hash(position[0], position[1], region.name) % 7 not in (0, 1)
            and position not in routes
        }
        blueprint.paint(BlueprintLayer.STRUCTURE_GROUND, footprint, "krailos_floor")
        blueprint.paint(BlueprintLayer.WALL, walls, "ruin_wall")
        decoration = {
            position
            for position in footprint - walls - routes
            if _stable_geometry_hash(position[0], position[1], region.name + "ruins") % 23 == 0
        }
        blueprint.paint(BlueprintLayer.DECORATION, decoration, "decoration")
        created += 1
        painted += len(footprint)
    return created, painted


def _paint_dark_chambers(
    blueprint: SemanticColorBlueprint,
    region: MapperPlannedRegion,
    terrain: set[tuple[int, int, int]],
    routes: set[tuple[int, int, int]],
    z: int,
) -> tuple[int, int]:
    centers = (
        (region.anchor[0] - 38, region.anchor[1] - 24, 15, 11),
        (region.anchor[0] + 4, region.anchor[1] - 10, 19, 14),
        (region.anchor[0] + 42, region.anchor[1] + 8, 16, 12),
        (region.anchor[0] - 12, region.anchor[1] + 34, 18, 13),
    )
    chambers: list[set[tuple[int, int, int]]] = []
    for cx, cy, rx, ry in centers:
        chamber = {
            (x, y, z)
            for x in range(cx - rx, cx + rx + 1)
            for y in range(cy - ry, cy + ry + 1)
            if (x, y, z) in terrain
        }
        if len(chamber) >= 80:
            chambers.append(chamber)
    floor = set().union(*chambers) if chambers else set()
    for first, second in zip(centers, centers[1:]):
        points = ((first[0], first[1]), (second[0], second[1]))
        corridor = {
            (x, y, z)
            for x in range(min(first[0], second[0]) - 3, max(first[0], second[0]) + 4)
            for y in range(min(first[1], second[1]) - 3, max(first[1], second[1]) + 4)
            if distance_to_polyline(x, y, points) <= 3 and (x, y, z) in terrain
        }
        floor.update(corridor)
    blueprint.paint(BlueprintLayer.STRUCTURE_GROUND, floor, "dark_floor")
    boundary = {
        position
        for position in floor
        if any((position[0] + dx, position[1] + dy, z) not in floor for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    }
    openings = _compact_route_openings(boundary & routes)
    boundary.difference_update(openings)
    boundary = {
        position
        for position in boundary
        if any(
            (position[0] + dx, position[1] + dy, position[2]) in boundary
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        )
    }
    blueprint.paint(BlueprintLayer.WALL, boundary, "roshamuul_wall")
    dangerous = {
        position
        for position in floor - boundary - routes
        if _stable_geometry_hash(position[0], position[1], region.name + "danger") % 29 == 0
    }
    blueprint.paint(BlueprintLayer.DECORATION, dangerous, "decoration")
    return len(chambers), len(floor)


def _paint_vertical_connectors(blueprint: SemanticColorBlueprint, plan: MapperPlan, z: int) -> None:
    if plan.policies.get("plan_scale") == "compact":
        # Compact z7 islands do not advertise isolated stairs without a designed
        # destination floor. Vertical links are added only by a multilevel plan.
        return
    for index, route in enumerate(route for route in plan.routes if route.role == "hunt_route"):
        if len(route.points) < 2:
            continue
        point = route.points[len(route.points) // 2]
        position = (point[0], point[1], z)
        token = "stairs" if index % 2 == 0 else "ramp"
        blueprint.paint(BlueprintLayer.STAIRS_RAMP, [position], token)
        blueprint.paint(BlueprintLayer.STRUCTURE_GROUND, [(point[0], point[1] - 1, z - 1)], "interior")


def _paint_multilevel_geometry(blueprint: SemanticColorBlueprint, plan: MapperPlan, z: int) -> None:
    city = next((region for region in plan.regions if "city" in region.tags and "landmass" in region.tags), None)
    boss = next((region for region in plan.regions if "boss" in region.tags and "landmass" in region.tags), None)
    links: list[dict[str, Any]] = []
    if city is not None:
        _paint_city_roofs(blueprint, plan, city, z)
        links.extend(_paint_city_tower(blueprint, city, z))
    if boss is not None:
        links.extend(_paint_mountain_terraces(blueprint, boss, z))
    blueprint.metadata["vertical_links"] = links
    blueprint.metadata["vertical_link_count"] = len(links)
    blueprint.metadata["designed_floors"] = sorted({position[2] for position in blueprint.positions if 0 <= position[2] <= 7})


def _paint_city_roofs(
    blueprint: SemanticColorBlueprint,
    plan: MapperPlan,
    city: MapperPlannedRegion,
    z: int,
) -> None:
    planned = [
        building
        for settlement in plan.architecture.get("settlements", ())
        for building in settlement.get("buildings", ())
    ]
    if not planned:
        planned = [
            {"center": [city.anchor[0] + dx, city.anchor[1] + dy], "width": 9, "height": 7}
            for dx, dy in ((-48, -30), (-22, -42), (48, -26), (-50, 25), (-20, 40), (20, 42), (50, 24))
        ]
    for building in planned:
        half_width = max(3, int(building["width"]) // 2)
        half_height = max(2, int(building["height"]) // 2)
        cx, cy = map(int, building["center"])
        roof = {
            (cx + x, cy + y, z - 1)
            for x in range(-half_width, half_width + 1)
            for y in range(-half_height, half_height + 1)
            if (cx + x, cy + y, z) in blueprint.mask(BlueprintLayer.STRUCTURE_GROUND).cells
        }
        blueprint.paint(BlueprintLayer.ROOF, roof, "brown_bamboo_roof")


def _compact_route_openings(candidates: set[tuple[int, int, int]]) -> set[tuple[int, int, int]]:
    remaining = set(candidates)
    openings: set[tuple[int, int, int]] = set()
    while remaining:
        start = remaining.pop()
        component = {start}
        pending = [start]
        while pending:
            x, y, z = pending.pop()
            for neighbor in ((x - 1, y, z), (x + 1, y, z), (x, y - 1, z), (x, y + 1, z)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    pending.append(neighbor)
        openings.add(sorted(component)[len(component) // 2])
    return openings


def _paint_city_tower(
    blueprint: SemanticColorBlueprint,
    city: MapperPlannedRegion,
    z: int,
) -> list[dict[str, Any]]:
    cx, cy = city.anchor[0] + 18, city.anchor[1] - 40
    sizes = {7: (5, 4), 6: (5, 4), 5: (4, 3), 4: (4, 3), 3: (3, 3), 2: (3, 2), 1: (2, 2)}
    links: list[dict[str, Any]] = []
    for floor, (rx, ry) in sizes.items():
        footprint = {
            (x, y, floor)
            for x in range(cx - rx, cx + rx + 1)
            for y in range(cy - ry, cy + ry + 1)
        }
        walls = {
            position
            for position in footprint
            if position[0] in (cx - rx, cx + rx) or position[1] in (cy - ry, cy + ry)
        }
        blueprint.paint(BlueprintLayer.STRUCTURE_GROUND, footprint, "interior")
        blueprint.paint(BlueprintLayer.WALL, walls, "wall")
        if floor > 1:
            source = (cx, cy + min(1, ry - 1), floor)
            destination = (cx, cy + min(1, sizes[floor - 1][1] - 1), floor - 1)
            blueprint.paint(BlueprintLayer.STAIRS_RAMP, [source], "gray_stone_stairs")
            links.append({"kind": "stairs", "from": source, "to": destination})
    cap = {
        (x, y, 0)
        for x in range(cx - 2, cx + 3)
        for y in range(cy - 2, cy + 3)
        if abs(x - cx) + abs(y - cy) <= 3
    }
    blueprint.paint(BlueprintLayer.ROOF, cap, "brown_bamboo_roof")
    source = (cx, cy, 1)
    destination = (cx, cy, 0)
    blueprint.paint(BlueprintLayer.STAIRS_RAMP, [source], "gray_stone_stairs")
    links.append({"kind": "stairs", "from": source, "to": destination})
    return links


def _paint_mountain_terraces(
    blueprint: SemanticColorBlueprint,
    boss: MapperPlannedRegion,
    z: int,
) -> list[dict[str, Any]]:
    cx, cy = boss.anchor
    levels = {z - 1: (22, 16), z - 2: (15, 11), z - 3: (9, 7)}
    links: list[dict[str, Any]] = []
    previous_floor = z
    previous_point = (cx, cy + boss.radius[1] // 2, z)
    for floor, (rx, ry) in levels.items():
        terrain = {
            (x, y, floor)
            for x in range(cx - rx, cx + rx + 1)
            for y in range(cy - ry, cy + ry + 1)
            if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0
        }
        edge = {
            position
            for position in terrain
            if any((position[0] + dx, position[1] + dy, floor) not in terrain for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        }
        blueprint.paint(BlueprintLayer.TERRAIN, terrain, "mountain")
        blueprint.paint(BlueprintLayer.TERRAIN_BORDER, edge, "terrain_border")
        destination = (cx, cy + max(0, ry - 2), floor)
        blueprint.paint(BlueprintLayer.STAIRS_RAMP, [previous_point], "swamp_clay_ramp")
        links.append({"kind": "ramp", "from": previous_point, "to": destination})
        previous_floor = floor
        previous_point = destination
    assert previous_floor == z - 3
    return links


def _stable_geometry_hash(x: int, y: int, salt: str) -> int:
    return abs(x * 73_856_093 ^ y * 19_349_663 ^ sum((i + 1) * ord(c) for i, c in enumerate(salt)))


def _safe_reference_summary(profile: dict[str, Any]) -> dict[str, Any]:
    summary = {
        key: profile[key]
        for key in (
            "source_sha256", "nodes_scanned", "tiles_scanned", "truncated",
            "mean_stack_depth", "median_house_component_tiles",
            "decoration_per_ground_tile", "nature_per_ground_tile", "multi_floor_ratio", "policy",
        )
        if key in profile
    }
    grammar = profile.get("visual_grammar")
    if isinstance(grammar, dict):
        summary["visual_grammar"] = {
            key: grammar[key]
            for key in (
                "tiles_sampled",
                "mean_nature_neighbors",
                "mean_wall_neighbors",
                "same_ground_neighbor_ratio",
                "border_on_transition_ratio",
                "policy",
            )
            if key in grammar
        }
    composition = profile.get("composition_reference")
    if isinstance(composition, dict):
        summary["composition_reference"] = {
            "reference_count": int(composition.get("reference_count", 0)),
            "aggregate": dict(composition.get("aggregate", {})),
            "policy": str(composition.get("policy", "")),
        }
    visual_memory = profile.get("visual_memory")
    if isinstance(visual_memory, dict):
        summary["visual_memory"] = {
            key: visual_memory[key]
            for key in (
                "reference_count",
                "architectural_edge_target",
                "water_envelope_target",
                "nature_cluster_bias",
                "dark_hunt_contrast_target",
                "requires_multifloor",
                "requires_roofs",
                "requires_wall_continuity",
                "semantic_evidence",
            )
            if key in visual_memory
        }
        summary["visual_memory"]["profile_tags"] = sorted(
            visual_memory.get("profiles_by_tag", {})
        )
        summary["visual_memory"]["top_cooccurrences"] = dict(
            list(visual_memory.get("semantic_cooccurrence", {}).items())[:12]
        )
    return summary


def distance_to_polyline(x: int, y: int, points: tuple[Point, ...]) -> float:
    if not points:
        return float("inf")
    if len(points) == 1:
        return math.hypot(x - points[0][0], y - points[0][1])
    return min(distance_to_segment(x, y, a, b) for a, b in zip(points, points[1:]))


def distance_to_segment(x: int, y: int, a: Point, b: Point) -> float:
    ax, ay = a
    bx, by = b
    dx = bx - ax
    dy = by - ay
    if dx == 0 and dy == 0:
        return math.hypot(x - ax, y - ay)
    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / float(dx * dx + dy * dy)))
    px = ax + t * dx
    py = ay + t * dy
    return math.hypot(x - px, y - py)
