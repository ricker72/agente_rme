"""
Paleta de colores para el Preview Generator V1.

Define colores RGB para cada tipo de tile en el mapa.
Usado por preview_renderer.py para pintar cada píxel.
"""

# Colores base
GROUND = (180, 180, 180)  # Terreno normal — gris claro
WALL = (80, 80, 80)  # Pared/muro — gris oscuro
WATER = (0, 100, 255)  # Agua — azul
SPAWN = (255, 0, 0)  # Spawn de monstruo — rojo
DECORATION = (0, 255, 0)  # Decoración — verde
BOSS = (255, 128, 0)  # Boss — naranja
TEMPLE = (255, 255, 0)  # Estructura tipo templo — amarillo
EMPTY = (20, 20, 20)  # Vacío — casi negro
STRUCTURE = (200, 150, 50)  # Otra estructura — marrón

# Mapa de IDs de item conocidos para clasificación
# ID → nombre descriptivo (usado para determinar color)
WALL_IDS = {
    1495,
    1496,
    1497,
    1498,
    1499,
    1500,
    1501,
    1502,
    1503,
    1504,
    1505,
    1506,
    1507,
    1508,
    1509,
}
GROUND_IDS = {
    415,
    393,
    421,
    1053,
    1056,
    1057,
    396,
    397,
    398,
    514,
    513,
    516,
    428,
    429,
    430,
}
WATER_IDS = {4821, 4822, 4823, 4824, 4825, 4826}
DECORATION_IDS = {
    2153,
    2117,
    1803,
    2150,
    2151,
    2152,
    2148,
    2149,
    2154,
    2155,
    2156,
    2157,
    2158,
    2159,
    2160,
}

# Lista de monstruos considerados "boss" para renderizado especial
BOSS_MONSTERS = {
    "Demon",
    "Dragon",
    "Behemoth",
    "Ferumbras",
    "Orshabaal",
    "Ghazbaran",
    "Morgaroth",
    "Zulazza",
    "The Noxious Spawn",
    "The Pale Worm",
    "The Many",
    "Ocyakao",
    "The Imperor",
    "Plagirath",
    "The Weakened Frazzlemaw",
    "The Abomination",
}


def get_color_for_ground(ground_id):
    """
    Determina el color de un tile según su ground ID.

    Args:
        ground_id: int ID del ground del tile (o None).

    Returns:
        Tupla RGB (r, g, b).
    """
    if ground_id is None:
        return EMPTY

    if ground_id in WALL_IDS:
        return WALL

    if ground_id in WATER_IDS:
        return WATER

    if ground_id in GROUND_IDS:
        return GROUND

    # IDs desconocidos → terreno por defecto
    return GROUND


def get_color_for_item(item_id):
    """
    Determina el color para un item decorativo.

    Args:
        item_id: int ID del item.

    Returns:
        Tupla RGB (r, g, b).
    """
    if item_id in DECORATION_IDS:
        return DECORATION
    return DECORATION  # Por defecto, cualquier item es decoración


def is_boss(monster_name: str) -> bool:
    """
    Verifica si un nombre de monstruo corresponde a un boss.

    Args:
        monster_name: Nombre del monstruo.

    Returns:
        True si es un boss conocido.
    """
    return monster_name in BOSS_MONSTERS
