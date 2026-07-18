from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from PySide6.QtGui import QColor


@dataclass(frozen=True)
class RMEMovementFlags:
    blocking: bool = False
    block_pathfinder: bool = False
    pickupable: bool = False
    moveable: bool = False
    avoidable: bool = False
    ground_speed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocking": self.blocking,
            "block_pathfinder": self.block_pathfinder,
            "pickupable": self.pickupable,
            "moveable": self.moveable,
            "avoidable": self.avoidable,
            "ground_speed": self.ground_speed,
        }


def movement_flags_for_model(model: Any) -> RMEMovementFlags:
    flags = {str(k).lower(): v for k, v in dict(getattr(model, "flags", {}) or {}).items()}
    moveable = _truthy(flags.get("moveable"))
    if "unmove" in flags:
        moveable = not _truthy(flags.get("unmove"))
    return RMEMovementFlags(
        blocking=_truthy(flags.get("unpassable") or flags.get("blocksolid") or flags.get("block_solid")),
        block_pathfinder=_truthy(flags.get("blockpathfinder") or flags.get("block_pathfinder") or flags.get("avoid")),
        pickupable=_truthy(flags.get("pickupable") or flags.get("take")),
        moveable=moveable,
        avoidable=_truthy(flags.get("avoid") or flags.get("blockpathfinder") or flags.get("block_pathfinder")),
        ground_speed=_int_or_zero(flags.get("speed") or flags.get("groundspeed") or flags.get("ground_speed")),
    )


def movement_flags_for_stack(stack: Iterable[Any]) -> RMEMovementFlags:
    result = RMEMovementFlags()
    for tile in stack:
        item = movement_flags_for_model(tile.model)
        result = RMEMovementFlags(
            blocking=result.blocking or item.blocking,
            block_pathfinder=result.block_pathfinder or item.block_pathfinder,
            pickupable=result.pickupable or item.pickupable,
            moveable=result.moveable or item.moveable,
            avoidable=result.avoidable or item.avoidable,
            ground_speed=max(result.ground_speed, item.ground_speed),
        )
    return result


def indicator_colors(flags: RMEMovementFlags) -> list[tuple[str, QColor]]:
    colors: list[tuple[str, QColor]] = []
    if flags.blocking:
        colors.append(("blocking", QColor(166, 0, 0, 170)))
    if flags.block_pathfinder or flags.avoidable:
        colors.append(("avoidable", QColor(255, 170, 0, 170)))
    if flags.pickupable and flags.moveable:
        colors.append(("pickupable_moveable", QColor(80, 170, 255, 190)))
    elif flags.pickupable:
        colors.append(("pickupable", QColor(255, 255, 80, 190)))
    elif flags.moveable:
        colors.append(("moveable", QColor(80, 255, 120, 190)))
    if flags.ground_speed:
        colors.append(("ground_speed", QColor(130, 210, 255, 130)))
    return colors


def audit_rme_movement_overlay_contract() -> dict[str, Any]:
    return {
        "rme_movement_overlay_ready": True,
        "source": "RME ItemType flags + MapDrawer::DrawTileIndicators",
        "supported_flags": ["blocking", "block_pathfinder", "pickupable", "moveable", "avoidable", "ground_speed"],
    }


def _truthy(value: Any) -> bool:
    return str(value).lower() in {"1", "true", "yes"}


def _int_or_zero(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
