"""
Minimap Renderer — genera preview_minimap.png con escalado variable.

Escalas soportadas:
    4x  → tile_size=4  (miniatura)
    8x  → tile_size=8  (mediano)
    16x → tile_size=16 (detallado)

Usa preview_renderer.py para pintar y aplica escalado.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .preview_renderer import render_layer, compute_bounds, add_structure_overlay


# Escalas disponibles: nombre → tile_size
SCALES = {
    "4x": 4,
    "8x": 8,
    "16x": 16,
}


class MinimapRenderer:
    """
    Legacy MinimapRenderer (V1) — mantiene compatibilidad con core/__init__.py.
    
    Nuevo uso: usar funciones sueltas render_minimap() / save_minimap().
    """

    def render(self, world_model: Any) -> Dict[str, object]:
        """Legacy API: devuelve un dict con grid y leyenda."""
        tiles = getattr(world_model, "tiles", {})
        if not tiles:
            return {"grid": [], "width": 0, "height": 0, "legend": {}}

        bounds = compute_bounds(tiles)
        if bounds is None:
            return {"grid": [], "width": 0, "height": 0, "legend": {}}

        width = bounds["max_x"] - bounds["min_x"] + 1
        height = bounds["max_y"] - bounds["min_y"] + 1

        grid = [[" " for _ in range(width)] for _ in range(height)]
        for tile in tiles.values():
            tx = getattr(tile, "x", None)
            ty = getattr(tile, "y", None)
            if tx is not None and ty is not None:
                col = tx - bounds["min_x"]
                row = ty - bounds["min_y"]
                if 0 <= row < height and 0 <= col < width:
                    grid[row][col] = self._tile_char(tile)

        return {
            "grid": ["".join(row) for row in grid],
            "width": width,
            "height": height,
            "x_offset": bounds["min_x"],
            "y_offset": bounds["min_y"],
            "legend": {
                "#": "wall/stone",
                ".": "ground",
                "M": "spawn",
                " ": "empty",
            },
        }

    @staticmethod
    def _tile_char(tile: Any) -> str:
        """Clasifica un tile en un caracter."""
        from .preview_renderer import render_tile
        from .palette import GROUND, WALL, SPAWN, BOSS

        color = render_tile(tile)
        if color == WALL:
            return "#"
        if color == SPAWN or color == BOSS:
            return "M"
        if color == GROUND:
            return "."
        return " "


def render_minimap(
    tiles: Dict[str, Any],
    structures: Optional[list] = None,
    z: int = 7,
    scale: str = "8x",
) -> Optional["Image.Image"]:
    """
    Genera una imagen de minimapa a la escala indicada.

    Args:
        tiles: Dict de tiles del WorldModel.
        structures: Lista de estructuras para overlay.
        z: Capa Z a renderizar.
        scale: Escala ('4x', '8x', '16x').

    Returns:
        Imagen PIL, o None si no hay PIL.
    """
    tile_size = SCALES.get(scale, 8)

    img = render_layer(tiles, z=z, tile_size=tile_size, padding=1)
    if img is None:
        return None

    if structures:
        bounds = compute_bounds(tiles)
        if bounds:
            img = add_structure_overlay(
                img, structures, bounds,
                z=z, tile_size=tile_size, padding=1,
            )

    return img


def save_minimap(
    tiles: Dict[str, Any],
    structures: Optional[list] = None,
    output_path: str = "output/preview_minimap.png",
    z: int = 7,
    scale: str = "8x",
) -> Optional[str]:
    """
    Genera y guarda el minimapa como PNG.

    Args:
        tiles: Dict de tiles del WorldModel.
        structures: Lista de estructuras.
        output_path: Ruta de salida.
        z: Capa Z.
        scale: Escala.

    Returns:
        Ruta del archivo guardado, o None si falló.
    """
    img = render_minimap(tiles, structures, z=z, scale=scale)
    if img is None:
        return None

    img.save(output_path, "PNG")
    return output_path