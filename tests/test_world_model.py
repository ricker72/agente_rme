"""
Tests for the unified WorldModel class.
Covers the core API: set_tile, get_tile, structures, regions, chunks, serialization.
"""

import pytest

from core.world import Tile, Item, Spawn, Structure, Region, WorldModel


class TestWorldModel:
    """Test the unified WorldModel."""

    @pytest.fixture
    def world(self):
        """Create a fresh empty WorldModel."""
        return WorldModel()

    def test_set_and_get_tile(self, world):
        """set_tile + get_tile should round-trip correctly."""
        tile = Tile(x=100, y=100, z=7, ground=817)
        world.set_tile(tile)

        retrieved = world.get_tile(100, 100, 7)
        assert retrieved is not None
        assert retrieved.x == 100
        assert retrieved.y == 100
        assert retrieved.z == 7
        assert retrieved.ground == 817

    def test_has_tile(self, world):
        """has_tile returns correct boolean."""
        assert not world.has_tile(50, 50, 7)
        world.set_tile(Tile(x=50, y=50, z=7))
        assert world.has_tile(50, 50, 7)

    def test_tile_count(self, world):
        """tile_count tracks total tiles."""
        assert world.tile_count() == 0
        world.set_tile(Tile(x=0, y=0, z=7))
        assert world.tile_count() == 1
        world.set_tile(Tile(x=1, y=0, z=7))
        assert world.tile_count() == 2

    def test_set_same_tile_does_not_duplicate(self, world):
        """Setting the same tile again should not increase count."""
        world.set_tile(Tile(x=100, y=100, z=7))
        assert world.tile_count() == 1
        world.set_tile(Tile(x=100, y=100, z=7, ground=888))
        assert world.tile_count() == 1  # Same key, no new tile
        # But ground should be updated
        assert world.get_tile(100, 100, 7).ground == 888

    def test_remove_tile(self, world):
        """remove_tile removes a tile and decrements count."""
        world.set_tile(Tile(x=10, y=10, z=7))
        assert world.tile_count() == 1
        assert world.remove_tile(10, 10, 7) is True
        assert world.tile_count() == 0
        assert world.get_tile(10, 10, 7) is None

    def test_remove_nonexistent_tile(self, world):
        """remove_tile returns False for non-existent tile."""
        assert world.remove_tile(999, 999, 7) is False

    def test_get_tiles_in_area(self, world):
        """get_tiles_in_area returns tiles within rectangle."""
        for x in range(0, 10):
            for y in range(0, 10):
                world.set_tile(Tile(x=x, y=y, z=7, ground=100))

        area = world.get_tiles_in_area(2, 2, 5, 5)
        assert len(area) == 16  # 4x4 = 16

    def test_get_tiles_in_area_z_filter(self, world):
        """get_tiles_in_area filters by Z level."""
        world.set_tile(Tile(x=0, y=0, z=7))
        world.set_tile(Tile(x=0, y=0, z=6))
        area = world.get_tiles_in_area(0, 0, 10, 10, z=7)
        assert len(area) == 1

    def test_add_structure(self, world):
        """add_structure registers a Structure."""
        s = Structure(
            name="test_bp", category="temple", x=1000, y=1000, z=7, width=20, height=20
        )
        world.add_structure(s)
        assert world.structure_count() == 1

    def test_get_structure_by_name(self, world):
        """get_structure finds by name."""
        s1 = Structure(
            name="temple_a", category="temple", x=0, y=0, z=7, width=10, height=10
        )
        s2 = Structure(
            name="temple_b", category="temple", x=10, y=0, z=7, width=10, height=10
        )
        world.add_structure(s1)
        world.add_structure(s2)

        found = world.get_structure("temple_a")
        assert found is not None
        assert found.name == "temple_a"

        assert world.get_structure("nonexistent") is None

    def test_get_structures_by_category(self, world):
        """get_structures_by_category filters by category."""
        world.add_structure(
            Structure(name="t1", category="temple", x=0, y=0, z=7, width=5, height=5)
        )
        world.add_structure(
            Structure(name="m1", category="market", x=0, y=0, z=7, width=5, height=5)
        )
        world.add_structure(
            Structure(name="t2", category="temple", x=0, y=0, z=7, width=5, height=5)
        )

        temples = world.get_structures_by_category("temple")
        assert len(temples) == 2
        markets = world.get_structures_by_category("market")
        assert len(markets) == 1

    def test_add_region(self, world):
        """add_region registers a Region."""
        r = Region(name="issavi_center", theme="issavi", min_level=1, max_level=50)
        world.add_region(r)
        assert world.region_count() == 1

    def test_get_region_by_name(self, world):
        """get_region finds by name."""
        r = Region(name="test_zone", theme="roshamuul")
        world.add_region(r)
        found = world.get_region("test_zone")
        assert found is not None
        assert found.theme == "roshamuul"

    def test_get_regions_by_theme(self, world):
        """get_regions_by_theme filters by theme."""
        world.add_region(Region(name="r1", theme="issavi"))
        world.add_region(Region(name="r2", theme="roshamuul"))
        world.add_region(Region(name="r3", theme="issavi"))

        issavi_regions = world.get_regions_by_theme("issavi")
        assert len(issavi_regions) == 2

    def test_chunk_creation_on_set_tile(self, world):
        """Setting a tile should create a chunk automatically."""
        world.set_tile(Tile(x=0, y=0, z=7))
        assert world.chunk_count() == 1

        # Same chunk
        world.set_tile(Tile(x=1, y=1, z=7))
        assert world.chunk_count() == 1

        # Different chunk (at 64,64 boundary)
        world.set_tile(Tile(x=100, y=100, z=7))
        assert world.chunk_count() == 2

    def test_get_chunk(self, world):
        """get_chunk returns chunk by indices."""
        world.set_tile(Tile(x=0, y=0, z=7))
        chunk = world.get_chunk(0, 0)
        assert chunk is not None
        assert chunk.chunk_x == 0
        assert chunk.chunk_y == 0

    def test_get_chunk_for(self, world):
        """get_chunk_for returns chunk containing a coordinate."""
        world.set_tile(Tile(x=100, y=100, z=7))
        chunk = world.get_chunk_for(100, 100)
        assert chunk is not None

    def test_clear(self, world):
        """clear removes everything."""
        world.set_tile(Tile(x=0, y=0, z=7))
        world.add_structure(
            Structure(name="s", category="t", x=0, y=0, z=7, width=5, height=5)
        )
        world.add_region(Region(name="r", theme="g"))
        world.clear()

        assert world.tile_count() == 0
        assert world.structure_count() == 0
        assert world.region_count() == 0
        assert world.chunk_count() == 0

    def test_summary(self, world):
        """summary returns a structured dict."""
        world.set_tile(Tile(x=0, y=0, z=7))
        world.add_structure(
            Structure(name="s", category="t", x=0, y=0, z=7, width=5, height=5)
        )

        summary = world.summary()
        assert "tiles" in summary
        assert summary["tiles"] > 0
        assert "structures" in summary
        assert summary["structures"] > 0
        assert "bounds" in summary

    def test_serialization_round_trip(self, world):
        """to_dict() + from_dict() should round-trip."""

        world.set_tile(Tile(x=10, y=20, z=7, ground=817))
        world.set_tile(Tile(x=11, y=20, z=7, ground=415))
        world.add_structure(
            Structure(name="s1", category="temple", x=10, y=20, z=7, width=2, height=1)
        )
        world.add_region(Region(name="test", theme="issavi"))

        data = world.to_dict()
        restored = WorldModel.from_dict(data)

        assert restored.tile_count() == 2
        assert restored.structure_count() == 1
        assert restored.region_count() == 1
        assert restored.get_tile(10, 20, 7).ground == 817
        assert restored.get_structure("s1") is not None
        assert restored.get_region("test") is not None

    def test_get_ground_ids_in_area(self, world):
        """get_ground_ids_in_area returns unique sorted ground IDs."""
        world.set_tile(Tile(x=0, y=0, z=7, ground=415))
        world.set_tile(Tile(x=1, y=0, z=7, ground=817))
        world.set_tile(Tile(x=0, y=1, z=7, ground=415))

        grounds = world.get_ground_ids_in_area(0, 0, 5, 5)
        assert 415 in grounds
        assert 817 in grounds
        assert 415 in grounds  # deduplicated
        assert grounds == sorted(grounds)

    def test_set_tile_with_full_data(self, world):
        """Setting a tile with items and spawn should preserve them."""
        tile = Tile(x=5, y=5, z=7, ground=817)
        tile.items.append(Item(itemid=2050))  # Torch
        tile.items.append(Item(itemid=1503))  # Fountain
        tile.spawn = Spawn(monster="Dragon", respawn=120, radius=7)

        world.set_tile(tile)
        retrieved = world.get_tile(5, 5, 7)

        assert retrieved is not None
        assert len(retrieved.items) == 2
        assert retrieved.items[0].itemid == 2050
        assert retrieved.spawn is not None
        assert retrieved.spawn.monster == "Dragon"
        assert retrieved.spawn.respawn == 120
        assert retrieved.spawn.radius == 7

    def test_definition_of_success(self):
        """The exact example from the task spec must work."""
        world = WorldModel()
        world.set_tile(Tile(x=100, y=100, z=7))
        result = world.get_tile(100, 100, 7)
        assert result is not None
        assert isinstance(result, Tile)
        assert result.x == 100
        assert result.y == 100
        assert result.z == 7
