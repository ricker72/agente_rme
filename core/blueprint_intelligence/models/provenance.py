"""BI-1 canonical provenance model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Provenance:
    """Source and reproducibility metadata required by v1.1 Rules 3 and 4."""

    source: str
    dataset: str
    generator_version: str
    seed: int
    timestamp: str

    def __post_init__(self) -> None:
        _require_str("source", self.source)
        _require_str("dataset", self.dataset)
        _require_str("generator_version", self.generator_version)
        if not isinstance(self.seed, int) or isinstance(self.seed, bool):
            raise TypeError("seed must be an int")
        _require_str("timestamp", self.timestamp)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "dataset": self.dataset,
            "generator_version": self.generator_version,
            "seed": self.seed,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Provenance:
        return cls(
            source=data["source"],
            dataset=data["dataset"],
            generator_version=data["generator_version"],
            seed=data["seed"],
            timestamp=data["timestamp"],
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Provenance:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("Provenance JSON must decode to an object")
        return cls.from_dict(data)


def _require_str(field_name: str, value: object) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")


__all__ = ["Provenance"]
