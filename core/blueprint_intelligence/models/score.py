"""BI-1 canonical blueprint score model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .metrics import BlueprintMetrics


@dataclass(slots=True)
class BlueprintScore:
    """Aggregate blueprint quality score plus its metric breakdown."""

    score: float
    grade: str
    metrics: BlueprintMetrics

    def __post_init__(self) -> None:
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool):
            raise TypeError("score must be a number")
        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")
        if not isinstance(self.grade, str):
            raise TypeError("grade must be a str")
        if not self.grade:
            raise ValueError("grade must not be empty")
        if not isinstance(self.metrics, BlueprintMetrics):
            raise TypeError("metrics must be a BlueprintMetrics")

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "grade": self.grade,
            "metrics": self.metrics.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlueprintScore:
        metrics_raw = data["metrics"]
        if not isinstance(metrics_raw, dict):
            raise TypeError("metrics must be an object")
        return cls(
            score=data["score"],
            grade=data["grade"],
            metrics=BlueprintMetrics.from_dict(metrics_raw),
        )

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> BlueprintScore:
        data = json.loads(payload)
        if not isinstance(data, dict):
            raise TypeError("BlueprintScore JSON must decode to an object")
        return cls.from_dict(data)


__all__ = ["BlueprintScore"]
