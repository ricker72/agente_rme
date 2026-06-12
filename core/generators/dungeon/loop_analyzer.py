from typing import List


class LoopAnalyzer:
    def __init__(self, corridors: List[List[tuple[int, int]]]):
        self.corridors = corridors

    def has_valid_loop(self) -> bool:
        return len(self.corridors) >= 2 and all(
            len(path) > 0 for path in self.corridors
        )

    def analyze(self) -> dict:
        return {
            "has_loop": self.has_valid_loop(),
            "corridor_count": len(self.corridors),
        }
