"""
Tests for OTBM export validation and roundtrip pipeline.

Validates the full pipeline:
  generated.otbm
  ↓
  OTBMImporter
  ↓
  WorldModel
  ↓
  OTBMExporter
  ↓
  generated_roundtrip.otbm
"""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.otbm.otbm_serializer import OtbmSerializer
from core.otbm.otbm_importer import OTBMImporter
from core.otbm.otbm_exporter import OTBMExporter
from core.world.world_model import WorldModel
from core.world.tile import Tile


def _make_tile(x, y, z, ground=106, items=None, flags=0):
    return Tile(x=x, y=y, z=z, ground=ground, items=items or [])


class TestOTBMRoundtripPipeline:
    """Verify the full export → import → re-export pipeline."""

    def test_roundtrip_basic(self, tmp_path):
        # Build world
        world = WorldModel()
        for i in range(5):
            for j in range(5):
                world.set_tile(_make_tile(i, j, 7, ground=106))
        # Add spawns
        world.spawns = [
            {"x": 2, "y": 2, "z": 7, "monster": "Dragon", "interval": 60, "radius": 3},
            {"x": 3, "y": 3, "z": 7, "monster": "Demon", "interval": 60, "radius": 3},
        ]
        # Add city
        world.cities = [{"name": "TestCity", "temple_x": 0, "temple_y": 0, "temple_z": 7}]
        # Add waypoint
        world.waypoints = [{"name": "Spawn", "x": 0, "y": 0, "z": 7}]

        # Export
        out1 = tmp_path / "generated.otbm"
        ser = OtbmSerializer()
        data = ser.serialize(world)
        out1.write_bytes(data)
        assert out1.exists()
        assert out1.read_bytes()[:4] == b"OTBM"

        # Import
        importer = OTBMImporter()
        result = importer.import_bytes(data)
        assert result["success"], f"Import failed: {result.get('error')}"
        assert result["stats"]["tiles"] > 0
        wm = result["world_model"]

        # Re-export
        out2 = tmp_path / "generated_roundtrip.otbm"
        data2 = ser.serialize(wm)
        out2.write_bytes(data2)
        assert out2.exists()
        assert out2.read_bytes()[:4] == b"OTBM"
        # Re-exported data should be parseable again
        result2 = importer.import_bytes(data2)
        assert result2["success"], f"Re-import failed: {result2.get('error')}"

    def test_roundtrip_through_exporter(self, tmp_path):
        """Verify OTBMExporter class works end-to-end."""
        world = WorldModel()
        for i in range(3):
            for j in range(3):
                world.set_tile(_make_tile(i, j, 7, ground=110))

        exporter = OTBMExporter(generate_templates=False)
        report = exporter.export(world, str(tmp_path / "via_exporter.otbm"))
        assert report["status"] in ("success", "warning")
        assert (tmp_path / "via_exporter.otbm").exists()

        # Import
        importer = OTBMImporter()
        result = importer.import_file(str(tmp_path / "via_exporter.otbm"))
        assert result["success"]

        # Re-export
        report2 = exporter.export(result["world_model"], str(tmp_path / "via_exporter2.otbm"))
        assert report2["status"] in ("success", "warning")

    def test_roundtrip_with_extreme_ids(self, tmp_path):
        """Roundtrip should not raise even with extreme IDs (regression for the byte range bug)."""
        world = WorldModel()
        for i, gid in enumerate([1, 50000, 99999, 9999999]):
            world.set_tile(_make_tile(i, 0, 7, ground=gid))

        ser = OtbmSerializer()
        data = ser.serialize(world)
        importer = OTBMImporter()
        result = importer.import_bytes(data)
        assert result["success"]

        data2 = ser.serialize(result["world_model"])
        assert data2[:4] == b"OTBM"


class TestOTBMValidation:
    """Verify OTBM validation catches structural issues."""

    def test_valid_otbm_passes(self):
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, 7))
        ser = OtbmSerializer()
        data = ser.serialize(world)

        from core.otbm.otbm_validator import OtbmValidator
        v = OtbmValidator()
        result = v.validate(data)
        assert result.is_valid

    def test_empty_data_fails(self):
        from core.otbm.otbm_validator import OtbmValidator
        v = OtbmValidator()
        result = v.validate(b"")
        # Empty data must fail validation
        assert not result.is_valid or len(result.errors) > 0

    def test_bad_magic_fails(self):
        from core.otbm.otbm_validator import OtbmValidator
        v = OtbmValidator()
        result = v.validate(b"XXXX" + b"\x00" * 100)
        assert not result.is_valid

    def test_truncated_otbm_fails(self):
        from core.otbm.otbm_validator import OtbmValidator
        v = OtbmValidator()
        result = v.validate(b"OTBM")
        # Truncated
        assert not result.is_valid


class TestOTBMPreview:
    """Verify the preview/get_summary pipeline."""

    def test_get_preview_returns_dict(self, tmp_path):
        world = WorldModel()
        for i in range(3):
            for j in range(3):
                world.set_tile(_make_tile(i, j, 7, ground=110))
        world.cities = [{"name": "C1", "temple_x": 0, "temple_y": 0, "temple_z": 7}]
        world.waypoints = [{"name": "W1", "x": 0, "y": 0, "z": 7}]
        world.spawns = [{"x": 0, "y": 0, "z": 7, "monster": "Rat", "interval": 60, "radius": 1}]

        ser = OtbmSerializer()
        data = ser.serialize(world)
        path = tmp_path / "preview.otbm"
        path.write_bytes(data)

        importer = OTBMImporter()
        preview = importer.get_preview(path)
        assert preview.get("valid") is True
        assert "tiles" in preview
        assert "version" in preview
        assert "width" in preview
        assert "height" in preview
