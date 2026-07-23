from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class TeleportDestination:
    x: int
    y: int
    z: int

    def __post_init__(self) -> None:
        _range("teleport x", self.x, 0xFFFF)
        _range("teleport y", self.y, 0xFFFF)
        _range("teleport z", self.z, 0xFF)

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "z": self.z}


@dataclass
class EditableItem:
    item_id: int
    action_id: int = 0
    unique_id: int = 0
    text: str = ""
    description: str = ""
    count: int | None = None
    charges: int | None = None
    depot_id: int = 0
    house_door_id: int = 0
    teleport_destination: TeleportDestination | None = None
    children: list["EditableItem"] = field(default_factory=list)
    extra_attributes: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _range("item id", self.item_id, 0xFFFF, minimum=1)
        _optional_range("action id", self.action_id, 100, 0xFFFF)
        _optional_range("unique id", self.unique_id, 1000, 0xFFFF)
        _range("depot id", self.depot_id, 0xFFFF)
        _range("house door id", self.house_door_id, 0xFF)
        if self.count is not None:
            _range("count", self.count, 0xFF)
        if self.charges is not None:
            _range("charges", self.charges, 0xFFFF)

    def add_child(self, item: "EditableItem") -> None:
        if item is self or item.contains(self):
            raise ValueError("Container item cycle detected")
        self.children.append(item)

    def contains(self, target: "EditableItem") -> bool:
        return any(child is target or child.contains(target) for child in self.children)

    def walk(self) -> Iterable["EditableItem"]:
        yield self
        for child in self.children:
            yield from child.walk()

    def attributes(self) -> dict[str, Any]:
        values: dict[str, Any] = copy.deepcopy(self.extra_attributes)
        for key, value in (
            ("action_id", self.action_id),
            ("unique_id", self.unique_id),
            ("text", self.text),
            ("description", self.description),
            ("count", self.count),
            ("charges", self.charges),
            ("depot_id", self.depot_id),
            ("house_door_id", self.house_door_id),
            ("teleport_destination", self.teleport_destination.to_dict() if self.teleport_destination else None),
        ):
            if value not in (None, "", 0):
                values[key] = value
        return values

    def copy(self) -> "EditableItem":
        return EditableItem(
            item_id=self.item_id,
            action_id=self.action_id,
            unique_id=self.unique_id,
            text=self.text,
            description=self.description,
            count=self.count,
            charges=self.charges,
            depot_id=self.depot_id,
            house_door_id=self.house_door_id,
            teleport_destination=self.teleport_destination,
            children=[child.copy() for child in self.children],
            extra_attributes=copy.deepcopy(self.extra_attributes),
        )


def _range(name: str, value: int, maximum: int, minimum: int = 0) -> None:
    if not minimum <= int(value) <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


def _optional_range(name: str, value: int, minimum: int, maximum: int) -> None:
    if int(value) != 0 and not minimum <= int(value) <= maximum:
        raise ValueError(f"{name} must be 0 or between {minimum} and {maximum}")
