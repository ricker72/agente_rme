from __future__ import annotations

from typing import Tuple, Union


class DifficultyPlanner:
    LEVEL_BANDS = [
        (1, 50, "easy"),
        (50, 100, "medium"),
        (100, 200, "hard"),
        (200, 300, "extreme"),
        (300, 500, "epic"),
        (500, 9999, "legendary"),
    ]

    def plan(self, level_range: Union[Tuple[int, int], None]) -> str:
        if not level_range:
            return "medium"
        low, high = level_range
        for minimum, maximum, label in self.LEVEL_BANDS:
            if low >= minimum and high <= maximum:
                return label
        if high >= 500:
            return "legendary"
        return "hard"
