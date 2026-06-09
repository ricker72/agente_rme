from __future__ import annotations

from typing import Any, Dict


class QualityScore:
    def evaluate(
        self,
        pathing_report: Dict[str, Any],
        spawn_report: Dict[str, Any],
        visual_report: Dict[str, Any],
        progression_report: Dict[str, Any],
        world_model: Any,
    ) -> Dict[str, int]:
        navigation = self._score_navigation(pathing_report)
        gameplay = self._score_gameplay(spawn_report)
        visual = self._score_visual(visual_report)
        progression = self._score_progression(progression_report)
        performance = self._score_performance(world_model)

        overall = round(
            navigation * 0.22
            + gameplay * 0.3
            + visual * 0.2
            + progression * 0.18
            + performance * 0.1
        )

        return {
            "overall": max(0, min(100, overall)),
            "Gameplay": max(0, min(100, gameplay)),
            "Visual": max(0, min(100, visual)),
            "Navigation": max(0, min(100, navigation)),
            "Progression": max(0, min(100, progression)),
            "Performance": max(0, min(100, performance)),
        }

    def _score_navigation(self, pathing_report: Dict[str, Any]) -> int:
        score = 100
        score -= min(len(pathing_report.get("dead_ends", [])) * 3, 18)
        score -= min(len(pathing_report.get("soft_locks", [])) * 6, 24)
        score -= min(len(pathing_report.get("hard_locks", [])) * 12, 36)
        score -= min(len(pathing_report.get("unreachable_zones", [])) * 8, 24)
        return max(10, score)

    def _score_gameplay(self, spawn_report: Dict[str, Any]) -> int:
        score = 100
        if spawn_report.get("density_trend") == "high":
            score -= 20
        elif spawn_report.get("density_trend") == "low":
            score -= 18
        if spawn_report.get("respawn_balance") == "unbalanced":
            score -= 12
        if spawn_report.get("difficulty_spikes"):
            score -= 16
        if spawn_report.get("balance", {}).get("monster_balance") == "poor":
            score -= 14
        return max(10, score)

    def _score_visual(self, visual_report: Dict[str, Any]) -> int:
        score = 100
        if visual_report.get("tile_spam"):
            score -= 20
        if visual_report.get("wall_spam"):
            score -= 18
        if visual_report.get("empty_spaces"):
            score -= 16
        if visual_report.get("overdecorated_zones"):
            score -= min(len(visual_report.get("overdecorated_zones", [])) * 3, 24)
        return max(10, score)

    def _score_progression(self, progression_report: Dict[str, Any]) -> int:
        score = 100
        if progression_report.get("quests", 0) < progression_report.get("recommended_quests", 3):
            score -= 18
        if progression_report.get("bosses", 0) < progression_report.get("recommended_bosses", 2):
            score -= 20
        if progression_report.get("tier_count", 0) < 2:
            score -= 10
        return max(10, score)

    def _score_performance(self, world_model: Any) -> int:
        tile_count = len(getattr(world_model, "tiles", {}))
        if tile_count > 7000:
            return 72
        if tile_count > 4500:
            return 82
        if tile_count > 2500:
            return 90
        return 96
