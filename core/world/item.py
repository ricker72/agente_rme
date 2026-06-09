from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class Item:
    """
    An item placed on a tile.

    Architecture:
      - itemid: The client ID of the item (ground, wall, decoration, etc.)
      - count: Stack count (default 1). 0 means "infinite" for some items.
      - actionid: Optional action ID for scripting.
      - uniqueid: Optional unique ID for scripting.
    """
    itemid: int
    count: int = 1
    actionid: Optional[int] = None
    uniqueid: Optional[int] = None

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "itemid": self.itemid,
            "count": self.count,
        }
        if self.actionid is not None:
            d["actionid"] = self.actionid
        if self.uniqueid is not None:
            d["uniqueid"] = self.uniqueid
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Item:
        return cls(
            itemid=data["itemid"] if "itemid" in data else data.get("id", 0),
            count=data.get("count", 1),
            actionid=data.get("actionid"),
            uniqueid=data.get("uniqueid"),
        )

    def __repr__(self) -> str:
        parts = [f"itemid={self.itemid}"]
        if self.count != 1:
            parts.append(f"count={self.count}")
        if self.actionid is not None:
            parts.append(f"aid={self.actionid}")
        if self.uniqueid is not None:
            parts.append(f"uid={self.uniqueid}")
        return f"Item({', '.join(parts)})"