from __future__ import annotations

from pathlib import Path
from typing import Any

from .otbm_serializer import OtbmSerializer
from .otbm_validator import OtbmValidator
from .otbm_templates import OtbmTemplateGenerator


class WorldModelToOTBM:
    """
    Converts a WorldModel directly to OTBM binary format.

    This is the primary entry point for the OTBM export pipeline:
        WorldModel -> WorldModelToOTBM.convert() -> bytes -> file.otbm

    Usage:
        converter = WorldModelToOTBM()
        otbm_bytes = converter.convert(world_model)
        converter.save(world_model, "output/map.otbm")
    """

    def __init__(self):
        self.serializer = OtbmSerializer()
        self.validator = OtbmValidator()
        self.templates = OtbmTemplateGenerator()

    def convert(self, world_model: Any) -> bytes:
        """
        Convert a WorldModel to OTBM binary bytes.

        Args:
            world_model: WorldModel dataclass instance.

        Returns:
            bytes: Valid OTBM binary data.
        """
        # Pre-serialization validation
        pre_report = self.validator.validate_world_model(world_model)
        if pre_report.status == "failure":
            raise ValueError(f"WorldModel validation failed: {pre_report.errors}")

        return self.serializer.serialize(world_model)

    def save(
        self,
        world_model: Any,
        destination: str | Path,
        generate_templates: bool = True,
    ) -> Path:
        """
        Convert and save a WorldModel as .otbm file.

        Args:
            world_model: WorldModel instance.
            destination: Output file path (.otbm).
            generate_templates: If True, also write house/monster/npc/zone XML files.

        Returns:
            Path to the written .otbm file.
        """
        path = Path(destination)
        content = self.convert(world_model)

        # Post-serialization validation
        post_report = self.validator.validate(content)
        if post_report.status == "failure":
            raise ValueError(f"OTBM binary validation failed: {post_report.errors}")
        if post_report.warnings:
            import warnings

            for w in post_report.warnings:
                warnings.warn(f"OTBM: {w}")

        path.write_bytes(content)

        if generate_templates:
            self.templates.write_all(world_model, path)

        return path


class OtbmWriter:
    """
    Writes OTBM binary data to disk.

    Uses the real OTBM binary format via OtbmSerializer and
    performs validation before writing.

    For new code, prefer WorldModelToOTBM which provides a cleaner API.
    """

    def __init__(self):
        self.serializer = OtbmSerializer()
        self.validator = OtbmValidator()
        self.templates = OtbmTemplateGenerator()

    def write(
        self,
        world_model: Any,
        destination: str | Path,
        generate_templates: bool = False,
    ) -> Path:
        """
        Serialize a WorldModel and write to .otbm file.

        Args:
            world_model: WorldModel dataclass instance.
            destination: Output path for the .otbm file.
            generate_templates: Also write companion XML files.

        Returns:
            Path to the written file.
        """
        converter = WorldModelToOTBM()
        return converter.save(world_model, destination, generate_templates)

    def write_templates(self, world_model: Any, destination_dir: str | Path) -> None:
        """Write house/monster/npc/zone XML files only."""
        self.templates.write_all_files(world_model, destination_dir)
