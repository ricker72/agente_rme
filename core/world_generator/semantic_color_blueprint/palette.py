from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Iterable

from rme_rendering.rme_mapcolors import (
    ROLE_MAPCOLORS,
    rme_minimap_color_to_rgb,
)

from .models import BlueprintLayer


@dataclass(frozen=True)
class SemanticColorToken:
    token_id: str
    layer: BlueprintLayer
    mapcolor: int
    role: str
    brush_name: str = ""
    brush_type: str = ""
    ground_ids: tuple[int, ...] = ()
    item_ids: tuple[int, ...] = ()
    composites: tuple[tuple[tuple[int, int, int, int], ...], ...] = ()
    material_keywords: tuple[str, ...] = ()
    requires_ground: bool = False

    @property
    def rgb(self) -> tuple[int, int, int]:
        return rme_minimap_color_to_rgb(self.mapcolor)

    @property
    def resolved(self) -> bool:
        return bool(self.ground_ids or self.item_ids or self.composites)


class SemanticColorPalette:
    """Layer-aware palette; equal RME colors remain semantically distinct."""

    def __init__(self, tokens: Iterable[SemanticColorToken] = ()) -> None:
        self.tokens: dict[str, SemanticColorToken] = {}
        for token in tokens:
            self.register(token)

    def register(self, token: SemanticColorToken) -> None:
        existing = self.tokens.get(token.token_id)
        if existing and existing.layer != token.layer:
            raise ValueError(f"Token {token.token_id!r} already belongs to {existing.layer.name}")
        self.tokens[token.token_id] = token

    def get(self, token_id: str, layer: BlueprintLayer | None = None) -> SemanticColorToken:
        try:
            token = self.tokens[token_id]
        except KeyError as exc:
            raise KeyError(f"Unknown semantic color token: {token_id}") from exc
        if layer is not None and token.layer != layer:
            raise ValueError(
                f"Token {token_id!r} belongs to {token.layer.name}, not {layer.name}"
            )
        return token

    def token_for_color(self, layer: BlueprintLayer, rgb: tuple[int, int, int]) -> SemanticColorToken:
        candidates = [token for token in self.tokens.values() if token.layer == layer and token.rgb == rgb]
        if len(candidates) != 1:
            raise ValueError(
                f"Color {rgb} in {layer.name} resolves to {len(candidates)} tokens; "
                "use a palette manifest to disambiguate"
            )
        return candidates[0]

    def bind_rme_brush_engine(self, engine: Any) -> "SemanticColorPalette":
        """Resolve semantic names against brushes already filtered by official flags."""
        bound = SemanticColorPalette()
        collections = {
            "ground": getattr(engine, "ground_brushes", {}),
            "doodad": getattr(engine, "doodad_brushes", {}),
            "wall": getattr(engine, "wall_brushes", {}),
            "table": getattr(engine, "table_brushes", {}),
            "carpet": getattr(engine, "carpet_brushes", {}),
            "wall decoration": getattr(engine, "wall_decoration_brushes", {}),
        }
        for token in self.tokens.values():
            collection = collections.get(token.brush_type, {})
            match = _find_brush(collection, token.brush_name, token.material_keywords)
            if match is None:
                bound.register(token)
                continue
            name, brush = match
            ground_ids: tuple[int, ...] = ()
            item_ids: tuple[int, ...] = ()
            composites: tuple[tuple[tuple[int, int, int, int], ...], ...] = ()
            if token.brush_type == "ground":
                ground_ids = _certified_item_ids(engine, getattr(brush, "items", ()))
            elif token.brush_type == "doodad":
                item_ids = _certified_item_ids(engine, getattr(brush, "items", ()))
                composites = tuple(
                    tuple(
                        (dx, dy, dz, item_id)
                        for (dx, dy, dz), stack in sorted(composite.items())
                        for item_id in _certified_item_ids(engine, stack)
                    )
                    for composite in getattr(brush, "composites", ())
                )
                composites = tuple(composite for composite in composites if composite)
            elif token.brush_type == "wall":
                item_ids = _variant_item_ids(getattr(brush, "variants", {}))
                composites = ()
            else:
                item_ids = _variant_item_ids(getattr(brush, "variants", {}))
                composites = ()
            bound.register(
                replace(
                    token,
                    brush_name=name,
                    ground_ids=ground_ids,
                    item_ids=item_ids,
                    composites=composites,
                )
            )
        return bound

    def apply_planner_material_intents(self, plan: Any) -> "SemanticColorPalette":
        """Bind semantic slots to AI-selected, server-certified brush names."""
        reference_style = getattr(plan, "reference_style", {})
        catalog = reference_style.get("certified_material_catalog", {})
        materials = catalog.get("materials", {}) if isinstance(catalog, dict) else {}
        semantic_ai = reference_style.get("semantic_ai", {})
        intents = semantic_ai.get("material_intents", ()) if isinstance(semantic_ai, dict) else ()
        if catalog.get("status") != "CERTIFIED" or not isinstance(materials, dict):
            return self

        candidates: dict[str, tuple[float, str]] = {}
        ground_slots = {
            "city": "swamp", "coast": "sea", "hunt": "sand", "mountain": "mountain",
            "road": "city_road", "interior": "interior",
        }
        wall_slots = {"city": "wall", "hunt": "roshamuul_wall", "interior": "wall"}
        for intent in intents:
            if not isinstance(intent, dict):
                continue
            role = str(intent.get("zone_role", "")).casefold()
            density = max(0.0, min(1.0, float(intent.get("density", 0.5))))
            ground_key = str(intent.get("ground_key", ""))
            wall_key = str(intent.get("wall_key", ""))
            if role in ground_slots and _certified_name(materials, ground_key, "ground"):
                _prefer(candidates, ground_slots[role], density, ground_key)
            if role in wall_slots and _certified_name(materials, wall_key, "wall"):
                _prefer(candidates, wall_slots[role], density, wall_key)
            doodads = [str(key) for key in intent.get("doodad_keys", ())]
            doodad_key = next((key for key in doodads if _certified_name(materials, key, "doodad")), "")
            if doodad_key and role == "nature":
                _prefer(candidates, "nature", density, doodad_key)

        rebound = SemanticColorPalette()
        for token in self.tokens.values():
            selected = candidates.get(token.token_id)
            if selected is None:
                rebound.register(token)
                continue
            key = selected[1]
            material = materials[key]
            rebound.register(replace(
                token,
                brush_name=str(material["name"]),
                brush_type=str(material["type"]),
                material_keywords=(str(material["name"]),),
            ))
        return rebound

    def audit(self) -> dict[str, Any]:
        return {
            "layer_aware_mapcolors": True,
            "token_count": len(self.tokens),
            "resolved_tokens": sum(token.resolved for token in self.tokens.values()),
            "unresolved_tokens": sorted(
                token.token_id for token in self.tokens.values() if not token.resolved
            ),
        }

    def to_manifest(self) -> dict[str, Any]:
        return {
            "format": "rme-semantic-color-palette-v1",
            "tokens": [
                {
                    "token_id": token.token_id,
                    "layer": token.layer.name,
                    "mapcolor": token.mapcolor,
                    "rgb": list(token.rgb),
                    "role": token.role,
                    "brush_name": token.brush_name,
                    "brush_type": token.brush_type,
                    "ground_ids": list(token.ground_ids),
                    "item_ids": list(token.item_ids),
                    "composites": [list(composite) for composite in token.composites],
                }
                for token in sorted(self.tokens.values(), key=lambda value: (value.layer, value.token_id))
            ],
        }

    @classmethod
    def official_defaults(cls) -> "SemanticColorPalette":
        role = ROLE_MAPCOLORS
        return cls(
            [
                SemanticColorToken("sea", BlueprintLayer.SEA_FOUNDATION, role["WATER"], "water", "sea", "ground", material_keywords=("sea", "shallow water")),
                SemanticColorToken("grass", BlueprintLayer.TERRAIN, role["GROUND"], "ground", "grass", "ground", material_keywords=("grass",)),
                SemanticColorToken("swamp", BlueprintLayer.TERRAIN, 132, "ground", "venore muddy floor", "ground", material_keywords=("venore muddy", "muddy", "swamp", "bog")),
                SemanticColorToken("sand", BlueprintLayer.TERRAIN, 210, "ground", "krailos dirt", "ground", material_keywords=("krailos dirt", "dirt", "sand")),
                SemanticColorToken("krailos_dirt", BlueprintLayer.TERRAIN, 207, "ground", "krailos dirt", "ground", material_keywords=("krailos dirt",)),
                SemanticColorToken("krailos_grass", BlueprintLayer.TERRAIN, 121, "ground", "grass (krailos)", "ground", material_keywords=("grass (krailos)",)),
                SemanticColorToken("rock_soil", BlueprintLayer.TERRAIN, 24, "ground", "rock soil", "ground", material_keywords=("rock soil",)),
                SemanticColorToken("krailos_orange", BlueprintLayer.TERRAIN, 192, "ground", "krailos orange", "ground", material_keywords=("krailos orange",)),
                SemanticColorToken("krailos_yellow", BlueprintLayer.TERRAIN, 193, "ground", "krailos yellow", "ground", material_keywords=("krailos yellow",)),
                SemanticColorToken("krailos_purple", BlueprintLayer.TERRAIN, 194, "ground", "krailos purple", "ground", material_keywords=("krailos purple",)),
                SemanticColorToken("mountain", BlueprintLayer.TERRAIN, role["MOUNTAIN"], "mountain", "cave", "ground", material_keywords=("cave", "mountain", "rock")),
                SemanticColorToken("terrain_border", BlueprintLayer.TERRAIN_BORDER, role["BORDER"], "border", brush_type="ground", requires_ground=True),
                SemanticColorToken("road", BlueprintLayer.ROAD, role["ROAD"], "road", "krailos dirt", "ground", material_keywords=("road", "street", "dirt")),
                SemanticColorToken("city_road", BlueprintLayer.ROAD, 86, "road", "grassy cobblestone", "ground", material_keywords=("grassy cobblestone",)),
                SemanticColorToken("transition_road", BlueprintLayer.ROAD, 87, "road", "krailos dirt", "ground", material_keywords=("krailos dirt",)),
                SemanticColorToken("dry_path", BlueprintLayer.ROAD, 88, "road", "grass (krailos)", "ground", material_keywords=("grass (krailos)", "krailos")),
                SemanticColorToken("dark_path", BlueprintLayer.ROAD, 89, "road", "cave", "ground", material_keywords=("cave",)),
                SemanticColorToken("rock_path", BlueprintLayer.ROAD, 24, "road", "rock soil", "ground", material_keywords=("rock soil",)),
                SemanticColorToken("interior", BlueprintLayer.STRUCTURE_GROUND, role["INTERIOR"], "interior", "timber floor", "ground", material_keywords=("wooden floor", "timber floor", "stone floor")),
                SemanticColorToken("civic_floor", BlueprintLayer.STRUCTURE_GROUND, 208, "interior", "ornamented stone floor 1", "ground", material_keywords=("ornamented stone floor", "stone floor")),
                SemanticColorToken("krailos_floor", BlueprintLayer.STRUCTURE_GROUND, 207, "interior", "stone floor", "ground", material_keywords=("stone floor",)),
                SemanticColorToken("krailos_temple_floor", BlueprintLayer.STRUCTURE_GROUND, 121, "interior", "grass (krailos)", "ground", material_keywords=("grass (krailos)",)),
                SemanticColorToken("dark_floor", BlueprintLayer.STRUCTURE_GROUND, 131, "interior", "dark scaled ground", "ground", material_keywords=("dark scaled ground", "dark")),
                SemanticColorToken("wall", BlueprintLayer.WALL, role["WALL"], "wall", "venore wall", "wall", material_keywords=("venore", "wood", "stone", "brick"), requires_ground=True),
                SemanticColorToken("ruin_wall", BlueprintLayer.WALL, 122, "wall", "ruin wall", "wall", material_keywords=("ruin wall", "ruin"), requires_ground=True),
                SemanticColorToken("krailos_temple_wall", BlueprintLayer.WALL, 120, "wall", "rock wall", "wall", material_keywords=("rock wall",), requires_ground=True),
                SemanticColorToken("krailos_spikes_1", BlueprintLayer.WALL, 124, "wall", "krailos spikes1", "wall", material_keywords=("krailos spikes1",), requires_ground=True),
                SemanticColorToken("krailos_spikes_2", BlueprintLayer.WALL, 125, "wall", "krailos spikes2", "wall", material_keywords=("krailos spikes2",), requires_ground=True),
                SemanticColorToken("roshamuul_wall", BlueprintLayer.WALL, 123, "wall", "roshamuul wall", "wall", material_keywords=("roshamuul wall", "roshamuul"), requires_ground=True),
                SemanticColorToken("door", BlueprintLayer.DOOR_WINDOW, role["DOOR"], "door", "venore wall", "wall", material_keywords=("venore", "wood", "stone"), requires_ground=True),
                SemanticColorToken("brown_bamboo_roof", BlueprintLayer.ROOF, 114, "roof", "brown bamboo roof", "ground", material_keywords=("brown bamboo roof", "roof")),
                SemanticColorToken("stairs", BlueprintLayer.STAIRS_RAMP, 129, "stairs", brush_type="doodad", material_keywords=("stairs", "stair"), requires_ground=True),
                SemanticColorToken("gray_stone_stairs", BlueprintLayer.STAIRS_RAMP, 127, "stairs", "gray stone stairs", "doodad", material_keywords=("gray stone stairs",), requires_ground=True),
                SemanticColorToken("swamp_clay_ramp", BlueprintLayer.STAIRS_RAMP, 128, "ramp", "swamp clay ramp", "doodad", material_keywords=("swamp clay ramp",), requires_ground=True),
                SemanticColorToken("ramp", BlueprintLayer.STAIRS_RAMP, 130, "ramp", "ramp", "doodad", material_keywords=("ramp",), requires_ground=True),
                SemanticColorToken("nature", BlueprintLayer.NATURE, role["NATURE"], "nature", brush_type="doodad", material_keywords=("tree", "bush", "plant"), requires_ground=True),
                SemanticColorToken("swamp_tree", BlueprintLayer.NATURE, 124, "nature", "mangrove tree", "doodad", material_keywords=("mangrove tree", "swamp gnarl"), requires_ground=True),
                SemanticColorToken("swamp_plant", BlueprintLayer.NATURE, 125, "nature", "swamp plants", "doodad", material_keywords=("swamp plants", "swamp claw"), requires_ground=True),
                SemanticColorToken("forest_shrub", BlueprintLayer.NATURE, 126, "nature", "jungle fern", "doodad", material_keywords=("jungle fern", "jungle plants", "bush"), requires_ground=True),
                SemanticColorToken("dry_rock_detail", BlueprintLayer.NATURE, 127, "nature", "krailos rocks", "doodad", material_keywords=("krailos rocks", "sandy rock"), requires_ground=True),
                SemanticColorToken("krailos_plant", BlueprintLayer.NATURE, 119, "nature", "jungle fern", "doodad", material_keywords=("jungle fern", "fern"), requires_ground=True),
                SemanticColorToken("krailos_rocks", BlueprintLayer.NATURE, 120, "nature", "krailos rocks", "doodad", material_keywords=("krailos rocks",), requires_ground=True),
                SemanticColorToken("krailos_mountains", BlueprintLayer.NATURE, 118, "nature", "krailos mountains", "doodad", material_keywords=("krailos mountains",), requires_ground=True),
                SemanticColorToken("dark_fungi", BlueprintLayer.NATURE, 128, "nature", "dark mushrooms", "doodad", material_keywords=("dark mushrooms", "void mushrooms"), requires_ground=True),
                SemanticColorToken("decoration", BlueprintLayer.DECORATION, role["DECORATION"], "decoration", brush_type="doodad", material_keywords=("debris", "detail", "decoration"), requires_ground=True),
                SemanticColorToken("krailos_banner", BlueprintLayer.DECORATION, 121, "decoration", "krailos banner", "doodad", material_keywords=("krailos banner",), requires_ground=True),
                SemanticColorToken("krailos_totem", BlueprintLayer.DECORATION, 122, "decoration", "krailos totem pole", "doodad", material_keywords=("krailos totem pole",), requires_ground=True),
                SemanticColorToken("krailos_pot", BlueprintLayer.DECORATION, 123, "decoration", "krailos pot", "doodad", material_keywords=("krailos pot",), requires_ground=True),
                SemanticColorToken("krailos_fence", BlueprintLayer.DECORATION, 116, "decoration", "krailos fence", "doodad", material_keywords=("krailos fence",), requires_ground=True),
                SemanticColorToken("krailos_tanned_skin", BlueprintLayer.DECORATION, 117, "decoration", "krailos tanned skin", "doodad", material_keywords=("krailos tanned skin",), requires_ground=True),
                SemanticColorToken("krailos_thing", BlueprintLayer.DECORATION, 118, "decoration", "krailos thing", "doodad", material_keywords=("krailos thing",), requires_ground=True),
                SemanticColorToken("krailos_totem_skull", BlueprintLayer.DECORATION, 119, "decoration", "krailos totem pole - skull", "doodad", material_keywords=("krailos totem pole - skull",), requires_ground=True),
                SemanticColorToken("krailos_hut", BlueprintLayer.DECORATION, 113, "decoration", "krailos hut", "doodad", material_keywords=("krailos hut",), requires_ground=True),
                SemanticColorToken("krailos_roof", BlueprintLayer.DECORATION, 114, "decoration", "krailos roof", "doodad", material_keywords=("krailos roof",), requires_ground=True),
                SemanticColorToken("krailos_roof_end", BlueprintLayer.DECORATION, 115, "decoration", "krailos roof - end", "doodad", material_keywords=("krailos roof - end",), requires_ground=True),
                SemanticColorToken("krailos_structure_1", BlueprintLayer.DECORATION, 110, "decoration", "krailos structure1", "doodad", material_keywords=("krailos structure1",), requires_ground=True),
                SemanticColorToken("krailos_structure_2", BlueprintLayer.DECORATION, 111, "decoration", "krailos structure2", "doodad", material_keywords=("krailos structure2",), requires_ground=True),
                SemanticColorToken("krailos_structure_3", BlueprintLayer.DECORATION, 112, "decoration", "krailos structure3", "doodad", material_keywords=("krailos structure3",), requires_ground=True),
                SemanticColorToken("krailos_structure_4", BlueprintLayer.DECORATION, 113, "decoration", "krailos structure4", "doodad", material_keywords=("krailos structure4",), requires_ground=True),
                SemanticColorToken("krailos_blood", BlueprintLayer.DECORATION, 126, "decoration", "krailos blood", "doodad", material_keywords=("krailos blood",), requires_ground=True),
                SemanticColorToken("spawn", BlueprintLayer.GAMEPLAY, role["SPAWN_OBJECT"], "spawn"),
            ]
        )


