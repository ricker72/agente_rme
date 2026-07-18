"""
OTBMExporter — fachada principal para exportar WorldModel → .otbm.

API:
    exporter = OTBMExporter()
    exporter.export(world, "map.otbm")

Pipeline:
    WorldModel
    ↓
    OTBMExporter
    ↓
    Validator
    ↓
    Serializer → Writer
    ↓
    map.otbm
    + monster.xml (opcional)
    + houses.xml (opcional)
    + waypoints.xml (opcional)

Export Report:
    {
        "tiles": 12500,
        "items": 2200,
        "spawns": 340,
        "houses": 12,
        "waypoints": 8,
        "status": "success"
    }
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

from core.rules.rule33c_enforcer import enforce_rule33c_otbm_export
from .otbm_writer import WorldModelToOTBM
from .otbm_serializer import OtbmSerializer
from .otbm_validator import OtbmValidator, OtbmValidationResult
from .item_encoder import ItemEncoder
from .spawn_encoder import SpawnEncoder
from .house_encoder import HouseEncoder
from .waypoint_encoder import WaypointEncoder

logger = logging.getLogger(__name__)


class OTBMExporter:
    """
    Exporta un WorldModel a archivo .otbm compatible con OpenTibiaBR RME.

    Uso:
        exporter = OTBMExporter()
        report = exporter.export(world, "output/map.otbm")
        print(report["status"])  # "success" | "error"

    También genera archivos auxiliares (monster.xml, houses.xml, waypoints.xml)
    y un reporte JSON con estadísticas.
    """

    def __init__(self, generate_templates: bool = True):
        """
        Args:
            generate_templates: Generar XMLs auxiliares (monster, houses, waypoints).
        """
        self._converter = WorldModelToOTBM()
        self._serializer = OtbmSerializer()
        self._validator = OtbmValidator()
        self._item_encoder = ItemEncoder()
        self._spawn_encoder = SpawnEncoder()
        self._house_encoder = HouseEncoder()
        self._waypoint_encoder = WaypointEncoder()
        self._generate_templates = generate_templates

    # ------------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------------

    def export(
        self,
        world_model: Any,
        output_path: str,
        generate_report: bool = False,
    ) -> Dict[str, Any]:
        """
        Exporta WorldModel → .otbm + XMLs auxiliares.

        Args:
            world_model: WorldModel instance.
            output_path: Ruta para el archivo .otbm (ej: "output/map.otbm").
            generate_report: Si True, también genera report.json.

        Returns:
            Dict con estadísticas de exportación.
        """
        # RULE-33-C: Enforce Semantic Design Before Materialization
        enforce_rule33c_otbm_export()
        logger.info("RULE-33-C gate passed: OTBM export permitted.")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        start_count = {
            "tiles": len(getattr(world_model, "tiles", {})),
            "items": self._count_items(world_model),
            "spawns": self._count_spawns(world_model),
            "houses": len(self._house_encoder.extract_houses(world_model)),
            "waypoints": len(self._waypoint_encoder.extract_waypoints(world_model)),
        }

        # 1. Convertir WorldModel a OTBM binario
        try:
            otbm_bytes = self._converter.convert(world_model)
        except ValueError as e:
            return {
                "status": "error",
                "error": str(e),
                **start_count,
            }

        # 2. Validar binario OTBM con RME Compatibility Validator
        validation = self._validator.validate(otbm_bytes)

        # 4. Combinar resultados de validación
        # 3. Escribir .otbm
        path.write_bytes(otbm_bytes)

        # 4. Generar templates XML (opcional)
        templates: Dict[str, Path] = {}
        if self._generate_templates:
            templates = self._write_templates(world_model, path)

        # 5. Reporte de exportación
        report: Dict[str, Any] = {
            "tiles": start_count["tiles"],
            "items": start_count["items"],
            "spawns": start_count["spawns"],
            "houses": start_count["houses"],
            "waypoints": start_count["waypoints"],
            "otbm_bytes": len(otbm_bytes),
            "validation": {
                "passed": validation.is_valid,
                "errors": validation.errors[:10],
                "warnings": validation.warnings[:10],
            },
            "status": "success" if validation.is_valid else "warning",
            "files": {
                "otbm": str(path),
                **{k: str(v) for k, v in templates.items()},
            },
        }

        # 6. Generar report.json si se solicita
        if generate_report:
            report_path = path.with_suffix(".report.json")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            report["files"]["report"] = str(report_path)

        # Mostrar resumen en consola
        status_text = "OK" if validation.is_valid else "WARN"
        print(
            f"  [OTBM] [{status_text}] {path.name}: "
            f"{report['tiles']} tiles, {report['items']} items, "
            f"{report['spawns']} spawns | "
            f"{report['otbm_bytes']} bytes"
        )

        return report

    def export_bytes(self, world_model: Any) -> bytes:
        """
        Exporta WorldModel a bytes OTBM sin escribir a disco.

        Args:
            world_model: WorldModel instance.

        Returns:
            bytes: Datos OTBM binarios.
        """
        return self._converter.convert(world_model)

    # ------------------------------------------------------------------
    # Validación
    # ------------------------------------------------------------------

    def validate(self, otbm_bytes: bytes) -> OtbmValidationResult:
        """
        Valida datos OTBM binarios.

        Args:
            otbm_bytes: Datos OTBM.

        Returns:
            OtbmValidationResult con estado y estadísticas.
        """
        return self._validator.validate(otbm_bytes)

    # ------------------------------------------------------------------
    # Generación de XMLs auxiliares
    # ------------------------------------------------------------------

    def generate_monster_xml(self, world_model: Any) -> str:
        """Genera XML de monstruos."""
        return self._spawn_encoder.generate_monster_xml(world_model)

    def generate_house_xml(self, world_model: Any) -> str:
        """Genera XML de houses."""
        return self._house_encoder.generate_house_xml(world_model)

    def generate_waypoint_xml(self, world_model: Any) -> str:
        """Genera XML de waypoints."""
        return self._waypoint_encoder.generate_waypoint_xml(world_model)

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _write_templates(self, world_model: Any, otbm_path: Path) -> Dict[str, Path]:
        """Escribe archivos XML auxiliares junto al .otbm."""
        base = otbm_path.parent / otbm_path.stem
        templates = {}

        monster_xml = self._spawn_encoder.generate_monster_xml(world_model)
        if monster_xml:
            mp = base.with_suffix(".monster.xml")
            mp.write_text(monster_xml, encoding="utf-8")
            templates["monster_xml"] = mp

        house_xml = self._house_encoder.generate_house_xml(world_model)
        if house_xml:
            hp = base.with_suffix(".houses.xml")
            hp.write_text(house_xml, encoding="utf-8")
            templates["houses_xml"] = hp

        waypoint_xml = self._waypoint_encoder.generate_waypoint_xml(world_model)
        if waypoint_xml:
            wp = base.with_suffix(".waypoints.xml")
            wp.write_text(waypoint_xml, encoding="utf-8")
            templates["waypoints_xml"] = wp

        return templates

    @staticmethod
    def _count_items(world_model: Any) -> int:
        """Cuenta items totales en tiles del WorldModel."""
        count = 0
        for tile in getattr(world_model, "tiles", {}).values():
            items = getattr(tile, "items", [])
            count += len(items)
            # El ground cuenta como 1 item
            if getattr(tile, "ground", None) is not None:
                count += 1
        return count

    @staticmethod
    def _count_spawns(world_model: Any) -> int:
        """Cuenta spawns totales en tiles del WorldModel."""
        count = 0
        for tile in getattr(world_model, "tiles", {}).values():
            if getattr(tile, "spawn", None) is not None:
                count += 1
        # Spawns a nivel de world_model
        count += len(getattr(world_model, "spawns", []) or [])
        return count
