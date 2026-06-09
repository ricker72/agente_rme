"""
Tests for OTBM byte range validation.

Verifies that all values written to OTBM binary are within the proper
integer ranges so that ``struct.pack`` never raises
``struct.error: 'B' format requires 0 <= number <= 255``
or ``struct.error: 'H' format requires 0 <= number <= 65535``.
"""

import io
import struct
import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.otbm.binary_writer import BinaryWriter
from core.otbm.node_encoder import NodeEncoder
from core.otbm.tile_encoder import TileEncoder


class TestBinaryWriterUint8:
    """Verify write_u8 clamps and never raises struct.error."""

    def test_valid_u8_writes_byte(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, 42, context="test")
        assert buf.getvalue() == b"\x2a"

    def test_u8_boundary_zero(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, 0, context="test")
        assert buf.getvalue() == b"\x00"

    def test_u8_boundary_max(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, 255, context="test")
        assert buf.getvalue() == b"\xff"

    def test_u8_above_range_clamps(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, 9999, context="test")
        assert buf.getvalue() == b"\xff"

    def test_u8_negative_clamps(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, -10, context="test")
        assert buf.getvalue() == b"\x00"

    def test_u8_none_treated_as_zero(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, None, context="test")
        assert buf.getvalue() == b"\x00"

    def test_u8_non_numeric_uses_zero(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u8(buf, "abc", context="test")
        assert buf.getvalue() == b"\x00"


class TestBinaryWriterUint16:
    """Verify write_u16 clamps and never raises struct.error."""

    def test_valid_u16(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u16(buf, 1000, context="test")
        assert buf.getvalue() == struct.pack("<H", 1000)

    def test_u16_boundary_max(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u16(buf, 65535, context="test")
        assert buf.getvalue() == b"\xff\xff"

    def test_u16_above_range_clamps(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u16(buf, 100000, context="test")
        assert buf.getvalue() == b"\xff\xff"

    def test_u16_negative_clamps(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u16(buf, -50, context="test")
        assert buf.getvalue() == b"\x00\x00"


class TestBinaryWriterUint32:
    """Verify write_u32 clamps and never raises struct.error."""

    def test_valid_u32(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u32(buf, 0xDEADBEEF, context="test")
        assert buf.getvalue() == struct.pack("<I", 0xDEADBEEF)

    def test_u32_huge_value_clamps(self):
        bw = BinaryWriter()
        buf = io.BytesIO()
        bw.write_u32(buf, 10 ** 30, context="test")
        # Should be clamped to 0xFFFFFFFF
        assert buf.getvalue() == b"\xff\xff\xff\xff"


class TestBinaryWriterValidation:
    """Test the validate_* helpers that raise on out-of-range."""

    def test_validate_u8_in_range(self):
        assert BinaryWriter.validate_u8(0) == 0
        assert BinaryWriter.validate_u8(255) == 255
        assert BinaryWriter.validate_u8(127) == 127

    def test_validate_u8_out_of_range_raises(self):
        with pytest.raises(ValueError):
            BinaryWriter.validate_u8(256)
        with pytest.raises(ValueError):
            BinaryWriter.validate_u8(-1)

    def test_validate_u8_none_raises(self):
        with pytest.raises(ValueError):
            BinaryWriter.validate_u8(None)

    def test_validate_u16_in_range(self):
        assert BinaryWriter.validate_u16(0) == 0
        assert BinaryWriter.validate_u16(65535) == 65535

    def test_validate_u16_out_of_range_raises(self):
        with pytest.raises(ValueError):
            BinaryWriter.validate_u16(65536)
        with pytest.raises(ValueError):
            BinaryWriter.validate_u16(-1)

    def test_validate_u32_in_range(self):
        assert BinaryWriter.validate_u32(0) == 0
        assert BinaryWriter.validate_u32(0xFFFFFFFF) == 0xFFFFFFFF

    def test_validate_u32_out_of_range_raises(self):
        with pytest.raises(ValueError):
            BinaryWriter.validate_u32(0x100000000)
        with pytest.raises(ValueError):
            BinaryWriter.validate_u32(-1)


class TestNodeEncoderByteRange:
    """Test that NodeEncoder.write_* paths never raise struct.error."""

    def test_encode_root_with_normal_values(self):
        enc = NodeEncoder()
        data = enc.encode_root(0, 200, 200, 3, 57, b"")
        assert len(data) > 0
        assert data[0] == 0x00  # OTBM_NODE_ROOT

    def test_encode_root_with_extreme_values(self):
        # Even with extreme width/height, the encoder should NOT raise
        # because the BinaryWriter clamps to uint16 range.
        enc = NodeEncoder()
        data = enc.encode_root(0, 99999, 99999, 99999, 99999, b"")
        assert len(data) > 0

    def test_encode_tile_area_with_extreme_z(self):
        enc = NodeEncoder()
        data = enc.encode_tile_area(0, 0, 999, b"")
        assert len(data) > 0

    def test_encode_tile_with_extreme_flags(self):
        enc = NodeEncoder()
        data = enc.encode_tile(0, 0, tile_flags=0xFFFFFFFF, children=b"")
        assert len(data) > 0

    def test_encode_spawn_area_extreme_radius(self):
        enc = NodeEncoder()
        data = enc.encode_spawn_area(0, 0, 7, 9999, b"")
        assert len(data) > 0

    def test_encode_monster_extreme_spawntime(self):
        enc = NodeEncoder()
        data = enc.encode_monster("Dragon", direction=2, spawntime=9999999)
        assert len(data) > 0

    def test_encode_town_extreme_id(self):
        enc = NodeEncoder()
        data = enc.encode_town(9999999, "City", 0, 0, 7)
        assert len(data) > 0

    def test_encode_waypoint_extreme_coords(self):
        enc = NodeEncoder()
        data = enc.encode_waypoint("Spawn", 99999, 99999, 999)
        assert len(data) > 0


class TestTileEncoderByteRange:
    """Test that TileEncoder offsets are clamped to [0, 255]."""

    def test_offset_clamped_above_255(self):
        enc = TileEncoder()
        data = enc.encode_tile_from_dict(
            {"x": 500, "y": 500, "z": 7, "ground": 106, "items": []},
            base_x=0, base_y=0,
        )
        # Must not raise; the offset is clamped to 255.
        assert len(data) > 0

    def test_offset_clamped_negative(self):
        enc = TileEncoder()
        data = enc.encode_tile_from_dict(
            {"x": 0, "y": 0, "z": 7, "ground": 106, "items": []},
            base_x=500, base_y=500,
        )
        assert len(data) > 0

    def test_spawn_area_extreme_values(self):
        enc = TileEncoder()
        data = enc.encode_spawn_area_from_entry(
            x=99999, y=99999, z=999, monster_name="Boss",
            interval=999999, radius=999,
        )
        assert len(data) > 0

    def test_house_tile_extreme_id(self):
        enc = TileEncoder()
        data = enc.encode_house_tile(
            offset_x=0, offset_y=0, house_id=0xFFFFFFFF
        )
        assert len(data) > 0
