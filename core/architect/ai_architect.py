"""
HITO 15 - AI Architect
======================

The main public API of the AI Architect system.

This is the "front door" of HITO 15: it hides the internal orchestrator
(WorldPlanner), exposes a single, memorable entry point
(`AIArchitect().plan(prompt)`) and provides convenience helpers
(`analyze`, `explain`, `summary`).

Architecture:
    Prompt
      ↓
    AIArchitect.plan(prompt)
      ↓
    WorldPlan (compatible with core.planner.WorldPlan)
      ↓
    WorldGenerator / BlueprintRegistry / AssetRegistry

Usage:

    from core.architect import AIArchitect

    architect = AIArchitect()
    plan = architect.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300 y un boss")
    print(plan.summary())
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .theme_resolver import (
    ThemeResolver,
    ThemeAssets,
)
from .zone_planner import (
    ZonePlanner,
)
from .difficulty_planner import DifficultyPlanner
from .layout_planner import LayoutPlanner
from .world_planner import WorldPlanner, WorldPlan, WorldRequest, PromptParser

# =============================================================================
# AIArchitect - the public entry point
# =============================================================================


class AIArchitect:
    """
    The public face of the AI Architect system.

    Example:
        >>> architect = AIArchitect()
        >>> plan = architect.plan("Genera una ciudad estilo Issavi con 3 hunts nivel 300 y un boss final")
        >>> print(plan.summary())
        WorldPlan(primary=issavi, cities=1, hunts=3, bosses=1)
    """

    def __init__(
        self,
        theme_resolver: Optional[ThemeResolver] = None,
        zone_planner: Optional[ZonePlanner] = None,
        difficulty_planner: Optional[DifficultyPlanner] = None,
        layout_planner: Optional[LayoutPlanner] = None,
        world_planner: Optional[WorldPlanner] = None,
        blueprint_registry: Optional[Any] = None,
        asset_registry: Optional[Any] = None,
        world_generator: Optional[Any] = None,
        seed: Optional[int] = None,
    ) -> None:
        if world_planner is not None:
            self.world_planner = world_planner
        else:
            self.world_planner = WorldPlanner(
                theme_resolver=theme_resolver,
                zone_planner=zone_planner,
                difficulty_planner=difficulty_planner,
                layout_planner=layout_planner,
                blueprint_registry=blueprint_registry,
                asset_registry=asset_registry,
                world_generator=world_generator,
                seed=seed,
            )
        self.theme_resolver = self.world_planner.theme_resolver
        self.zone_planner = self.world_planner.zone_planner
        self.difficulty_planner = self.world_planner.difficulty_planner
        self.layout_planner = self.world_planner.layout_planner
        self.blueprint_registry = blueprint_registry
        self.asset_registry = asset_registry
        self.world_generator = world_generator
        self._seed = seed

    # ------------------------------------------------------------------
    # Primary API
    # ------------------------------------------------------------------

    def plan(
        self,
        prompt: str,
        world_width: int = 200,
        world_height: int = 200,
    ) -> WorldPlan:
        """
        Convert a free-form prompt into a complete WorldPlan.

        Args:
            prompt: Free-form text describing the desired world.
                    Supports English and Spanish, e.g.:
                      "Generate a city issavi style with 3 hunts level 300 and a boss"
                      "Genera una ciudad estilo Issavi con 3 hunts nivel 300 y un boss final"
                      "Issavi + Roshamuul level 300"
            world_width: Target world width in tiles.
            world_height: Target world height in tiles.

        Returns:
            WorldPlan with all city, dungeon, hunt, boss, and quest plans.
        """
        return self.world_planner.plan(
            prompt,
            world_width=world_width,
            world_height=world_height,
        )

    # Backward-compat alias
    def __call__(
        self,
        prompt: str,
        world_width: int = 200,
        world_height: int = 200,
    ) -> WorldPlan:
        return self.plan(prompt, world_width, world_height)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def analyze(self, prompt: str) -> WorldRequest:
        """Parse a prompt into a structured WorldRequest without planning."""
        return (
            self.world_planner.prompt_parser.parse.__class__()
            if False
            else _request_from_prompt(self.world_planner.prompt_parser, prompt)
        )

    def explain(self, plan: WorldPlan) -> str:
        """
        Generate a human-readable explanation of a plan.

        Returns a multi-line string describing the design decisions.
        """
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append(f"  AI ARCHITECT - {plan.primary_theme.upper()}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"Prompt:  {plan.prompt}")
        lines.append(f"Themes:  {', '.join(plan.themes)}")
        lines.append(f"Range:  level {plan.level_min}-{plan.level_max}")
        lines.append("")

        if plan.request:
            r = plan.request
            lines.append("Request:")
            lines.append(f"  Cities:    {r.city_count}")
            lines.append(f"  Dungeons:  {r.dungeon_count}")
            lines.append(f"  Hunts:     {r.hunt_count}")
            lines.append(f"  Quests:    {r.quest_count}")
            lines.append(f"  Bosses:    {r.boss_count}")
            lines.append("")

        if plan.cities:
            lines.append(f"Cities ({len(plan.cities)}):")
            for c in plan.cities:
                lines.append(
                    f"  - {c.name} (pop {c.population}, districts {len(c.districts)}, features {len(c.features)})"
                )
            lines.append("")

        if plan.hunting_zones:
            lines.append(f"Hunting Zones ({len(plan.hunting_zones)}):")
            for h in plan.hunting_zones:
                lines.append(
                    f"  - {h.name} (lvl {h.min_level}-{h.max_level}, "
                    f"pool {len(h.monster_pool)}, spawns {h.spawn_count})"
                )
            lines.append("")

        if plan.boss_zones:
            lines.append(f"Boss Zones ({len(plan.boss_zones)}):")
            for b in plan.boss_zones:
                lines.append(
                    f"  - {b.name} (boss: {b.boss_monster}, loot: {len(b.loot_table)} items)"
                )
            lines.append("")

        if plan.quest_zones:
            lines.append(f"Quest Zones ({len(plan.quest_zones)}):")
            for q in plan.quest_zones:
                lines.append(
                    f"  - {q.title} (objectives: {len(q.objectives)}, rewards: {len(q.rewards)})"
                )
            lines.append("")

        if plan.difficulty_progression:
            lines.append("Difficulty Progression:")
            for d in plan.difficulty_progression:
                notes = f" - {d.notes[0]}" if d.notes else ""
                lines.append(
                    f"  - {d.zone_kind:8s} lvl {d.level_min}-{d.level_max} "
                    f"({d.band:9s}, density={d.spawn_density}){notes}"
                )
            lines.append("")

        if plan.layout:
            lines.append("Layout:")
            lines.append(f"  Strategy:    {plan.layout.strategy}")
            lines.append(
                f"  World size:  {plan.layout.world_width} x {plan.layout.world_height}"
            )
            lines.append(f"  Bounds:      {plan.layout.bounds()}")
            lines.append(f"  Roads:       {len(plan.roads)}")
            lines.append(f"  Teleports:   {len(plan.teleports)}")
            lines.append(f"  Waypoints:   {len(plan.waypoints)}")
            lines.append("")

        lines.append("Metadata:")
        for k, v in plan.metadata.items():
            if k != "integrations":
                lines.append(f"  {k}: {v}")
        lines.append("")
        lines.append("=" * 60)
        return "\n".join(lines)

    def summary(self, plan: WorldPlan) -> str:
        """One-line summary of a plan."""
        return plan.summary()

    def to_dict(self, plan: WorldPlan) -> Dict[str, Any]:
        """Serialize a plan to a dict (for JSON export)."""
        return plan.to_dict()

    # ------------------------------------------------------------------
    # Registry access
    # ------------------------------------------------------------------

    def list_known_themes(self) -> List[str]:
        """Return themes known to the resolver."""
        return self.theme_resolver.list_known_themes()

    def resolve_theme(self, name: str) -> ThemeAssets:
        """Resolve a theme name to its ThemeAssets."""
        return self.theme_resolver.resolve(name)

    # ------------------------------------------------------------------
    # Integration helpers
    # ------------------------------------------------------------------

    def attach_world_generator(self, world_generator: Any) -> "AIArchitect":
        """Attach a WorldGenerator; future plan() calls will execute it."""
        self.world_generator = world_generator
        self.world_planner.world_generator = world_generator
        return self

    def attach_blueprint_registry(self, blueprint_registry: Any) -> "AIArchitect":
        """Attach a BlueprintRegistry for theme-specific blueprints."""
        self.blueprint_registry = blueprint_registry
        self.world_planner.blueprint_registry = blueprint_registry
        # Re-create the layout_planner to use the new registry
        self.world_planner.layout_planner = LayoutPlanner(
            blueprint_registry=blueprint_registry,
            zone_planner=self.zone_planner,
            seed=self._seed,
        )
        self.layout_planner = self.world_planner.layout_planner
        return self

    def attach_asset_registry(self, asset_registry: Any) -> "AIArchitect":
        """Attach an AssetRegistry for asset validation."""
        self.asset_registry = asset_registry
        self.world_planner.asset_registry = asset_registry
        # Re-create the theme_resolver to use the new registry
        self.world_planner.theme_resolver = ThemeResolver(
            asset_registry=asset_registry,
            blueprint_registry=self.blueprint_registry,
        )
        self.theme_resolver = self.world_planner.theme_resolver
        return self


# =============================================================================
# Helpers
# =============================================================================


def _request_from_prompt(parser: PromptParser, prompt: str) -> WorldRequest:
    parsed = parser.parse(prompt)
    return WorldRequest(
        prompt=prompt,
        themes=parsed["themes"] or ["issavi"],
        level_min=parsed.get("level_min") or 1,
        level_max=parsed.get("level_max") or 200,
        zone_kinds=parsed["zone_kinds"],
    )


# =============================================================================
# Module-level convenience
# =============================================================================


def plan(
    prompt: str,
    world_width: int = 200,
    world_height: int = 200,
) -> WorldPlan:
    """
    Shortcut: build a default AIArchitect and call plan().

    Usage:
        from core.architect import plan
        world_plan = plan("Genera una ciudad issavi con 3 hunts nivel 300")
    """
    return AIArchitect().plan(prompt, world_width, world_height)
