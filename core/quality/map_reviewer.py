from __future__ import annotations

from typing import Any, Dict, List

from .pathing_analyzer import PathingAnalyzer
from .quality_score import QualityScore
from .spawn_analyzer import SpawnAnalyzer
from .visual_analyzer import VisualAnalyzer


class MapReviewer:
    def __init__(self, threshold: int = 80):
        self.pathing_analyzer = PathingAnalyzer()
        self.spawn_analyzer = SpawnAnalyzer()
        self.visual_analyzer = VisualAnalyzer()
        self.quality_score = QualityScore()
        self.threshold = threshold

    def review(self, world_model: Any) -> Dict[str, Any]:
        pathing_report = self.pathing_analyzer.analyze(world_model)
        spawn_report = self.spawn_analyzer.analyze(world_model)
        visual_report = self.visual_analyzer.analyze(world_model)
        progression_report = self._analyze_progression(world_model)

        category_scores = self.quality_score.evaluate(
            pathing_report=pathing_report,
            spawn_report=spawn_report,
            visual_report=visual_report,
            progression_report=progression_report,
            world_model=world_model,
        )

        review = {
            "score": category_scores["overall"],
            "categories": category_scores,
            "pathing": pathing_report,
            "spawn": spawn_report,
            "visual": visual_report,
            "progression": progression_report,
            "accessibility_issues": self._collect_accessibility_issues(pathing_report),
            "design_issues": self._collect_design_issues(visual_report),
            "navigation_issues": self._collect_navigation_issues(pathing_report),
            "progression_issues": self._collect_progression_issues(progression_report),
            "density_issues": self._collect_density_issues(spawn_report, visual_report),
            "should_export": category_scores["overall"] >= self.threshold,
        }
        return review

    def improve(self, world_model: Any) -> Dict[str, Any]:
        review = self.review(world_model)
        if review["score"] >= self.threshold:
            return review

        self._fix_pathing(world_model, review)
        self._fix_spawns(world_model, review)
        self._fix_visual(world_model, review)

        improved_review = self.review(world_model)
        return improved_review

    def _analyze_progression(self, world_model: Any) -> Dict[str, Any]:
        quests = getattr(world_model, "quests", []) or []
        bosses = getattr(world_model, "bosses", []) or []
        progression = {
            "quests": len(quests),
            "bosses": len(bosses),
            "tier_count": (
                len({quest.get("tier") for quest in quests if quest.get("tier")})
                if quests
                else 0
            ),
            "recommended_quests": 3,
            "recommended_bosses": 2,
        }
        return progression

    def _collect_accessibility_issues(
        self, pathing_report: Dict[str, Any]
    ) -> List[str]:
        issues = []
        if pathing_report["dead_ends"]:
            issues.append(f"Dead ends detected: {len(pathing_report['dead_ends'])}")
        if pathing_report["soft_locks"]:
            issues.append(f"Potential soft locks: {len(pathing_report['soft_locks'])}")
        if pathing_report["hard_locks"]:
            issues.append(f"Hard locks found: {len(pathing_report['hard_locks'])}")
        if pathing_report["unreachable_zones"]:
            issues.append(
                f"Unreachable zones: {len(pathing_report['unreachable_zones'])}"
            )
        return issues

    def _collect_design_issues(self, visual_report: Dict[str, Any]) -> List[str]:
        issues = []
        if visual_report["tile_spam"]:
            issues.append("Excessive tile spam detected.")
        if visual_report["wall_spam"]:
            issues.append("Too many wall tiles or wall decorations.")
        if visual_report["empty_spaces"]:
            issues.append("Large empty areas reduce visual quality.")
        if visual_report["overdecorated_zones"]:
            issues.append("Some zones are overdecorated and noisy.")
        return issues

    def _collect_navigation_issues(self, pathing_report: Dict[str, Any]) -> List[str]:
        return [issue for issue in pathing_report.get("warnings", [])]

    def _collect_progression_issues(
        self, progression_report: Dict[str, Any]
    ) -> List[str]:
        issues = []
        if progression_report["quests"] < progression_report["recommended_quests"]:
            issues.append("Insufficient quest count for a satisfying progression loop.")
        if progression_report["bosses"] < progression_report["recommended_bosses"]:
            issues.append("Not enough boss encounters to anchor progression.")
        return issues

    def _collect_density_issues(
        self, spawn_report: Dict[str, Any], visual_report: Dict[str, Any]
    ) -> List[str]:
        issues = []
        if spawn_report["density_trend"] != "balanced":
            issues.append("Monster density is not balanced.")
        if visual_report["empty_spaces"]:
            issues.append("Visual density is uneven, leaving dead floor space.")
        return issues

    def _fix_pathing(self, world_model: Any, review: Dict[str, Any]) -> None:
        unreachable = review["pathing"]["unreachable_zones"]
        tiles = getattr(world_model, "tiles", {})
        if unreachable and tiles:
            reachable_tiles = [
                coords
                for coords in self.pathing_analyzer._find_reachable_tiles(world_model)
            ]
            if reachable_tiles:
                target = reachable_tiles[0]
                for zone in unreachable[:1]:
                    self._connect_zone(world_model, zone, target)

    def _connect_zone(
        self,
        world_model: Any,
        zone_coords: Dict[str, int],
        target: tuple[int, int, int],
    ) -> None:
        x1, y1, z1 = zone_coords["x"], zone_coords["y"], zone_coords["z"]
        x2, y2, z2 = target
        step_x = 1 if x2 > x1 else -1 if x2 < x1 else 0
        step_y = 1 if y2 > y1 else -1 if y2 < y1 else 0
        current_x, current_y = x1, y1
        while (current_x, current_y) != (x2, y2):
            if current_x != x2:
                current_x += step_x
            elif current_y != y2:
                current_y += step_y
            tile = getattr(world_model, "tiles", {}).get(
                f"{current_x}:{current_y}:{z1}"
            )
            if tile is None:
                (
                    type(next(iter(world_model.tiles.values())))
                    if world_model.tiles
                    else None
                )
                if hasattr(world_model, "add_tile"):
                    from core.world_engine.world_engine import Tile

                    world_model.add_tile(
                        Tile(x=current_x, y=current_y, z=z1, ground="floor")
                    )

    def _fix_spawns(self, world_model: Any, review: Dict[str, Any]) -> None:
        if review["spawn"]["density_trend"] == "high":
            all_spawns = getattr(world_model, "spawns", [])
            for spawn in all_spawns[: len(all_spawns) // 3]:
                if getattr(world_model, "spawns", None) is not None:
                    all_spawns.remove(spawn)

    def _fix_visual(self, world_model: Any, review: Dict[str, Any]) -> None:
        for tile in getattr(world_model, "tiles", {}).values():
            if len(tile.decorations) > 3:
                tile.decorations = tile.decorations[:3]
            if len(tile.items) > 4:
                tile.items = tile.items[:4]
