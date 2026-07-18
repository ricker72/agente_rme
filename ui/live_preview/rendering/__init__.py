"""
WG-20U-A real appearance rendering bridge.
"""

from .appearance_render_loader import AppearanceRenderLoader
from .appearance_render_model import AppearanceRenderModel, RenderedTile
from .appearance_tile_renderer import AppearanceTileRenderer
from .ingame_render_mode import IngameRenderMode, IngameRenderState, IngameTileVisual
from .ingame_visual_qa import IngameVisualQA, IngameVisualQAResult
from .render_cache import RenderCache
from .rme_draw_order import RMEDrawOrderEngine, RMEStackItem
from .rme_mapcolors import (
    audit_rme_mapcolor_contract,
    dominant_stack_mapcolor,
    resolve_rme_mapcolor,
    rme_minimap_color_to_rgb,
)
from .rme_movement_overlay import (
    audit_rme_movement_overlay_contract,
    indicator_colors,
    movement_flags_for_stack,
)
from .semantic_tile_render_adapter import SemanticTileRenderAdapter
from .sprites import SpriteRenderModel, SpriteTileRenderer

__all__ = [
    "AppearanceRenderLoader",
    "AppearanceRenderModel",
    "RenderedTile",
    "AppearanceTileRenderer",
    "IngameRenderMode",
    "IngameRenderState",
    "IngameTileVisual",
    "IngameVisualQA",
    "IngameVisualQAResult",
    "RenderCache",
    "RMEDrawOrderEngine",
    "RMEStackItem",
    "audit_rme_mapcolor_contract",
    "dominant_stack_mapcolor",
    "resolve_rme_mapcolor",
    "rme_minimap_color_to_rgb",
    "audit_rme_movement_overlay_contract",
    "indicator_colors",
    "movement_flags_for_stack",
    "SemanticTileRenderAdapter",
    "SpriteRenderModel",
    "SpriteTileRenderer",
]
