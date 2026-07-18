from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.editor.item_type_flags import RMEItemTypeCatalog
from core.editor.rme_fidelity_gate import _load_invalid_ground_ids, _load_sprite_backed_item_ids
from core.otbm.otbm_importer import OTBMAttributeReader, OTBMNode, OTBMNodeReader
from rme_rendering.rme_draw_order import RMEDrawOrderEngine


@dataclass(frozen=True)
class ItemSafetyReport:
    status: str
    source: str
    full_file_scanned: bool
    tiles_checked: int
    stack_items_checked: int
    container_items_checked: int
    sprite_backed_items: int
    issue_counts: dict[str, int]
    issue_samples: tuple[dict[str, Any], ...]
    contracts: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {"stage": "Item Safety Full-map Certification", **asdict(self)}


class OTBMItemSafetyCertifier:
    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)
        self.catalog = RMEItemTypeCatalog.load(self.root)
        self.sprite_backed = _load_sprite_backed_item_ids(self.root)
        self.invalid_ground = _load_invalid_ground_ids(self.root)
        if not self.invalid_ground:
            self.invalid_ground = {
                item_id
                for item_id, item in self.catalog.items.items()
                if not item.is_ground and (
                    item.pickupable
                    or item.is_border
                    or item.is_wall
                    or item.is_table
                    or item.is_carpet
                    or item.is_door
                    or item.is_container
                    or item.is_teleport
                    or item.is_depot
                )
            }
        self.draw_order = RMEDrawOrderEngine(self.catalog)

    def certify(self, otbm_path: str | Path) -> ItemSafetyReport:
        path = Path(otbm_path)
        issues: Counter[str] = Counter()
        samples: list[dict[str, Any]] = []
        current: dict[str, Any] | None = None
        tiles_checked = stack_items = container_items = sprite_items = 0

        def add_issue(code: str, item_id: int | None, position: tuple[int, int, int] | None) -> None:
            issues[code] += 1
            if len(samples) < 100:
                samples.append({"code": code, "item_id": item_id, "position": position})

        def check_sprite(item_id: int, position: tuple[int, int, int]) -> None:
            nonlocal sprite_items
            if item_id in self.sprite_backed:
                sprite_items += 1
            else:
                add_issue("MISSING_OFFICIAL_SPRITE", item_id, position)

        def finish_tile() -> None:
            nonlocal current, tiles_checked, stack_items
            if current is None:
                return
            tiles_checked += 1
            stack = current["stack"]
            position = current["position"]
            stack_items += len(stack)
            if not stack:
                add_issue("MISSING_GROUND", None, position)
                current = None
                return
            # OTBM files in the wild can contain more than one ground candidate.
            # Canary accepts this representation and Tile::addLoadedItem/update
            # keeps the final ground while ordering the remaining bottom items.
            ground, ordered_items = self.catalog.classify_stack(stack)
            canonical_stack = ([ground] if ground is not None else []) + ordered_items
            if ground is None:
                add_issue("MISSING_GROUND", None, position)
                current = None
                return
            item_type = self.catalog.get(ground)
            if (
                not item_type.is_ground
                or item_type.pickupable
                or (ground in self.invalid_ground and not item_type.is_ground)
            ):
                add_issue("INVALID_GROUND_ITEM", ground, position)
            for item_id in stack:
                if self.catalog.get(item_id).flag_source != "appearances.dat:Canary loadFromProtobuf":
                    add_issue("NON_EXACT_ITEMTYPE_FLAGS", item_id, position)
            expected = self.draw_order.sort_item_ids(canonical_stack)
            if expected != canonical_stack:
                add_issue("DRAW_ORDER_MISMATCH", None, position)
            for item_id in stack:
                check_sprite(item_id, position)
            current = None

        area: tuple[int, int, int] | None = None

        def on_node(node: OTBMNode, _context: dict[str, Any]) -> None:
            nonlocal area, current, container_items
            if node.node_type == 0x04:
                finish_tile()
                try:
                    area = OTBMAttributeReader.parse_tile_area(node.attrs)
                except ValueError:
                    area = None
            elif node.node_type in (0x05, 0x0E) and area is not None:
                finish_tile()
                tile = OTBMAttributeReader.parse_tile(
                    node.attrs,
                    *area,
                    house=node.node_type == 0x0E,
                )
                current = {
                    "position": (tile["x"], tile["y"], tile["z"]),
                    "depth": node.depth,
                    "stack": _inline_ground(node.attrs, node.node_type == 0x0E),
                }
            elif node.node_type == 0x06 and current is not None:
                try:
                    item_id = OTBMAttributeReader.parse_item(node.attrs)["id"]
                except ValueError:
                    add_issue("INVALID_ITEM_PAYLOAD", None, current["position"])
                    return
                if node.depth == current["depth"] + 1:
                    current["stack"].append(item_id)
                else:
                    container_items += 1
                    check_sprite(item_id, current["position"])

        with OTBMNodeReader(path) as reader:
            stats = reader.traverse(on_node, max_nodes=None, max_bytes=None)
        finish_tile()
        contracts = {
            "official_sprite_catalog_loaded": bool(self.sprite_backed),
            "item_type_catalog_loaded": bool(self.catalog.items),
            "invalid_ground_catalog_loaded": bool(self.invalid_ground),
            "full_file_not_truncated": not stats.truncated,
            "exact_canary_itemtype_flags": bool(self.catalog.items) and all(
                item.flag_source == "appearances.dat:Canary loadFromProtobuf"
                for item in self.catalog.items.values()
                if item.client_id is not None
            ),
            "canary_draw_order_engine": self.draw_order.audit()["canary_tile_add_item_order"],
        }
        if not all(contracts.values()):
            issues["CATALOG_CONTRACT_MISSING"] += sum(not value for value in contracts.values())
        return ItemSafetyReport(
            "PASS" if not issues else "BLOCKED",
            str(path),
            not stats.truncated,
            tiles_checked,
            stack_items,
            container_items,
            sprite_items,
            dict(sorted(issues.items())),
            tuple(samples),
            contracts,
        )


def _inline_ground(attrs: bytes, house: bool) -> list[int]:
    offset = 6 if house else 2
    items: list[int] = []
    while offset < len(attrs):
        attribute = attrs[offset]
        offset += 1
        if attribute == 0x03 and offset + 4 <= len(attrs):
            offset += 4
        elif attribute == 0x09 and offset + 2 <= len(attrs):
            items.append(int.from_bytes(attrs[offset : offset + 2], "little"))
            offset += 2
        else:
            break
    return items
