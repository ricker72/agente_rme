from __future__ import annotations

import copy
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

from core.otbm.lossless_document import LosslessOTBMDocument
from core.otbm.otbm_writer import OtbmWriter
from core.otbm.transaction_writer import LosslessOTBMTransactionWriter, TileStackPatch


class CertifiedOTBMService:
    """Route Workspace exports through the certified OTBM writers."""

    def export(
        self,
        world_model: Any,
        destination: str | Path,
        *,
        source_path: str | Path | None = None,
        patches: Iterable[TileStackPatch | Mapping[str, Any]] = (),
        quality_validator: Callable[[Any], Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source_path is not None:
            return self._export_lossless(Path(source_path), target, patches)
        return self._export_new(world_model, target, quality_validator, metadata)

    @staticmethod
    def _export_lossless(
        source: Path,
        target: Path,
        patches: Iterable[TileStackPatch | Mapping[str, Any]],
    ) -> dict[str, Any]:
        normalized = tuple(CertifiedOTBMService._tile_patch(value) for value in patches)
        if normalized:
            report = LosslessOTBMTransactionWriter(source).write(target, normalized)
            return {
                "mode": "lossless_copy_on_write",
                "patch_count": report.patch_count,
                "replaced_tiles": report.replaced_tiles,
                "inserted_tiles": report.inserted_tiles,
                "validated_tiles": report.validated_tiles,
                "output_size": report.output_size,
                "audit_status": report.audit_status,
            }

        if source.resolve() == target.resolve():
            audit = LosslessOTBMDocument(source).audit_full_file()
            if audit.status != "PASS":
                raise ValueError(f"Source OTBM audit failed: {audit.diagnostics[:5]}")
        else:
            identity = LosslessOTBMDocument(source).write_unchanged(target)
            if identity.status != "PASS":
                raise ValueError("Unchanged OTBM copy failed byte-identity validation")
        return {
            "mode": "lossless_unchanged",
            "patch_count": 0,
            "output_size": target.stat().st_size,
            "audit_status": "PASS",
        }

    @staticmethod
    def _export_new(
        world_model: Any,
        target: Path,
        quality_validator: Callable[[Any], Any] | None,
        metadata: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        export_model = CertifiedOTBMService._with_supported_metadata(world_model, metadata)
        if quality_validator is not None:
            quality_validator(export_model)

        handle = tempfile.NamedTemporaryFile(
            prefix=f".{target.name}.", suffix=".tmp", dir=target.parent, delete=False
        )
        temporary = Path(handle.name)
        handle.close()
        try:
            OtbmWriter().write(export_model, temporary, generate_templates=False)
            audit = LosslessOTBMDocument(temporary).audit_full_file()
            if audit.status != "PASS":
                raise ValueError(f"Generated OTBM audit failed: {audit.diagnostics[:5]}")
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink()
        return {
            "mode": "validated_new_map",
            "patch_count": 0,
            "output_size": target.stat().st_size,
            "audit_status": "PASS",
        }

    @staticmethod
    def _tile_patch(value: TileStackPatch | Mapping[str, Any]) -> TileStackPatch:
        if isinstance(value, TileStackPatch):
            return value
        return TileStackPatch(
            x=int(value["x"]),
            y=int(value["y"]),
            z=int(value["z"]),
            ground_id=(int(value["ground_id"]) if value.get("ground_id") is not None else None),
            items=tuple(value.get("items", ()) or ()),
            flags=int(value.get("flags", 0) or 0),
            house_id=(int(value["house_id"]) if value.get("house_id") is not None else None),
        )

    @staticmethod
    def _with_supported_metadata(
        world_model: Any,
        metadata: Mapping[str, Any] | None,
    ) -> Any:
        if not metadata:
            return world_model
        export_model = copy.copy(world_model)
        supported = {
            "towns": "cities",
            "spawns": "spawns",
            "waypoints": "waypoints",
        }
        for source_name, model_name in supported.items():
            if source_name in metadata:
                setattr(export_model, model_name, copy.deepcopy(list(metadata[source_name] or ())))
        return export_model
