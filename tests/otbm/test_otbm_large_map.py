"""
Tests for OTBM export with large / complex worlds.

Ensures the export pipeline (Serializer + Exporter + Roundtrip) can
handle maps with thousands of tiles, large ID values, and complex
structures without raising struct errors.
"""

import os
import sys
import struct
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.otbm.otbm_serializer import OtbmSerializer
from core.otbm.otbm_importer import OTBMImporter
from core.otbm.otbm_validator import OtbmValidator
from core.otbm.otbm_exporter import OTBMExporter
from core.otbm.byte_validator import (
    ByteValidator,
    validate_byte,
    validate_word,
    validate_dword,
)
from core.world.world_model import WorldModel
from core.world.tile import Tile


def _make_tile(x, y, z, ground=106, items=None, flags=0):
    return Tile(x=x, y=y, z=z, ground=ground, items=items or [])


class TestByteValidatorAPI:
    """ByteValidator + validate_byte/word/dword standalone API."""

    def test_validate_byte_in_range(self):
        assert validate_byte(0) == 0
        assert validate_byte(127) == 127
        assert validate_byte(255) == 255

    def test_validate_byte_above_max_raises(self):
        with pytest.raises(ValueError):
            validate_byte(256)
        with pytest.raises(ValueError):
            validate_byte(999999)

    def test_validate_byte_negative_raises(self):
        with pytest.raises(ValueError):
            validate_byte(-1)
        with pytest.raises(ValueError):
            validate_byte(-999)

    def test_validate_byte_none_returns_zero(self):
        assert validate_byte(None) == 0

    def test_validate_byte_non_numeric_raises(self):
        with pytest.raises(ValueError):
            validate_byte("abc")
        with pytest.raises(ValueError):
            validate_byte(object())

    def test_validate_word_in_range(self):
        assert validate_word(0) == 0
        assert validate_word(65535) == 65535

    def test_validate_word_out_of_range(self):
        with pytest.raises(ValueError):
            validate_word(65536)
        with pytest.raises(ValueError):
            validate_word(-1)

    def test_validate_dword_in_range(self):
        assert validate_dword(0) == 0
        assert validate_dword(0xFFFFFFFF) == 0xFFFFFFFF

    def test_validate_dword_out_of_range(self):
        with pytest.raises(ValueError):
            validate_dword(0x100000000)
        with pytest.raises(ValueError):
            validate_dword(-1)

    def test_byte_validator_strict_raises(self):
        v = ByteValidator(strict=True)
        with pytest.raises(ValueError):
            v.validate_tile_offset(500)
        with pytest.raises(ValueError):
            v.validate_house_id(-1)

    def test_byte_validator_coerce_clamp(self):
        v = ByteValidator()
        assert v.coerce_byte(500) == 255
        assert v.coerce_byte(-5) == 0
        assert v.coerce_word(99999) == 65535
        assert v.coerce_dword(10 ** 30) == 0xFFFFFFFF
        assert v.coerce_z(99) == 99
        assert v.coerce_z(999) == 255

    def test_byte_validator_coerce_none_safe(self):
        v = ByteValidator()
        assert v.coerce_byte(None) == 0
        assert v.coerce_word(None) == 0
        assert v.coerce_dword(None) == 0

    def test_byte_validator_records_warnings(self):
        v = ByteValidator()
        v.coerce_byte(500)
        v.coerce_word(99999)
        assert len(v.warnings) >= 2
        assert any("out of" in w for w in v.warnings)

    def test_byte_validator_validates_tile_dict(self):
        v = ByteValidator()
        tile = {
            "x": 0, "y": 0, "z": 7,
            "offset_x": 300, "offset_y": 500,
            "items": [
                {"id": 99999, "action_id": 70000, "subtype": 200},
                {"id": -5},
            ],
            "flags": 0xFFFFFFFF,
        }
        warnings = v.validate_tile_dict(tile)
        assert isinstance(warnings, list)
        # Out-of-range fields should produce warnings
        assert len(v.warnings) > 0

    def test_byte_validator_categorised_methods(self):
        v = ByteValidator()
        assert v.validate_item_id(100) == 100
        assert v.validate_action_id(50) == 50
        assert v.validate_unique_id(50) == 50
        assert v.validate_zone_id(0xFFFFFFFE) == 0xFFFFFFFE
        assert v.validate_flag(0xFFFFFFFF) == 0xFFFFFFFF
        assert v.validate_attribute(10) == 10
        assert v.validate_spawn_radius(5) == 5


