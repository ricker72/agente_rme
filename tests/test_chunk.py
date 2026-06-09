"""
Tests for the Chunk dataclass.
Covers coordinate conversion, tile operations, and serialization.
"""

import pytest

from core.world import Chunk, Tile
from core.world.chunk import DEFAULT_CHUNK_SIZE


class TestChunk:
    """Test the Chunk spatial partitioning."""

    @pytest.fixture
    def chunk(self):
        """Create a default chunk at (0, 0)."""
        return Chunk(chunk_x=0, chunk_y=0)

    def test_chunk_creation(self, chunk):
        """A fresh chunk is empty."""
        assert chunk.chunk_x == 0
        assert chunk.chunk_y == 0
        assert chunk.tile_count() == 0
        assert chunk.chunk_size == DEFAULT_CHUNK_SIZE

    def test_world_offset(self, chunk):
        """world_offset is chunk_index * chunk_size."""
        assert chunk.world_offset_x == 0
        assert chunk.world_offset_y == 0

        c2 = Chunk(chunk_x=3, chunk_y=5)
        assert c2.world_offset_x == 3 * DEFAULT_CHUNK_SIZE
        assert c2.world_offset_y == 5 * DEFAULT_CHUNK_SIZE

    def test_bounds_world(self, chunk):
        """bounds_world returns correct world-space bounds."""
        min_x, min_y, max_x, max_y = chunk.bounds_world
        assert min_x == 0
        assert min_y == 0
        assert max_x == DEFAULT_CHUNK_SIZE
        assert max_y == DEFAULT_CHUNK_SIZE

    def test_world_to_chunk(self):
        """world_to_chunk converts world coords to chunk indices."""
        assert Chunk.world_to_chunk(0, 0) == (0, 0)
        assert Chunk.world_to_chunk(63, 63) == (0, 0)
        assert Chunk.world_to_chunk(64, 0) == (1, 0)
        assert Chunk.world_to_chunk(0, 64) == (0, 1)
        assert Chunk.world_to_chunk(100, 200) == (1, 3)

    def test_world_to_local(self):
        """world_to_local converts world coords to local chunk coords."""
        assert Chunk.world_to_local(0, 0) == (0, 0)
        assert Chunk.world_to_local(63, 63) == (63, 63)
        assert Chunk.world_to_local(64, 0) == (0, 0)
        assert Chunk.world_to_local(65, 65) == (1, 1)
        assert Chunk.world_to_local(127, 127) == (63, 63)
        assert Chunk.world_to_local(128, 128) == (0, 0)

    def test_to_local(self, chunk):
        """to_local converts world coords to local within chunk."""
        assert chunk.to_local(0, 0) == (0, 0)
        assert chunk.to_local(63, 63) == (63, 63)

        c2 = Chunk(chunk_x=2, chunk_y=3)
        assert c2.to_local(128, 192) == (0, 0)  # 2*64=128, 3*64=192
        assert c2.to_local(130, 195) == (2, 3)

    def test_set_and_get_tile(self, chunk):
        """set_tile and get_tile work within a chunk."""
        tile = Tile(x=10, y=10, z=7, ground=817)
        chunk.set_tile(tile)

        assert chunk.tile_count() == 1
        retrieved = chunk.get_tile(10, 10)
        assert retrieved is not None
        assert retrieved.ground == 817

    def test_get_tile_nonexistent(self, chunk):
        """get_tile returns None for missing tile."""
        assert chunk.get_tile(999, 999) is None

    def test_has_tile(self, chunk):
        """has_tile returns correct boolean."""
        chunk.set_tile(Tile(x=5, y=5, z=7))
        assert chunk.has_tile(5, 5) is True
        assert chunk.has_tile(99, 99) is False

    def test_clear(self, chunk):
        """clear removes all tiles."""
        chunk.set_tile(Tile(x=0, y=0, z=7))
        chunk.set_tile(Tile(x=1, y=0, z=7))
        assert chunk.tile_count() == 2
        chunk.clear()
        assert chunk.tile_count() == 0

    def test_serialization_round_trip(self, chunk):
        """Chunk to_dict + from_dict round-trips."""
        chunk.set_tile(Tile(x=10, y=10, z=7, ground=817))
        chunk.set_tile(Tile(x=20, y=30, z=7, ground=415))

        data = chunk.to_dict()
        restored = Chunk.from_dict(data)

        assert restored.chunk_x == 0
        assert restored.chunk_y == 0
        assert restored.tile_count() == 2
        assert restored.get_tile(10, 10).ground == 817
        assert restored.get_tile(20, 30).ground == 415

    def test_chunk_repr(self, chunk):
        """Chunk repr includes indices and tile count."""
        s = repr(chunk)
        assert "Chunk" in s
        assert "0" in s
        assert "0" in s
        assert "0" in s  # tile_count

    def test_large_chunk_capacity(self):
        """Chunk can hold up to 64x64 tiles."""
        c = Chunk(chunk_x=0, chunk_y=0)
        for x in range(DEFAULT_CHUNK_SIZE):
            for y in range(DEFAULT_CHUNK_SIZE):
                c.set_tile(Tile(x=x, y=y, z=7))
        assert c.tile_count() == DEFAULT_CHUNK_SIZE * DEFAULT_CHUNK_SIZE