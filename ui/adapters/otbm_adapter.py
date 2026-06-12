"""Core-backed OTBM adapter."""

from __future__ import annotations

import logging
import importlib
from pathlib import Path
from typing import Any, Callable

from ui.adapters._helpers import CORE_EXECUTION_FAILED, CORE_UNAVAILABLE, safe_str
from ui.models.otbm_dto import (
    OTBMExportRequestDTO,
    OTBMExportResultDTO,
    OTBMImportResultDTO,
    OTBMValidationDTO,
)

logger = logging.getLogger(__name__)
OTBMExporter: Any | None = None
OTBMImporter: Any | None = None
OtbmValidator: Any | None = None
WorldModel: Any | None = None
_IMPORT_ERROR: BaseException | None = None


class OTBMAdapter:
    """Bridge OTBMService calls to frozen core OTBM components."""

    def __init__(
        self,
        importer_factory: Callable[[], Any] | None = None,
        exporter_factory: Callable[[], Any] | None = None,
        validator_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._importer_factory = importer_factory
        self._exporter_factory = exporter_factory
        self._validator_factory = validator_factory

    def import_otbm(self, path: str) -> OTBMImportResultDTO:
        importer_class = self._load_core_class("core.otbm.otbm_importer", "OTBMImporter")
        if _IMPORT_ERROR is not None or importer_class is None:
            return OTBMImportResultDTO(
                path=path,
                message=CORE_UNAVAILABLE,
                error_message=self._error_text(),
            )
        try:
            result = (self._importer_factory or importer_class)().import_file(path)
            success = bool(result.get("success", False))
            return OTBMImportResultDTO(
                path=path,
                world_id=Path(path).stem,
                world_name=Path(path).stem,
                success=success,
                message="Imported" if success else str(result.get("error", CORE_EXECUTION_FAILED)),
                error_message="" if success else str(result.get("error", CORE_EXECUTION_FAILED)),
            )
        except Exception as exc:
            logger.exception("OTBM adapter import failed: %s", exc)
            return OTBMImportResultDTO(path=path, message=CORE_EXECUTION_FAILED, error_message=safe_str(exc))

    def export_otbm(self, request: OTBMExportRequestDTO) -> OTBMExportResultDTO:
        exporter_class = self._load_core_class("core.otbm.otbm_exporter", "OTBMExporter")
        world_class = self._load_core_class("core.world.world_model", "WorldModel")
        if _IMPORT_ERROR is not None or exporter_class is None or world_class is None:
            return OTBMExportResultDTO(
                path=request.output_path,
                message=CORE_UNAVAILABLE,
                error_message=self._error_text(),
            )
        try:
            report = (self._exporter_factory or exporter_class)().export(
                world_class(),
                request.output_path,
            )
            success = str(report.get("status", "")) in {"success", "warning"}
            return OTBMExportResultDTO(
                path=request.output_path,
                tile_count=int(report.get("tiles", 0) or 0),
                success=success,
                message="Exported" if success else str(report.get("error", CORE_EXECUTION_FAILED)),
                error_message="" if success else str(report.get("error", CORE_EXECUTION_FAILED)),
            )
        except Exception as exc:
            logger.exception("OTBM adapter export failed: %s", exc)
            return OTBMExportResultDTO(
                path=request.output_path,
                message=CORE_EXECUTION_FAILED,
                error_message=safe_str(exc),
            )

    def validate_otbm(self, path: str) -> OTBMValidationDTO:
        validator_class = self._load_core_class("core.otbm.otbm_validator", "OtbmValidator")
        if _IMPORT_ERROR is not None or validator_class is None:
            return OTBMValidationDTO(
                path=path,
                message=CORE_UNAVAILABLE,
                error_message=self._error_text(),
            )
        try:
            data = Path(path).read_bytes()
            result = (self._validator_factory or validator_class)().validate(data)
            valid = bool(getattr(result, "is_valid", False))
            return OTBMValidationDTO(
                path=path,
                valid=valid,
                errors=list(getattr(result, "errors", []) or []),
                warnings=list(getattr(result, "warnings", []) or []),
                message="Valid" if valid else "Invalid",
                success=valid,
            )
        except Exception as exc:
            logger.exception("OTBM adapter validation failed: %s", exc)
            return OTBMValidationDTO(
                path=path,
                message=CORE_EXECUTION_FAILED,
                error_message=safe_str(exc),
            )

    @staticmethod
    def _load_core_class(module_name: str, class_name: str) -> Any | None:
        global _IMPORT_ERROR
        if _IMPORT_ERROR is not None:
            return None
        cached = globals().get(class_name)
        if cached is not None:
            return cached
        try:
            module = importlib.import_module(module_name)
            loaded = getattr(module, class_name)
            globals()[class_name] = loaded
            return loaded
        except Exception as exc:  # pragma: no cover - import failure path
            _IMPORT_ERROR = exc
            return None

    @staticmethod
    def _error_text() -> str:
        return safe_str(_IMPORT_ERROR) if _IMPORT_ERROR is not None else CORE_UNAVAILABLE
