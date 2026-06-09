from __future__ import annotations

# HITO 14 (original architect system)
from .architect import ArchitectAI
from .design_rules import DesignRules
from .style_engine import StyleEngine, StyleDNA
from .layout_engine import LayoutEngine
from .composition_engine import CompositionEngine
from .mapper_ai import MapperAI

# HITO 15 (AI Architect)
from .theme_resolver import (
    ThemeResolver, ThemeAssets,
    resolve_theme, resolve_themes, merge_themes,
    get_default_resolver,
)
from .zone_planner import (
    ZonePlanner, CityPlan, DungeonPlan, HuntPlan, BossPlan, QuestPlan,
    DIFFICULTY_BANDS,
    get_default_planner,
)
from .difficulty_planner import (
    DifficultyPlanner, ZoneDifficulty, DENSITY_CURVE,
)
from .layout_planner import (
    LayoutPlanner, WorldLayout, PlacedZone,
    DEFAULT_SIZES,
)
from .world_planner import (
    WorldPlanner, WorldPlan, WorldRequest, PromptParser,
)
from .ai_architect import AIArchitect, plan as ai_plan


__all__ = [
    # HITO 14
    "ArchitectAI",
    "DesignRules",
    "StyleEngine",
    "StyleDNA",
    "LayoutEngine",
    "CompositionEngine",
    "MapperAI",
    # HITO 15 - Theme
    "ThemeResolver",
    "ThemeAssets",
    "resolve_theme",
    "resolve_themes",
    "merge_themes",
    "get_default_resolver",
    # HITO 15 - Zone
    "ZonePlanner",
    "CityPlan",
    "DungeonPlan",
    "HuntPlan",
    "BossPlan",
    "QuestPlan",
    "DIFFICULTY_BANDS",
    "get_default_planner",
    # HITO 15 - Difficulty
    "DifficultyPlanner",
    "ZoneDifficulty",
    "DENSITY_CURVE",
    # HITO 15 - Layout
    "LayoutPlanner",
    "WorldLayout",
    "PlacedZone",
    "DEFAULT_SIZES",
    # HITO 15 - World
    "WorldPlanner",
    "WorldPlan",
    "WorldRequest",
    "PromptParser",
    # HITO 15 - Main API
    "AIArchitect",
    "ai_plan",
]
