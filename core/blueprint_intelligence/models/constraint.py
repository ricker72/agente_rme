"""BI-1 canonical generation constraint model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


@dataclass(slots=True)
class Constraint:
    """Generator-ready constraint derived from learned blueprint patterns."""

    constraint_id: str
    name: str
    value: object
    required: bool

    def __post_init__(self) -> None:
        _require_str("constraint_id", self.constraint_id)
        _require_str("name", self.name)
        if not _is_json_value(self.value):
            raise ValueError("value must be JSON serializable")
        if not isinstance(self.required, bool):
            raise TypeError("required must be a bool")

    def to_dict(self) -> dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "name": self.name,
            "value": self.value,
            "required": self.required,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Constraint:
        return cls(
            constraint_id=data["constraint_id"],
            name=data["name"],
            value=data["value"],
            required=data["required"],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Constraint:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("Constraint JSON must decode to an object")
        return cls.from_dict(data)


def _require_str(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


def _is_json_value(value: object) -> bool:
    if value is None or isinstance(value, (bool, int, float, str)):
        return True
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


__all__ = ["Constraint", "JsonValue"]
