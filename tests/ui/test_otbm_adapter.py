"""Tests for OTBMAdapter."""

from __future__ import annotations

from pathlib import Path

from pytest import MonkeyPatch

from ui.adapters import otbm_adapter
from ui.adapters.otbm_adapter import OTBMAdapter
from ui.models.otbm_dto import (
    OTBMExportRequestDTO,
    OTBMExportResultDTO,
    OTBMImportResultDTO,
    OTBMValidationDTO,
)


class FakeImporter:
    def import_file(self, path: str) -> dict[str, object]:
        return {"success": True, "map_info": {}, "stats": {}}


class FakeExporter:
    def export(self, world_model: object, output_path: str) -> dict[str, object]:
        return {"status": "success", "tiles": 3}


class FakeValidation:
    is_valid = True
    errors: list[str] = []
    warnings: list[str] = []


class FakeValidator:
    def validate(self, data: bytes) -> FakeValidation:
        return FakeValidation()


def test_otbm_adapter_returns_dtos(tmp_path: Path) -> None:
    source = tmp_path / "in.otbm"
    source.write_bytes(b"OTBM")
    adapter = OTBMAdapter(
        importer_factory=FakeImporter,
        exporter_factory=FakeExporter,
        validator_factory=FakeValidator,
    )
    assert isinstance(adapter.import_otbm(str(source)), OTBMImportResultDTO)
    export = adapter.export_otbm(OTBMExportRequestDTO(output_path=str(tmp_path / "out.otbm")))
    assert isinstance(export, OTBMExportResultDTO)
    assert export.success is True
    assert isinstance(adapter.validate_otbm(str(source)), OTBMValidationDTO)


def test_otbm_adapter_failure_returns_safe_dto(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(otbm_adapter, "_IMPORT_ERROR", ImportError("otbm missing"))
    monkeypatch.setattr(otbm_adapter, "OTBMImporter", None)
    dto = OTBMAdapter().import_otbm("missing.otbm")
    assert dto.message == "Core unavailable"
    assert dto.success is False
