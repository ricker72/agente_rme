"""
core.preview — sistema de preview de mapas.

Estructura:
    palette.py            → colores y clasificación de IDs
    preview_renderer.py   → renderizado de tiles a píxeles
    minimap_renderer.py   → minimapa escalado
    preview_report.py     → reporte JSON de estadísticas
    preview_generator.py  → orquestador principal

Uso:
    from core.preview import PreviewGenerator

    generator = PreviewGenerator()
    generator.generate(world, output_png="output/preview.png")
    # → output/preview.png
    # → output/preview_minimap.png
    # → output/preview.json
"""

from .heatmap_renderer import HeatmapRenderer
from .minimap_renderer import MinimapRenderer
from .minimap_renderer import render_minimap, save_minimap
from .structure_renderer import StructureRenderer
from .tile_renderer import TileRenderer
from .palette import (
    GROUND,
    WALL,
    WATER,
    SPAWN,
    BOSS,
    DECORATION,
    TEMPLE,
    EMPTY,
    STRUCTURE,
    WALL_IDS,
    GROUND_IDS,
    WATER_IDS,
    DECORATION_IDS,
    BOSS_MONSTERS,
    get_color_for_ground,
    get_color_for_item,
    is_boss,
)
from .preview_renderer import (
    render_tile,
    render_layer,
    render_all_layers,
    compute_bounds,
    add_structure_overlay,
)
from .preview_report import generate_report
from .preview_generator import PreviewGenerator

__all__ = [
    # Legacy V1 classes
    "HeatmapRenderer",
    "MinimapRenderer",
    "StructureRenderer",
    "TileRenderer",
    # Palette
    "GROUND",
    "WALL",
    "WATER",
    "SPAWN",
    "BOSS",
    "DECORATION",
    "TEMPLE",
    "EMPTY",
    "STRUCTURE",
    "WALL_IDS",
    "GROUND_IDS",
    "WATER_IDS",
    "DECORATION_IDS",
    "BOSS_MONSTERS",
    "get_color_for_ground",
    "get_color_for_item",
    "is_boss",
    # Renderer
    "render_tile",
    "render_layer",
    "render_all_layers",
    "compute_bounds",
    "add_structure_overlay",
    # Minimap
    "render_minimap",
    "save_minimap",
    # Report
    "generate_report",
    # Generator
    "PreviewGenerator",
]