def _variant_item_ids(variants: Any) -> tuple[int, ...]:
    """Expose only certified numeric IDs outside the weighted brush resolver."""
    result: list[int] = []
    for values in getattr(variants, "values", lambda: ())():
        for value in values:
            item_id = getattr(value, "item_id", value)
            try:
                normalized = int(item_id)
            except (TypeError, ValueError):
                continue
            if normalized > 0:
                result.append(normalized)
    return tuple(result)


def _certified_item_ids(engine: Any, values: Any) -> tuple[int, ...]:
    """Flatten an official brush stack without losing its source order.

    RME doodad composites store a tuple of item IDs at every relative tile.
    Treating that tuple as one ID produces values such as ``(1951,)`` at the
    materializer boundary.  Normalize here, where the brush data still has
    enough context to preserve a complete multi-item stack.
    """
    result: list[int] = []

    def visit(value: Any) -> None:
        if isinstance(value, (tuple, list)):
            for member in value:
                visit(member)
            return
        item_id = getattr(value, "item_id", value)
        try:
            normalized = int(item_id)
        except (TypeError, ValueError):
            return
        if normalized > 0 and engine.is_sprite_backed(normalized):
            result.append(normalized)

    visit(values)
    return tuple(result)


def _find_brush(collection: dict[str, Any], exact: str, keywords: tuple[str, ...]) -> tuple[str, Any] | None:
    if exact and exact.lower() in collection:
        return exact.lower(), collection[exact.lower()]
    for keyword in keywords:
        for name in sorted(collection):
            if keyword.lower() in name.lower():
                return name, collection[name]
    return None


def _certified_name(materials: dict[str, Any], key: str, expected_type: str) -> str:
    material = materials.get(key)
    if not isinstance(material, dict) or str(material.get("type", "")) != expected_type:
        return ""
    return str(material.get("name", ""))


def _prefer(candidates: dict[str, tuple[float, str]], slot: str, density: float, key: str) -> None:
    current = candidates.get(slot)
    if current is None or density > current[0]:
        candidates[slot] = (density, key)
