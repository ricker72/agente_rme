"""
House Encoder — prepara datos de houses para houses.xml compatible con OTServBR.

Exporta:
  - houses.xml con ubicaciones de houses
  - Nodos OTBM HOUSETILE si hay houses definidas
"""

from __future__ import annotations

from typing import Any, Dict, List

# Import NodeEncoder locally to avoid circular imports


class HouseEncoder:
    """
    Prepara datos de houses para exportación OTBM + houses.xml.

    Detecta houses por:
      - Atributo 'house_id' en tiles
      - Estructuras con category='house'
      - Tiles con ground en IDs de house
    """

    HOUSE_GROUND_IDS = {900, 901, 902, 903, 904, 905}

    def __init__(self):
        # Import NodeEncoder locally to avoid circular imports
        from .node_encoder import NodeEncoder

        self.node = NodeEncoder()

    def extract_houses(self, world_model: Any) -> List[Dict[str, Any]]:
        """
        Extrae lista de houses del WorldModel.

        Args:
            world_model: WorldModel instance.

        Returns:
            Lista de dicts con datos de houses.
        """
        houses: List[Dict[str, Any]] = []
        tiles = getattr(world_model, "tiles", {})

        # Detectar por ground ID o atributo house_id
        for tile in tiles.values():
            ground = getattr(tile, "ground", None)
            house_id = getattr(tile, "house_id", None)
            if house_id is not None or (ground is not None and ground in self.HOUSE_GROUND_IDS):
                houses.append(
                    {
                        "id": house_id or len(houses) + 1,
                        "x": getattr(tile, "x", 0),
                        "y": getattr(tile, "y", 0),
                        "z": getattr(tile, "z", 7),
                        "tiles": [getattr(tile, "x", 0), getattr(tile, "y", 0)],
                    }
                )

        # Detectar por estructuras con categoría house
        structures = getattr(world_model, "structures", [])
        for s in structures:
            if getattr(s, "category", "") == "house":
                houses.append(
                    {
                        "id": len(houses) + 1,
                        "x": getattr(s, "x", 0),
                        "y": getattr(s, "y", 0),
                        "z": getattr(s, "z", 7),
                        "name": getattr(s, "name", f"House{len(houses) + 1}"),
                        "size": (getattr(s, "width", 10), getattr(s, "height", 10)),
                        "tiles": [getattr(s, "x", 0), getattr(s, "y", 0)],
                    }
                )

        # Asignar IDs consistentes
        for i, h in enumerate(houses, start=1):
            h["id"] = h.get("id", i) or i

        return houses

    def generate_house_xml(self, world_model: Any) -> str:
        """
        Genera XML de houses para houses.xml (formato OTServBR).

        Args:
            world_model: WorldModel instance.

        Returns:
            String XML compatible con OTServBR.
        """
        houses = self.extract_houses(world_model)
        if not houses:
            return ""

        lines = ["<houses>"]
        for h in houses:
            name = h.get("name", f"House{h['id']}")
            lines.append(
                f'  <house id="{h["id"]}" name="{name}"><entry x="{h["x"]}" y="{h["y"]}" z="{h["z"]}" /></house>'
            )
        lines.append("</houses>")
        return "\n".join(lines)
