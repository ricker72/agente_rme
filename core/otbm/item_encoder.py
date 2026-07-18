"""
Item Encoder — convierte Items de WorldModel a nodos OTBM ITEM.

Tile(
    x=1000, y=1000, z=7,
    items=[Item(itemid=9043), Item(itemid=2050)]
)
↓
Nodo OTBM ITEM por cada item.
"""

from __future__ import annotations

from typing import Any, cast

# Import NodeEncoder locally to avoid circular imports


class ItemEncoder:
    """
    Codifica items individuales a nodos OTBM ITEM.

    Cada ITEM node contiene:
      - item_id (uint16)
      - Atributos opcionales: count, action_id, unique_id, text, charges, subtype, duration
      - Children (para contenedores con items anidados)
    """

    def __init__(self):
        # Import NodeEncoder locally to avoid circular imports
        from .node_encoder import NodeEncoder

        self.node = NodeEncoder()

    def encode(self, item: Any) -> bytes:
        """
        Codifica un item (dict o Item dataclass) a nodo OTBM ITEM.

        Args:
            item: Puede ser:
                - Dict con claves 'id'/'itemid', 'count', 'action_id', etc.
                - Item dataclass con atributos itemid, count, action_id, etc.
                - int (solo item_id)

        Returns:
            bytes: Nodo OTBM ITEM listo para insertar en un TILE.
        """
        (
            item_id,
            count,
            action_id,
            unique_id,
            text,
            subtype,
            charges,
            duration,
            decaying,
        ) = self._extract_attributes(item)

        return cast(
            bytes,
            self.node.encode_item(
                item_id=item_id,
                count=count,
                action_id=action_id,
                unique_id=unique_id,
                text=text,
                subtype=subtype,
                charges=charges,
                duration=duration,
                decaying_state=decaying,
            ),
        )

    def encode_ground(self, ground_id: int) -> bytes:
        """
        Codifica un ground como item OTBM.

        Args:
            ground_id: ID numérico del ground.

        Returns:
            bytes: Nodo OTBM ITEM para el ground.
        """
        return cast(bytes, self.node.encode_item(item_id=ground_id))

    @staticmethod
    def _extract_attributes(item: Any) -> tuple:
        """Extrae atributos normalizados de un item en cualquier formato."""
        item_id = 0
        count = None
        action_id = None
        unique_id = None
        text = None
        subtype = None
        charges = None
        duration = None
        decaying = None

        if isinstance(item, (int, float)):
            item_id = int(item)
        elif isinstance(item, dict):
            item_id = int(cast(Any, item.get("id", item.get("itemid", 0))))
            count = item.get("count")
            action_id = item.get("action_id")
            unique_id = item.get("unique_id")
            text = item.get("text")
            subtype = item.get("subtype")
            charges = item.get("charges")
            duration = item.get("duration")
            decaying = item.get("decaying_state")
        elif hasattr(item, "itemid"):
            item_id = int(item.itemid)
            if hasattr(item, "count") and item.count is not None:
                count = int(item.count)
            if hasattr(item, "action_id"):
                action_id = getattr(item, "action_id", None)
            if hasattr(item, "unique_id"):
                unique_id = getattr(item, "unique_id", None)
            if hasattr(item, "text"):
                text = getattr(item, "text", None)
        else:
            item_id = int(getattr(item, "id", getattr(item, "itemid", 0)))

        return (
            item_id,
            count,
            action_id,
            unique_id,
            text,
            subtype,
            charges,
            duration,
            decaying,
        )
