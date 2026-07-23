"""Headless-safe rendering contracts shared by Engine and desktop applications."""

from .ingame_render_mode import IngameRenderMode, IngameRenderState, IngameTileVisual
from .asset_paths import resolve_client_asset_root
from .rme_draw_order import RMEDrawOrderEngine, RMEStackItem
from .rme_mapcolors import RMEMapColor, dominant_stack_mapcolor, rme_minimap_color_to_rgb
from .rme_visual_compat import RMEDrawingOptions, RMEViewState, audit_rme_visual_contract

__all__ = [
    "IngameRenderMode",
    "IngameRenderState",
    "IngameTileVisual",
    "RMEDrawOrderEngine",
    "RMEDrawingOptions",
    "RMEMapColor",
    "RMEStackItem",
    "RMEViewState",
    "audit_rme_visual_contract",
    "dominant_stack_mapcolor",
    "rme_minimap_color_to_rgb",
    "resolve_client_asset_root",
]
