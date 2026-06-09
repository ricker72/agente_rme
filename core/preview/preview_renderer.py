"""
Preview Renderer — núcleo de renderizado de tiles a píxeles.

Convierte tile.ground, tile.items, tile.spawn en colores RGB
usando la paleta definida en palette.py.

Flujo:
    WorldModel → renderizar tiles → imagen PIL → PNG
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from . import palette


def compute_bounds(tiles) -> Optional[Dict[str, int]]:
    """
    Calcula el bounding box de un conjunto de tiles.
    
    Returns:
        Dict con min_x, max_x, min_y, max_y, min_z, max_z
        o None si no hay tiles.
    """
    xs, ys, zs = [], [], []
    for tile in tiles.values():
        tx = getattr(tile, "x", None)
        ty = getattr(tile, "y", None)
        tz = getattr(tile, "z", None)
        if tx is not None:
            xs.append(tx)
        if ty is not None:
            ys.append(ty)
        if tz is not None:
            zs.append(tz)

    if not xs or not ys:
        return None

    return {
        "min_x": min(xs), "max_x": max(xs),
        "min_y": min(ys), "max_y": max(ys),
        "min_z": min(zs), "max_z": max(zs),
    }


def render_tile(tile: Any) -> Tuple[int, int, int]:
    """
    Renderiza un tile individual a un color RGB.

    Prioridad de render:
        1. Spawn (rojo) o Boss (naranja) si tiene spawn
        2. Items decorativos (verde) si tiene items conocidos
        3. Ground (gris) / Wall (gris oscuro) según ground ID
        4. Vacío (casi negro) si no hay nada

    Args:
        tile: Una instancia de Tile de WorldModel.

    Returns:
        Tupla RGB (r, g, b).
    """
    if tile is None:
        return palette.EMPTY

    # 1. Spawn / Boss
    spawn = getattr(tile, "spawn", None)
    if spawn is not None:
        monster_name = getattr(spawn, "monster", "")
        if monster_name and palette.is_boss(monster_name):
            return palette.BOSS
        return palette.SPAWN

    # 2. Items decorativos
    items = getattr(tile, "items", [])
    if items:
        for item in items:
            item_id = getattr(item, "itemid", None)
            if item_id is None:
                item_id = item.get("id") if isinstance(item, dict) else None
            if item_id is not None:
                item_color = palette.get_color_for_item(item_id)
                if item_color != palette.DECORATION:
                    return item_color
        return palette.DECORATION

    # 3. Ground (incluye paredes)
    ground = getattr(tile, "ground", None)
    if ground is not None:
        return palette.get_color_for_ground(ground)

    return palette.EMPTY


def render_layer(
    tiles: Dict[str, Any],
    z: int = 7,
    tile_size: int = 4,
    padding: int = 1,
) -> Optional["Image.Image"]:
    """
    Renderiza una capa Z completa a una imagen PIL.

    Args:
        tiles: Dict de tiles del WorldModel (world.tiles).
        z: Capa Z a renderizar.
        tile_size: Tamaño de cada tile en píxeles.
        padding: Celdas de borde adicional (para margen visual).

    Returns:
        Imagen PIL, o None si PIL no está disponible.
    """
    if not HAS_PIL:
        return None

    bounds = compute_bounds(tiles)
    if bounds is None:
        return None

    min_x, max_x = bounds["min_x"], bounds["max_x"]
    min_y, max_y = bounds["min_y"], bounds["max_y"]

    grid_w = (max_x - min_x) + 1 + padding * 2
    grid_h = (max_y - min_y) + 1 + padding * 2

    img_w = grid_w * tile_size
    img_h = grid_h * tile_size

    img = Image.new("RGB", (img_w, img_h), palette.EMPTY)
    draw = ImageDraw.Draw(img)

    for tile in tiles.values():
        tx = getattr(tile, "x", None)
        ty = getattr(tile, "y", None)
        tz = getattr(tile, "z", None)

        if tx is None or ty is None or tz != z:
            continue

        color = render_tile(tile)
        col = (tx - min_x) + padding
        row = (ty - min_y) + padding

        x1 = col * tile_size
        y1 = row * tile_size
        draw.rectangle(
            [x1, y1, x1 + tile_size - 1, y1 + tile_size - 1],
            fill=color,
        )

    return img


def render_all_layers(
    tiles: Dict[str, Any],
    tile_size: int = 4,
    padding: int = 1,
) -> Dict[int, "Image.Image"]:
    """
    Renderiza todas las capas Z como imágenes separadas.

    Args:
        tiles: Dict de tiles del WorldModel.
        tile_size: Tamaño de cada tile en píxeles.
        padding: Celdas de borde adicional.

    Returns:
        Dict {z_layer: Image}.
    """
    z_layers = set()
    for tile in tiles.values():
        tz = getattr(tile, "z", None)
        if tz is not None:
            z_layers.add(tz)

    images = {}
    for z in sorted(z_layers):
        img = render_layer(tiles, z=z, tile_size=tile_size, padding=padding)
        if img is not None:
            images[z] = img

    return images


def add_structure_overlay(
    img: "Image.Image",
    structures: List[Any],
    bounds: Dict[str, int],
    z: int = 7,
    tile_size: int = 4,
    padding: int = 1,
    outline_color: Tuple[int, int, int] = palette.TEMPLE,
) -> "Image.Image":
    """
    Dibuja rectángulos de estructura sobre la imagen.

    Args:
        img: Imagen PIL base.
        structures: Lista de Structure del WorldModel.
        bounds: Bounding box del mapa.
        z: Capa Z a dibujar.
        tile_size: Tamaño del tile en píxeles.
        padding: Padding usado al renderizar.
        outline_color: Color del borde.

    Returns:
        Imagen con overlays dibujados.
    """
    draw = ImageDraw.Draw(img)
    min_x, min_y = bounds["min_x"], bounds["min_y"]

    for struct in structures:
        sz = getattr(struct, "z", 7)
        if sz != z:
            continue

        sx = getattr(struct, "x", 0)
        sy = getattr(struct, "y", 0)
        sw = getattr(struct, "width", 1)
        sh = getattr(struct, "height", 1)

        col = (sx - min_x) + padding
        row = (sy - min_y) + padding

        x1 = col * tile_size
        y1 = row * tile_size
        x2 = (col + sw) * tile_size - 1
        y2 = (row + sh) * tile_size - 1

        draw.rectangle([x1, y1, x2, y2], outline=outline_color, width=2)

        # Nombre de la estructura
        name = getattr(struct, "name", "")
        if name:
            try:
                font = ImageFont.load_default()
                draw.text((x1 + 2, y1 + 2), name, fill=(255, 255, 255), font=font)
            except Exception:
                pass

    return img