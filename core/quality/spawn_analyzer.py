from __future__ import annotations

from typing import Any, Dict, List

from .balance_analyzer import BalanceAnalyzer


class SpawnAnalyzer:
    def __init__(self):
        self.balance_analyzer = BalanceAnalyzer()

    def analyze(self, world_model: Any) -> Dict[str, object]:
        spawns = getattr(world_model, "spawns", []) or []
        tiles = getattr(world_model, "tiles", {})
        spawn_tiles = [spawn for spawn in spawns if spawn.get("monster")]
        density = len(spawn_tiles) / max(len(tiles), 1)

        [
            spawn.get("respawn_time", 0)
            for spawn in spawn_tiles
            if isinstance(spawn.get("respawn_time"), (int, float))
        ]
        rerolls = [
            spawn for spawn in spawn_tiles if spawn.get("respawn_time") in (0, None)
        ]

        difficulties = []
        for entry in spawn_tiles:
            difficulty = entry.get("difficulty")
            if isinstance(difficulty, (int, float)):
                difficulties.append(float(difficulty))
            elif isinstance(difficulty, str) and difficulty.isdigit():
                difficulties.append(float(difficulty))

        difficulty_spike = self._detect_difficulty_spike(difficulties)
        balance = self.balance_analyzer.analyze(world_model)

        density_trend = "balanced"
        if density > 0.18:
            density_trend = "high"
        elif density < 0.03:
            density_trend = "low"

        return {
            "spawn_count": len(spawn_tiles),
            "density": round(density, 3),
            "density_trend": density_trend,
            "respawn_balance": (
                "unbalanced" if len(rerolls) > len(spawn_tiles) * 0.3 else "balanced"
            ),
            "difficulty_spikes": difficulty_spike,
            "balance": balance,
        }

    def _detect_difficulty_spike(self, difficulties: List[float]) -> bool:
        if len(difficulties) < 2:
            return False
        difficulties_sorted = sorted(difficulties)
        for first, second in zip(difficulties_sorted, difficulties_sorted[1:]):
            if second - first > 2.5:
                return True
        return False
