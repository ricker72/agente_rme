from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from PySide6.QtGui import QImage


@dataclass(frozen=True)
class IngameVisualQAResult:
    status: str
    compared_pixels: int
    average_delta: float
    max_delta: int
    size_match: bool
    source_a: str
    source_b: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IngameVisualQA:
    """Compares an agent viewport capture against a Canary/RME screenshot."""

    def __init__(self, average_delta_threshold: float = 18.0) -> None:
        self.average_delta_threshold = float(average_delta_threshold)

    def compare_images(self, canary_image: str | Path, agent_image: str | Path) -> IngameVisualQAResult:
        canary_path = Path(canary_image)
        agent_path = Path(agent_image)
        canary = QImage(str(canary_path))
        agent = QImage(str(agent_path))
        if canary.isNull() or agent.isNull():
            return IngameVisualQAResult(
                status="FAIL_IMAGE_LOAD",
                compared_pixels=0,
                average_delta=999.0,
                max_delta=255,
                size_match=False,
                source_a=str(canary_path),
                source_b=str(agent_path),
            )
        width = min(canary.width(), agent.width())
        height = min(canary.height(), agent.height())
        size_match = canary.size() == agent.size()
        if width <= 0 or height <= 0:
            return IngameVisualQAResult(
                status="FAIL_EMPTY_IMAGE",
                compared_pixels=0,
                average_delta=999.0,
                max_delta=255,
                size_match=size_match,
                source_a=str(canary_path),
                source_b=str(agent_path),
            )

        total = 0
        max_delta = 0
        compared = width * height
        for y in range(height):
            for x in range(width):
                a = canary.pixelColor(x, y)
                b = agent.pixelColor(x, y)
                delta = (
                    abs(a.red() - b.red())
                    + abs(a.green() - b.green())
                    + abs(a.blue() - b.blue())
                ) // 3
                total += delta
                max_delta = max(max_delta, delta)
        average = total / compared
        status = "PASS" if size_match and average <= self.average_delta_threshold else "FAIL_VISUAL_DELTA"
        return IngameVisualQAResult(
            status=status,
            compared_pixels=compared,
            average_delta=average,
            max_delta=max_delta,
            size_match=size_match,
            source_a=str(canary_path),
            source_b=str(agent_path),
        )

    def audit(self) -> dict[str, Any]:
        return {
            "ingame_visual_qa_ready": True,
            "comparison_target": "Canary/RME screenshot vs agent viewport capture",
            "metrics": ["size_match", "average_rgb_delta", "max_rgb_delta"],
            "average_delta_threshold": self.average_delta_threshold,
        }
