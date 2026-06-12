"""
HITO 15 - AI Architect: World Planner
=====================================

Top-level orchestrator. Takes a free-form prompt and produces a complete
WorldPlan that can be consumed by the existing WorldGenerator,
BlueprintRegistry, and AssetRegistry.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .theme_resolver import ThemeResolver
from .zone_planner import (
    ZonePlanner,
    CityPlan,
    DungeonPlan,
    HuntPlan,
    BossPlan,
    QuestPlan,
)
from .difficulty_planner import DifficultyPlanner, ZoneDifficulty
from .layout_planner import LayoutPlanner, WorldLayout

# =============================================================================
# PromptParser
# =============================================================================


class PromptParser:
    """Parses a free-form prompt into a structured dict."""

    THEME_KEYWORDS: Dict[str, List[str]] = {
        "issavi": ["issavi"],
        "roshamuul": ["roshamuul"],
        "soul_war": ["soul war", "soulwar"],
        "library": ["library"],
        "yalahar": ["yalahar"],
        "falcon": ["falcon", "bastia"],
        "cobra": ["cobra"],
        "ice": ["ice", "hielo"],
        "jungle": ["jungle", "jungla"],
        "thais": ["thais"],
        "venore": ["venore"],
        "ankrahmun": ["ankrahmun"],
    }

    def parse(self, prompt: str) -> Dict[str, Any]:
        lower = (prompt or "").lower()
        result: Dict[str, Any] = {
            "themes": self._extract_themes(lower),
            "level_min": None,
            "level_max": None,
            "city_count": 0,
            "dungeon_count": 0,
            "hunt_count": 0,
            "boss_count": 0,
            "quest_count": 0,
            "zone_kinds": [],
        }

        # Level range: "level 300-500" or "nivel 300-500" or "level 300"
        m = re.search(r"(?:level|nivel)\s*(\d+)\s*[-–]\s*(\d+)", lower)
        if m:
            result["level_min"] = int(m.group(1))
            result["level_max"] = int(m.group(2))
        else:
            m = re.search(r"(?:level|nivel)\s*(\d+)", lower)
            if m:
                lv = int(m.group(1))
                result["level_min"] = max(1, lv - 20)
                result["level_max"] = lv + 20

        # Counts (with explicit numbers like "3 hunts", "2 bosses")
        for kind in ("hunt", "boss", "dungeon", "city", "quest"):
            result[f"{kind}_count"] = self._extract_count(lower, kind)

        # Keyword-based detection (also for cases without explicit count)
        if "ciudad" in lower or "city" in lower:
            if result["city_count"] == 0:
                result["city_count"] = 1
        if "dungeon" in lower or "mazmorra" in lower or "calabozo" in lower:
            if result["dungeon_count"] == 0:
                result["dungeon_count"] = 1
        if "boss" in lower or "jefe" in lower or "final boss" in lower:
            if result["boss_count"] == 0:
                result["boss_count"] = 1
        if "quest" in lower or "mision" in lower or "misión" in lower:
            if result["quest_count"] == 0:
                result["quest_count"] = 1

        # Final fallback: if still nothing at all, default to a single hunt
        total = sum(
            result[f"{k}_count"] for k in ("hunt", "boss", "dungeon", "city", "quest")
        )
        if total == 0:
            result["hunt_count"] = 1

        # Build zone_kinds in canonical order: city -> dungeon -> hunt -> quest -> boss
        kinds: List[str] = []
        kinds.extend(["city"] * result["city_count"])
        kinds.extend(["dungeon"] * result["dungeon_count"])
        kinds.extend(["hunt"] * result["hunt_count"])
        kinds.extend(["quest"] * result["quest_count"])
        kinds.extend(["boss"] * result["boss_count"])
        result["zone_kinds"] = kinds

        return result

    def _extract_themes(self, lower: str) -> List[str]:
        themes: List[str] = []
        for canonical, keywords in self.THEME_KEYWORDS.items():
            for kw in keywords:
                if kw in lower and canonical not in themes:
                    themes.append(canonical)
        return themes

    def _extract_count(self, text: str, kind: str) -> int:
        m = re.search(rf"(\d+)\s*{kind}", text)
        if m:
            return int(m.group(1))
        m = re.search(rf"(\d+)\s*{kind}s", text)
        if m:
            return int(m.group(1))
        return 0


# =============================================================================
# WorldRequest
# =============================================================================


@dataclass
class WorldRequest:
    prompt: str
    themes: List[str] = field(default_factory=list)
    level_min: int = 1
    level_max: int = 200
    zone_kinds: List[str] = field(default_factory=list)

    @property
    def has_city(self) -> bool:
        return "city" in self.zone_kinds

    @property
    def has_dungeon(self) -> bool:
        return "dungeon" in self.zone_kinds

    @property
    def has_boss(self) -> bool:
        return "boss" in self.zone_kinds

    @property
    def has_quest(self) -> bool:
        return "quest" in self.zone_kinds

    @property
    def hunt_count(self) -> int:
        return self.zone_kinds.count("hunt")

    @property
    def boss_count(self) -> int:
        return self.zone_kinds.count("boss")

    @property
    def city_count(self) -> int:
        return self.zone_kinds.count("city")

    @property
    def dungeon_count(self) -> int:
        return self.zone_kinds.count("dungeon")

    @property
    def quest_count(self) -> int:
        return self.zone_kinds.count("quest")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "themes": self.themes,
            "level_range": [self.level_min, self.level_max],
            "zone_kinds": self.zone_kinds,
        }


# =============================================================================
# WorldPlan - final output
# =============================================================================


@dataclass
class WorldPlan:
    prompt: str
    themes: List[str] = field(default_factory=list)
    primary_theme: str = "issavi"
    level_min: int = 1
    level_max: int = 200
    request: Optional[WorldRequest] = None
    cities: List[CityPlan] = field(default_factory=list)
    dungeons: List[DungeonPlan] = field(default_factory=list)
    hunting_zones: List[HuntPlan] = field(default_factory=list)
    boss_zones: List[BossPlan] = field(default_factory=list)
    quest_zones: List[QuestPlan] = field(default_factory=list)
    roads: List[Dict[str, Any]] = field(default_factory=list)
    teleports: List[Dict[str, Any]] = field(default_factory=list)
    ports: List[Dict[str, Any]] = field(default_factory=list)
    waypoints: List[Dict[str, Any]] = field(default_factory=list)
    difficulty_progression: List[ZoneDifficulty] = field(default_factory=list)
    layout: Optional[WorldLayout] = None
    world_width: int = 200
    world_height: int = 200
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "themes": self.themes,
            "primary_theme": self.primary_theme,
            "level_range": [self.level_min, self.level_max],
            "request": self.request.to_dict() if self.request else None,
            "cities": [c.to_dict() for c in self.cities],
            "dungeons": [d.to_dict() for d in self.dungeons],
            "hunting_zones": [h.to_dict() for h in self.hunting_zones],
            "boss_zones": [b.to_dict() for b in self.boss_zones],
            "quest_zones": [q.to_dict() for q in self.quest_zones],
            "roads": self.roads,
            "teleports": self.teleports,
            "ports": self.ports,
            "waypoints": self.waypoints,
            "difficulty_progression": [
                d.to_dict() for d in self.difficulty_progression
            ],
            "layout": self.layout.to_dict() if self.layout else None,
            "world_width": self.world_width,
            "world_height": self.world_height,
            "metadata": self.metadata,
        }

    def summary(self) -> str:
        parts = [f"primary={self.primary_theme}"]
        if self.cities:
            parts.append(f"cities={len(self.cities)}")
        if self.dungeons:
            parts.append(f"dungeons={len(self.dungeons)}")
        if self.hunting_zones:
            parts.append(f"hunts={len(self.hunting_zones)}")
        if self.boss_zones:
            parts.append(f"bosses={len(self.boss_zones)}")
        if self.quest_zones:
            parts.append(f"quests={len(self.quest_zones)}")
        return "WorldPlan(" + ", ".join(parts) + ")"


# =============================================================================
# WorldPlanner
# =============================================================================


class WorldPlanner:
    """The full AI Architect pipeline."""

    def __init__(
        self,
        theme_resolver: Optional[ThemeResolver] = None,
        zone_planner: Optional[ZonePlanner] = None,
        difficulty_planner: Optional[DifficultyPlanner] = None,
        layout_planner: Optional[LayoutPlanner] = None,
        blueprint_registry: Optional[Any] = None,
        asset_registry: Optional[Any] = None,
        world_generator: Optional[Any] = None,
        seed: Optional[int] = None,
    ) -> None:
        self.theme_resolver = theme_resolver or ThemeResolver(
            asset_registry=asset_registry,
            blueprint_registry=blueprint_registry,
        )
        self.zone_planner = zone_planner or ZonePlanner(seed=seed)
        self.difficulty_planner = difficulty_planner or DifficultyPlanner()
        self.layout_planner = layout_planner or LayoutPlanner(
            blueprint_registry=blueprint_registry,
            zone_planner=self.zone_planner,
            seed=seed,
        )
        self.prompt_parser = PromptParser()
        self.blueprint_registry = blueprint_registry
        self.asset_registry = asset_registry
        self.world_generator = world_generator
        self._seed = seed

    def plan(
        self,
        prompt: str,
        world_width: int = 200,
        world_height: int = 200,
    ) -> WorldPlan:
        """Convert a free-form prompt into a complete WorldPlan."""
        # 1. Parse
        parsed = self.prompt_parser.parse(prompt)
        request = WorldRequest(
            prompt=prompt,
            themes=parsed["themes"] or ["issavi"],
            level_min=parsed.get("level_min") or 1,
            level_max=parsed.get("level_max") or 200,
            zone_kinds=parsed["zone_kinds"],
        )

        # 2. Resolve themes
        themes_assets = self.theme_resolver.resolve_all(request.themes)
        if not themes_assets:
            themes_assets = [self.theme_resolver.resolve("generic")]
        primary_theme = themes_assets[0]

        # 3. Difficulty progression
        style = self.difficulty_planner.recommend_style(request.zone_kinds)
        difficulty = self.difficulty_planner.plan_progression(
            request.zone_kinds,
            request.level_min,
            request.level_max,
            primary_theme.monsters,
            style=style,
        )

        # 4. Plan each zone
        cities: List[CityPlan] = []
        dungeons: List[DungeonPlan] = []
        hunts: List[HuntPlan] = []
        bosses: List[BossPlan] = []
        quests: List[QuestPlan] = []
        all_zones: List[Any] = []

        zone_difficulties = {d.zone_index: d for d in difficulty}
        for idx, kind in enumerate(request.zone_kinds):
            diff = zone_difficulties.get(idx)
            lo = diff.level_min if diff else request.level_min
            hi = diff.level_max if diff else request.level_max
            theme = themes_assets[idx % len(themes_assets)]

            if kind == "city":
                c = self.zone_planner.plan_city(
                    name=f"{theme.name.capitalize()} Capital",
                    theme=theme,
                    min_level=lo,
                    max_level=hi,
                )
                cities.append(c)
                all_zones.append(c)
            elif kind == "dungeon":
                d = self.zone_planner.plan_dungeon(
                    name=f"{theme.name.capitalize()} Depths",
                    theme=theme,
                    min_level=lo,
                    max_level=hi,
                )
                dungeons.append(d)
                all_zones.append(d)
            elif kind == "hunt":
                h = self.zone_planner.plan_hunt(
                    name=f"{theme.name.capitalize()} Hunt {len(hunts) + 1}",
                    theme=theme,
                    min_level=lo,
                    max_level=hi,
                    density=diff.spawn_density if diff else "medium",
                )
                hunts.append(h)
                all_zones.append(h)
            elif kind == "boss":
                b = self.zone_planner.plan_boss(
                    name=f"{theme.name.capitalize()} Final Boss",
                    theme=theme,
                    min_level=lo,
                    max_level=hi,
                )
                bosses.append(b)
                all_zones.append(b)
            elif kind == "quest":
                q = self.zone_planner.plan_quest(
                    title=f"{theme.name.capitalize()} Trial {len(quests) + 1}",
                    theme=theme,
                    min_level=lo,
                    max_level=hi,
                )
                quests.append(q)
                all_zones.append(q)

        # 5. Layout
        layout = (
            self.layout_planner.arrange(
                all_zones,
                world_width=world_width,
                world_height=world_height,
            )
            if all_zones
            else None
        )

        # 6. Build meta WorldPlan
        wp = WorldPlan(
            prompt=prompt,
            themes=request.themes,
            primary_theme=primary_theme.name,
            level_min=request.level_min,
            level_max=request.level_max,
            request=request,
            cities=cities,
            dungeons=dungeons,
            hunting_zones=hunts,
            boss_zones=bosses,
            quest_zones=quests,
            roads=layout.roads if layout else [],
            teleports=layout.teleports if layout else [],
            ports=[],
            waypoints=layout.waypoints if layout else [],
            difficulty_progression=difficulty,
            layout=layout,
            world_width=world_width,
            world_height=world_height,
            metadata={
                "strategy": layout.strategy if layout else "none",
                "difficulty_style": style,
                "total_zones": len(all_zones),
                "integrations": {
                    "blueprint_registry": self.blueprint_registry is not None,
                    "asset_registry": self.asset_registry is not None,
                    "world_generator": self.world_generator is not None,
                },
            },
        )

        # 7. (Optional) execute via WorldGenerator
        if self.world_generator is not None:
            try:
                world_model = self.world_generator.generate(wp.to_dict())
                wp.metadata["world_model_tile_count"] = (
                    world_model.tile_count()
                    if hasattr(world_model, "tile_count")
                    else None
                )
            except Exception as exc:
                wp.metadata["world_generator_error"] = str(exc)

        return wp

    # Backward-compat alias
    def __call__(
        self,
        prompt: str,
        world_width: int = 200,
        world_height: int = 200,
    ) -> WorldPlan:
        return self.plan(prompt, world_width, world_height)
