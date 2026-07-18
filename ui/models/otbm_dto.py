"""OTBM service DTOs."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class OTBMImportResultDTO:
    """Result of an OTBM import request."""

    path: str = ""
    world_id: str = ""
    world_name: str = ""
    success: bool = False
    message: str = "Service not connected"
    error_message: str = ""


@dataclass(slots=True)
class OTBMExportRequestDTO:
    """Input data for a future OTBM export adapter."""

    world_id: str = ""
    output_path: str = ""
    include_metadata: bool = True


@dataclass(slots=True)
class OTBMExportResultDTO:
    """Result of an OTBM export request."""

    path: str = ""
    tile_count: int = 0
    success: bool = False
    message: str = "Service not connected"
    error_message: str = ""


@dataclass(slots=True)
class OTBMValidationDTO:
    """OTBM validation result."""

    path: str = ""
    valid: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    message: str = "Service not connected"
    success: bool = False
    error_message: str = ""


OTBMExportDTO = OTBMExportResultDTO
OTBMImportDTO = OTBMImportResultDTO
