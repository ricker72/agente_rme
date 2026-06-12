"""Core-backed critic adapter."""

from __future__ import annotations

import logging
import importlib
from typing import Any, Callable

from ui.adapters._helpers import CORE_EXECUTION_FAILED, CORE_UNAVAILABLE, read_attr, safe_str
from ui.models.critic_dto import CriticDTO, CriticIssueDTO, CriticRequestDTO, HeatmapDTO

logger = logging.getLogger(__name__)
CriticEngine: Any | None = None
_IMPORT_ERROR: BaseException | None = None


class CriticAdapter:
    """Bridge CriticService calls to the frozen core critic engine."""

    def __init__(self, engine_factory: Callable[[], Any] | None = None) -> None:
        self._engine_factory = engine_factory
        self._last_report: CriticDTO = CriticDTO(summary="No report", success=False)
        self._heatmaps: list[HeatmapDTO] = []

    def analyze_world(self, request: CriticRequestDTO) -> CriticDTO:
        engine_class = self._load_engine_class()
        if _IMPORT_ERROR is not None or engine_class is None:
            return self._failure(CORE_UNAVAILABLE, _IMPORT_ERROR)
        try:
            engine = (self._engine_factory or engine_class)()
            result = engine.analyze_dict({"tiles": []}, map_name=request.world_id)
            self._last_report = self._from_core(result, request)
            return self._last_report
        except Exception as exc:
            logger.exception("Critic adapter failed to analyze world: %s", exc)
            self._last_report = self._failure(CORE_EXECUTION_FAILED, exc)
            return self._last_report

    def get_last_report(self) -> CriticDTO:
        return self._last_report

    def get_heatmaps(self) -> list[HeatmapDTO]:
        return list(self._heatmaps)

    def _from_core(self, result: Any, request: CriticRequestDTO) -> CriticDTO:
        issues = [
            CriticIssueDTO(
                code=str(read_attr(issue, "issue_type", "")),
                message=str(read_attr(issue, "message", "")),
                severity=str(read_attr(issue, "severity", "info")),
            )
            for issue in list(read_attr(result, "issues", []) or [])
        ]
        recommendations = list(read_attr(result, "recommendations", []) or [])
        suggestions = [
            str(read_attr(item, "title", read_attr(item, "message", item)))
            for item in recommendations
        ]
        score_obj = read_attr(result, "overall_score", 0.0)
        score = float(read_attr(score_obj, "value", score_obj) or 0.0)
        return CriticDTO(
            analysis_id=request.world_id,
            score=score,
            issues=issues,
            suggestions=suggestions,
            summary="Analysis completed",
            success=True,
        )

    @staticmethod
    def _failure(status: str, error: BaseException | None) -> CriticDTO:
        message = safe_str(error) if error is not None else status
        return CriticDTO(summary=status, success=False, error_message=message)

    @staticmethod
    def _load_engine_class() -> Any | None:
        global CriticEngine, _IMPORT_ERROR
        if CriticEngine is not None or _IMPORT_ERROR is not None:
            return CriticEngine
        try:
            module = importlib.import_module("core.critic.critic_engine")
            CriticEngine = getattr(module, "CriticEngine")
        except Exception as exc:  # pragma: no cover - import failure path
            _IMPORT_ERROR = exc
            CriticEngine = None
        return CriticEngine
