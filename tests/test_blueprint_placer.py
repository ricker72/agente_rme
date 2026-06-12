"""
Tests for the BlueprintPlacer class.
Covers placing tile-based and descriptive blueprints into WorldModel.
"""

import pytest

from core.blueprints import Blueprint, BlueprintTile, BlueprintPlacer


class TestBlueprintPlacer:
    """Test placing blueprints into WorldModel."""

    @pytest.fixture
    def placer(self):
        """Create a BlueprintPlacer."""
        return BlueprintPlacer()

    @pytest.fixture
    def tile_based_bp(self):
        """Create a simple tile-based blueprint."""
        bp = Blueprint(
            name="test_tile_bp",
            theme="test",
            category="building",
            size=(4, 4),
            entry=(2, 3),
        )
        bp.tiles = [
            BlueprintTile(x=0, y=0, ground=100),
            BlueprintTile(x=1, y=0, ground=100),
            BlueprintTile(x=2, y=0, ground=100),
            BlueprintTile(x=3, y=0, ground=100),
            BlueprintTile(x=0, y=1, ground=100),
            BlueprintTile(x=1, y=1, ground=200, item=500),
            BlueprintTile(x=2, y=1, ground=100),
            BlueprintTile(x=3, y=1, ground=100),
            BlueprintTile(x=0, y=2, ground=100),
            BlueprintTile(x=1, y=2, ground=100),
            BlueprintTile(x=2, y=2, ground=100),
            BlueprintTile(x=3, y=2, ground=100),
            BlueprintTile(x=0, y=3, ground=817),
            BlueprintTile(x=1, y=3, ground=817),
            BlueprintTile(x=2, y=3, ground=817),
            BlueprintTile(x=3, y=3, ground=817),
        ]
        return bp

    @pytest.fixture
    def descriptive_bp(self):
        """Create a simple descriptive blueprint."""
        bp = Blueprint(
            name="test_descriptive",
            theme="issavi",
            category="temple",
            size=(5, 5),
            entry=(2, 4),
            grounds=[415, 393],
            features=[
                {"type": "altar", "position": [2, 2], "item_id": 1512},
                {"type": "torch", "position": [1, 1], "item_id": 2050},
            ],
        )
        return bp

    def test_place_tile_based(self, placer, tile_based_bp):
        """Placing a tile-based blueprint adds tiles to world model."""
        world = placer.place(tile_based_bp, x=1000, y=1000, z=7)
        assert world is not None
        assert len(world.tiles) == 16  # 4x4 grid

        # Check specific tile
        key = "1000:1000:7"
        assert key in world.tiles
        tile = world.tiles[key]
        assert tile.x == 1000
        assert tile.y == 1000
        assert tile.z == 7

    def test_place_tile_based_with_offset(self, placer, tile_based_bp):
        """Placing with offset offsets the tile positions."""
        world = placer.place(tile_based_bp, x=500, y=600, z=7)
        key = "500:600:7"
        assert key in world.tiles
        assert world.tiles[key].x == 500
        assert world.tiles[key].y == 600

        # Last tile should be at (500+3, 600+3)
        key_end = "503:603:7"
        assert key_end in world.tiles

    def test_place_tile_based_items(self, placer, tile_based_bp):
        """Tiles with items should have them in the world model."""
        world = placer.place(tile_based_bp, x=0, y=0, z=7)
        # Tile at (1,1) has item 500
        key = "1:1:7"
        tile = world.tiles[key]
        assert len(tile.items) > 0
        assert tile.items[0]["id"] == 500

    def test_collision_detection(self, placer, tile_based_bp):
        """Tiles already occupied should be skipped with collision check."""
        world = placer.place(tile_based_bp, x=0, y=0, z=7, check_collision=True)
        # Place the same blueprint at the same position
        world2 = placer.place(
            tile_based_bp, x=0, y=0, z=7, world_model=world, check_collision=True
        )
        # No new tiles should be added
        assert len(world2.tiles) == 16  # Should remain the same

    def test_place_descriptive(self, placer, descriptive_bp):
        """Placing a descriptive blueprint should expand into tiles."""
        world = placer.place(descriptive_bp, x=1000, y=1000, z=7)
        assert world is not None
        assert len(world.tiles) == 25  # 5x5 grid + features on existing tiles

    def test_place_descriptive_grounds(self, placer, descriptive_bp):
        """Descriptive blueprint should use the ground IDs from specification."""
        world = placer.place(descriptive_bp, x=0, y=0, z=7)
        key = "0:0:7"
        tile = world.tiles[key]
        assert tile.ground == str(415) or tile.ground == str(393)

    def test_place_descriptive_features(self, placer, descriptive_bp):
        """Features in descriptive blueprint should add items to tiles."""
        world = placer.place(descriptive_bp, x=0, y=0, z=7)
        # Altar at (2,2)
        altar_key = "2:2:7"
        assert altar_key in world.tiles
        altar_tile = world.tiles[altar_key]
        assert len(altar_tile.items) > 0
        assert altar_tile.items[0]["id"] == 1512

    def test_place_batch(self, placer, tile_based_bp):
        """place_batch should place multiple blueprints."""
        blueprints = [
            (tile_based_bp, 0, 0, 7),
            (tile_based_bp, 10, 10, 7),
        ]
        world = placer.place_batch(blueprints)
        assert len(world.tiles) == 32  # 16 + 16

        # First blueprint at (0,0)
        assert "0:0:7" in world.tiles
        # Second blueprint at (10,10)
        assert "10:10:7" in world.tiles

    def test_place_creates_new_world(self, placer, tile_based_bp):
        """place() with no world_model creates a new one."""
        world = placer.place(tile_based_bp, x=0, y=0, z=7, world_model=None)
        assert world is not None
        assert len(world.tiles) == 16

    def test_create_world_model(self, placer):
        """create_world_model() returns a fresh WorldModel."""
        wm = placer.create_world_model()
        assert wm is not None
        assert len(wm.tiles) == 0

    def test_get_place_count(self, placer, tile_based_bp):
        """get_place_count() returns number of place operations."""
        assert placer.get_place_count() == 0
        placer.place(tile_based_bp, x=0, y=0, z=7)
        assert placer.get_place_count() == 1
        placer.place(tile_based_bp, x=10, y=10, z=7)
        assert placer.get_place_count() == 2
