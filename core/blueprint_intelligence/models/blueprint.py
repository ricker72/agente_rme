"""BI-1 canonical blueprint model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, ClassVar

from .provenance import Provenance


@dataclass(slots=True)
class Blueprint:
    """Canonical structural blueprint shared across v1.1 subsystems."""

    VALID_BLUEPRINT_TYPES: ClassVar[frozenset[str]] = frozenset(
        {
            "city",
            "hunt",
            "dungeon",
            "boss_area",
            "quest_chain",
            "region",
        }
    )

    blueprint_id: str
    name: str
    blueprint_type: str
    width: int
    height: int
    regions: list[str]
    patterns: list[str]
    constraints: list[str]
    provenance: Provenance

    def __post_init__(self) -> None:
        _require_str("blueprint_id", self.blueprint_id)
        _require_str("name", self.name)
        _require_str("blueprint_type", self.blueprint_type)
        if self.blueprint_type not in self.VALID_BLUEPRINT_TYPES:
            raise ValueError(f"Invalid blueprint_type: {self.blueprint_type}")
        _require_int("width", self.width)
        _require_int("height", self.height)
        _require_str_list("regions", self.regions)
        _require_str_list("patterns", self.patterns)
        _require_str_list("constraints", self.constraints)
        if not isinstance(self.provenance, Provenance):
            raise TypeError("provenance must be a Provenance")

    def to_dict(self) -> dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "blueprint_type": self.blueprint_type,
            "width": self.width,
            "height": self.height,
            "regions": list(self.regions),
            "patterns": list(self.patterns),
            "constraints": list(self.constraints),
            "provenance": self.provenance.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Blueprint:
        provenance_raw = data["provenance"]
        if not isinstance(provenance_raw, dict):
            raise TypeError("provenance must be an object")
        return cls(
            blueprint_id=data["blueprint_id"],
            name=data["name"],
            blueprint_type=data["blueprint_type"],
            width=data["width"],
            height=data["height"],
            regions=data["regions"],
            patterns=data["patterns"],
            constraints=data["constraints"],
            provenance=Provenance.from_dict(provenance_raw),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Blueprint:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("Blueprint JSON must decode to an object")
        return cls.from_dict(data)


def _require_str(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _require_int(field_name: str, value: object) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_str_list(field_name: str, value: object) -> None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{field_name} must be a list[str]")


__all__ = ["Blueprint"]