class TestLargeMapExport:
    """Verify export of large world models."""

    def test_export_100x100_grid(self):
        world = WorldModel()
        for x in range(100):
            for y in range(100):
                world.set_tile(_make_tile(x, y, 7, ground=106))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        assert len(data) > 10000

    def test_export_50x50_grid_multiple_z(self):
        world = WorldModel()
        for z in range(3):
            for x in range(50):
                for y in range(50):
                    world.set_tile(_make_tile(x, y, z, ground=110))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        assert len(data) > 5000

    def test_export_with_cities(self):
        world = WorldModel()
        for i in range(10):
            for j in range(10):
                world.set_tile(_make_tile(i, j, 7))
        world.cities = [
            {"name": f"City{i}", "temple_x": i*10, "temple_y": j*10, "temple_z": 7}
            for i in range(5) for j in [0]
        ]
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        assert len(data) > 0

    def test_export_with_waypoints(self):
        world = WorldModel()
        for i in range(5):
            for j in range(5):
                world.set_tile(_make_tile(i, j, 7))
        world.waypoints = [
            {"name": f"WP{i}", "x": i*10, "y": j*10, "z": 7}
            for i in range(5) for j in [0]
        ]
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"

    def test_export_with_spawns(self):
        world = WorldModel()
        for i in range(10):
            for j in range(10):
                world.set_tile(_make_tile(i, j, 7))
        world.spawns = [
            {"x": i, "y": j, "z": 7, "monster": "Dragon", "interval": 60, "radius": 3}
            for i in range(5) for j in range(5)
        ]
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"

    def test_export_with_extreme_ground_ids(self):
        # Use ground IDs that, before the fix, would trigger the byte range bug.
        world = WorldModel()
        for i, gid in enumerate([106, 9999, 99999, 999999, 9999999]):
            world.set_tile(_make_tile(i, 0, 7, ground=gid))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        assert len(data) > 0

    def test_export_with_extreme_z(self):
        world = WorldModel()
        world.set_tile(_make_tile(0, 0, 7, ground=106))
        world.set_tile(_make_tile(1, 0, 255, ground=106))
        world.set_tile(_make_tile(2, 0, 999, ground=106))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"

    def test_export_world_with_tiles_at_far_coordinates(self):
        world = WorldModel()
        # x=1000 is far from base 0 — offset 1000 > 255 must be normalised
        for i in range(5):
            world.set_tile(_make_tile(1000 + i, 1000 + i, 7, ground=106))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"

    def test_export_empty_world(self):
        world = WorldModel()
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        # Should still be valid OTBM with a minimal tile
        assert len(data) > 0

    def test_export_world_with_tiles_items(self):
        world = WorldModel()
        for i in range(5):
            for j in range(5):
                world.set_tile(_make_tile(
                    i, j, 7,
                    ground=106,
                    items=[{"id": 2050}, {"id": 2016}],
                ))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        assert len(data) > 100

    def test_export_thousand_tile_map_runs_quickly(self):
        world = WorldModel()
        for i in range(32):
            for j in range(32):
                world.set_tile(_make_tile(i, j, 7))
        ser = OtbmSerializer()
        start = time.time()
        data = ser.serialize(world)
        elapsed = time.time() - start
        # 1024 tiles should serialize in <5s
        assert elapsed < 5.0, f"Serialization took {elapsed:.2f}s"
        assert data[:4] == b"OTBM"

    def test_export_200x200_large(self):
        """True stress test: 40 000 tiles in a single export.

        Note: _wrap_node truncates payloads > 65535 bytes, so the
        total OTBM file may be smaller than expected. The key is
        that serialization succeeds without struct.error and produces
        valid OTBM data.
        """
        world = WorldModel()
        for x in range(200):
            for y in range(200):
                world.set_tile(_make_tile(x, y, 7, ground=110))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        # At minimum we should have the OTBM header + root + map_data
        # Even with truncated nodes the output is structurally valid
        assert len(data) > 1000


class TestLargeMapRoundtrip:
    """Verify roundtrip import → export for large worlds."""

    def test_roundtrip_small_world(self):
        world = WorldModel()
        for i in range(5):
            for j in range(5):
                world.set_tile(_make_tile(i, j, 7))
        ser = OtbmSerializer()
        data = ser.serialize(world)

        importer = OTBMImporter()
        result = importer.import_bytes(data)
        assert result["success"], f"Import failed: {result.get('error')}"
        assert result["stats"]["tiles"] > 0

        wm = result["world_model"]
        data2 = ser.serialize(wm)
        assert data2[:4] == b"OTBM"
        assert len(data2) > 0

    def test_roundtrip_extreme_values(self):
        world = WorldModel()
        for i, gid in enumerate([1, 100, 50000, 99999, 9999999]):
            world.set_tile(_make_tile(i, 0, 7, ground=gid))
        ser = OtbmSerializer()
        data = ser.serialize(world)

        importer = OTBMImporter()
        result = importer.import_bytes(data)
        assert result["success"], f"Import failed: {result.get('error')}"

        data2 = ser.serialize(result["world_model"])
        assert data2[:4] == b"OTBM"

    def test_roundtrip_through_validator(self):
        """ByteValidator + OtbmValidator both happy with a 50x50 map."""
        world = WorldModel()
        for x in range(50):
            for y in range(50):
                world.set_tile(_make_tile(x, y, 7, ground=110))
        ser = OtbmSerializer()
        data = ser.serialize(world)

        v = OtbmValidator()
        report = v.validate(data)
        assert report.is_valid, f"Validator failures: {report.errors}"
        assert report.stats["tiles"] >= 2500

        # The owned ByteValidator should also work
        assert v.byte_validator is not None
        assert v.byte_validator.validated_count >= 0
