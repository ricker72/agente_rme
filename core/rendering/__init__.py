"""PMX-04R1 — Real Viewport Rendering Engine for the OpenTibia editor."""

from .appearance_loader import AppearanceLoader
from .appearance_models import (
    AppearanceParseReport,
    AppearanceRecord,
    MaterializedSprite,
    ResolvedSprite,
)
from .appearance_resolver import AppearanceResolver
from .chunk_renderer import CHUNK_SIZE, ChunkRenderer
from .coordinate_translator import CoordinateTranslator
from .dirty_region_manager import DirtyRegionManager
from .overlay_renderer import OverlayConfig, OverlayRenderer
from .rendering_pipeline import FPSCounter, RenderingPipeline
from .sprite_cache import SpriteCache
from .sprite_cache_lru import LRUSpriteCache
from .sprite_materializer import SpriteMaterializer
from .sprite_pixel_adapter import SpritePixelAdapter
from .sprite_pixel_decoder import SpritePixelDecoder
from .sprite_pixel_source import SpritePixelSourceDiscovery
from .sprite_resolver import SpriteResolver
from .stack_renderer import StackRenderer
from .tile_render_model import TileRenderModel
from .tile_renderer import TileRenderer

__all__ = [
    "AppearanceLoader",
    "AppearanceParseReport",
    "AppearanceRecord",
    "AppearanceResolver",
    "Camera",
    "CHUNK_SIZE",
    "ChunkRenderer",
    "CoordinateTranslator",
    "DirtyRegionManager",
    "FPSCounter",
    "LRUSpriteCache",
    "MaterializedSprite",
    "OverlayConfig",
    "OverlayRenderer",
    "RenderingPipeline",
    "ResolvedSprite",
    "SpriteCache",
    "SpriteMaterializer",
    "SpritePixelAdapter",
    "SpritePixelDecoder",
    "SpritePixelSourceDiscovery",
    "SpriteResolver",
    "StackRenderer",
    "TileRenderModel",
    "TileRenderer",
]


def __getattr__(name: str):
    if name == "Camera":
        from .camera import Camera

        return Camera
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
