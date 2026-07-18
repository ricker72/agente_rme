from __future__ import annotations

from dataclasses import dataclass
from typing import Any


DRAW_ORDER_PRIORITY = {
    "GROUND": 10,
    "WATER": 10,
    "ROAD": 12,
    "BORDER": 20,
    "RAMP": 24,
    "STAIR": 25,
    "CARPET": 28,
    "INTERIOR": 30,
    "EXTERIOR": 32,
    "DOCK": 34,
    "WALL": 40,
    "WINDOW": 42,
    "DOOR": 43,
    "TABLE": 48,
    "DECORATION": 55,
    "NATURE": 58,
    "ROOF": 70,
    "SPAWN_OBJECT": 80,
    "CREATURE": 90,
    "EFFECT": 100,
    "UNKNOWN": 60,
}


@dataclass(frozen=True)
class RMEStackItem:
    item_id: int
    role: str
    appearance_id: int | None = None
    name: str = ""
    source_index: int = 0

    @property
    def priority(self) -> int:
        return DRAW_ORDER_PRIORITY.get(self.role.upper(), DRAW_ORDER_PRIORITY["UNKNOWN"])


class RMEDrawOrderEngine:
    def __init__(self, item_catalog: Any | None = None) -> None:
        self.item_catalog = item_catalog

    def sort_stack(self, items: list[RMEStackItem]) -> list[RMEStackItem]:
        if self.item_catalog is not None:
            ground = [item for item in items if self.item_catalog.get(item.item_id).is_ground]
            rest = [item for item in items if not self.item_catalog.get(item.item_id).is_ground]
            by_identity = {id(item): item for item in rest}
            ordered_objects: list[RMEStackItem] = []
            working: list[RMEStackItem] = []
            for item in rest:
                item_type = self.item_catalog.get(item.item_id)
                if item_type.ground_equivalent:
                    working.insert(0, item)
                elif not item_type.always_on_bottom:
                    working.append(item)
                else:
                    index = len(working)
                    for candidate_index, candidate in enumerate(working):
                        candidate_type = self.item_catalog.get(candidate.item_id)
                        if (
                            not candidate_type.always_on_bottom
                            or item_type.always_on_top_order < candidate_type.always_on_top_order
                        ):
                            index = candidate_index
                            break
                    working.insert(index, item)
            ordered_objects.extend(by_identity[id(item)] for item in working)
            return ground[-1:] + ordered_objects
        return sorted(items, key=lambda item: (item.priority, item.source_index, item.item_id))

    def sort_item_ids(self, item_ids: list[int]) -> list[int]:
        if self.item_catalog is None:
            raise ValueError("Exact Canary draw order requires an ItemType catalog")
        ground, items = self.item_catalog.classify_stack(item_ids)
        return ([ground] if ground is not None else []) + items

    def sort_tile_dicts(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        stack = [
            RMEStackItem(
                item_id=int(item.get("item_id") or item.get("id") or 0),
                appearance_id=int(item["appearance_id"]) if item.get("appearance_id") is not None else None,
                role=str(item.get("role") or item.get("ground_role") or "UNKNOWN").upper(),
                name=str(item.get("name") or item.get("ground_name") or ""),
                source_index=index,
            )
            for index, item in enumerate(items)
        ]
        order_by_key = {
            (stack_item.item_id, stack_item.source_index): order
            for order, stack_item in enumerate(self.sort_stack(stack))
        }
        sorted_pairs = sorted(
            enumerate(items),
            key=lambda indexed: order_by_key[(int(indexed[1].get("item_id") or indexed[1].get("id") or 0), indexed[0])],
        )
        return [item for _index, item in sorted_pairs]

    def audit(self) -> dict[str, Any]:
        return {
            "rme_draw_order_ready": True,
            "priority_count": len(DRAW_ORDER_PRIORITY),
            "ground_first": DRAW_ORDER_PRIORITY["GROUND"] < DRAW_ORDER_PRIORITY["BORDER"] < DRAW_ORDER_PRIORITY["WALL"],
            "roof_above_walls": DRAW_ORDER_PRIORITY["ROOF"] > DRAW_ORDER_PRIORITY["WALL"],
            "creatures_above_map_items": DRAW_ORDER_PRIORITY["CREATURE"] > DRAW_ORDER_PRIORITY["DECORATION"],
            "canary_tile_add_item_order": self.item_catalog is not None,
            "source": "Canary tile.cpp Tile::addItem/findBottomInsertPosition + MapDrawer item iteration",
        }
