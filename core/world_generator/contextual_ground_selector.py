from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GroundContext:
    role: str
    terrain: str
    route_name: str = ""
    biome_style: str = ""


class ContextualGroundBrushSelector:
    """Select semantic GroundBrush tokens from planner context, never raw IDs."""

    def route_token(self, context: GroundContext) -> str:
        name = context.route_name.lower()
        style = context.biome_style.lower()
        terrain = context.terrain.lower()
        if "rock soil" in terrain or "mountain" in terrain:
            return "rock_path"
        if "krailos" in name or "krailos" in style:
            return "dry_path"
        if context.role == "city_route":
            return "city_road"
        if "roshamuul" in name or "dark" in style:
            return "dark_path"
        if context.role == "hunt_route" or "dry" in style:
            return "dry_path"
        return "transition_road"
