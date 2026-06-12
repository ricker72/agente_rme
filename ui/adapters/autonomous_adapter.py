"""Core-backed autonomous design adapter."""

from __future__ import annotations

import json
import logging
import importlib
from pathlib import Path
from typing import Any, Callable

from ui.adapters._helpers import CORE_EXECUTION_FAILED, CORE_UNAVAILABLE, read_attr, safe_str
from ui.models.autonomous_dto import (
    AutonomousDesignRequestDTO,
    AutonomousIterationDTO,
    AutonomousMetricsDTO,
    AutonomousResultDTO,
)

logger = logging.getLogger(__name__)
AutonomousWorldDesigner: Any | None = None
_IMPORT_ERROR: BaseException | None = None


class AutonomousAdapter:
    """Bridge AutonomousService calls to the frozen autonomous designer."""

    def __init__(
        self,
        designer_factory: Callable[[], Any] | None = None,
        metrics_path: str = "output/autonomous/autonomous_metrics.json",
    ) -> None:
        self._designer_factory = designer_factory
        self._metrics_path = metrics_path
        self._iterations: list[AutonomousIterationDTO] = []

    def run_design(self, request: AutonomousDesignRequestDTO) -> AutonomousResultDTO:
        designer_class = self._load_designer_class()
        if _IMPORT_ERROR is not None or designer_class is None:
            return self._failure(request.world_id, CORE_UNAVAILABLE, _IMPORT_ERROR)
        try:
            designer = (self._designer_factory or designer_class)()
            result = designer.generate(request.goal, max_iterations=request.max_iterations or 1)
            success = bool(read_attr(result, "success", False))
            self._iterations = self._iterations_from_core(result)
            return AutonomousResultDTO(
                design_id=str(read_attr(result, "design_id", request.world_id)),
                world_id=request.world_id,
                success=success,
                summary="Design completed" if success else "Design failed",
                iterations=self._iterations,
            )
        except Exception as exc:
            logger.exception("Autonomous adapter design run failed: %s", exc)
            return self._failure(request.world_id, CORE_EXECUTION_FAILED, exc)

    def get_iterations(self) -> list[AutonomousIterationDTO]:
        return list(self._iterations)

    def get_metrics(self) -> AutonomousMetricsDTO:
        path = Path(self._metrics_path)
        if not path.is_file():
            return AutonomousMetricsDTO(status="Metrics unavailable", success=False)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AutonomousMetricsDTO(
                total_iterations=int(data.get("total_iterations", data.get("iterations", 0)) or 0),
                successful_runs=int(data.get("successful_runs", data.get("successful_worlds", 0)) or 0),
                failed_runs=int(data.get("failed_runs", 0) or 0),
                status="Loaded",
                success=True,
            )
        except Exception as exc:
            logger.exception("Autonomous adapter metrics load failed: %s", exc)
            return AutonomousMetricsDTO(status=CORE_EXECUTION_FAILED, success=False, error_message=safe_str(exc))

    def _iterations_from_core(self, result: Any) -> list[AutonomousIterationDTO]:
        data = list(read_attr(result, "iterations", read_attr(result, "convergence_data", [])) or [])
        return [
            AutonomousIterationDTO(
                iteration_id=str(index),
                iteration_number=index,
                status="completed",
                progress=1.0,
                summary=str(item),
            )
            for index, item in enumerate(data, start=1)
        ]

    @staticmethod
    def _failure(world_id: str, status: str, error: BaseException | None) -> AutonomousResultDTO:
        message = safe_str(error) if error is not None else status
        return AutonomousResultDTO(
            world_id=world_id,
            success=False,
            summary=status,
            iterations=[],
            design_id="",
            error_message=message,
        )

    @staticmethod
    def _load_designer_class() -> Any | None:
        global AutonomousWorldDesigner, _IMPORT_ERROR
        if AutonomousWorldDesigner is not None or _IMPORT_ERROR is not None:
            return AutonomousWorldDesigner
        try:
            module = importlib.import_module("core.autonomous.autonomous_world_designer")
            AutonomousWorldDesigner = getattr(module, "AutonomousWorldDesigner")
        except Exception as exc:  # pragma: no cover - import failure path
            _IMPORT_ERROR = exc
            AutonomousWorldDesigner = None
        return AutonomousWorldDesigner
