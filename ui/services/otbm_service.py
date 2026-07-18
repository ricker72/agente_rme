"""OTBM service contract."""

from __future__ import annotations

from typing import Protocol

from ui.models.otbm_dto import (
    OTBMExportRequestDTO,
    OTBMExportResultDTO,
    OTBMImportResultDTO,
    OTBMValidationDTO,
)


class OTBMService(Protocol):
    """Contract between UI pages and future OTBM adapters."""

    def import_otbm(self, path: str) -> OTBMImportResultDTO:
        """Import an OTBM file."""
        ...

    def export_otbm(self, request: OTBMExportRequestDTO) -> OTBMExportResultDTO:
        """Export a world to OTBM."""
        ...

    def validate_otbm(self, path: str) -> OTBMValidationDTO:
        """Validate an OTBM file path."""
        ...
