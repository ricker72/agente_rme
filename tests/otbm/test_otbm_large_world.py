"""
Tests for OTBM export with large / complex worlds.

Ensures the export pipeline (Serializer + Exporter + Roundtrip) can
handle maps with thousands of tiles, large ID values, and complex
structures without raising struct errors.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.otbm.otbm_serializer import OtbmSerializer
from core.otbm.otbm_importer import OTBMImporter
from core.world.world_model import WorldModel
from core.world.tile import Tile


def _make_tile(x, y, z, ground=106, items=None, flags=0):
    return Tile(x=x, y=y, z=z, ground=ground, items=items or [])


class TestLargeWorldExport:
    """Verify export of large world models."""

    def test_export_100x100_grid(self):
        world = WorldModel()
        for x in range(100):
            for y in range(100):
                world.set_tile(_make_tile(x, y, 7, ground=106))
        ser = OtbmSerializer()
        data = ser.serialize(world)
        # Must start with OTBM magic
        assert data[:4] == b"OTBM"
        # Should be at least 10 KB of data
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
            {"name": f"City{i}", "temple_x": i * 10, "temple_y": j * 10, "temple_z": 7}
            for i in range(5)
            for j in [0]
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
            {"name": f"WP{i}", "x": i * 10, "y": j * 10, "z": 7}
            for i in range(5)
            for j in [0]
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
            for i in range(5)
            for j in range(5)
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
                world.set_tile(
                    _make_tile(
                        i,
                        j,
                        7,
                        ground=106,
                        items=[{"id": 2050}, {"id": 2016}],
                    )
                )
        ser = OtbmSerializer()
        data = ser.serialize(world)
        assert data[:4] == b"OTBM"
        assert len(data) > 100

    def test_export_thousand_tile_map_runs_quickly(self):
        import time

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


class TestLargeWorldRoundtrip:
    """Verify roundtrip import -> export for large worlds."""

    def test_roundtrip_small_world(self):
        world = WorldModel()
        for i in range(5):
            for j in range(5):
                world.set_tile(_make_tile(i, j, 7))
        ser = OtbmSerializer()
        data = ser.serialize(world)

        # Import should not raise
        importer = OTBMImporter()
        result = importer.import_bytes(data)
        assert result["success"], f"Import failed: {result.get('error')}"
        assert result["stats"]["tiles"] > 0

        # Re-export should not raise
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
