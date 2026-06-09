"""
Tests for the Tile, Item, and Spawn dataclasses.
"""

import pytest

from core.world import Tile, Item, Spawn
from core.world.tile import Tile as TileClass


class TestTile:
    """Test the Tile dataclass."""

    def test_tile_creation(self):
        """Create a basic tile."""
        tile = Tile(x=10, y=20, z=7)
        assert tile.x == 10
        assert tile.y == 20
        assert tile.z == 7
        assert tile.ground is None
        assert tile.items == []
        assert tile.spawn is None
        assert tile.zone is None

    def test_tile_with_ground(self):
        """Create a tile with a ground ID."""
        tile = Tile(x=0, y=0, z=7, ground=817)
        assert tile.ground == 817

    def test_tile_with_items(self):
        """Tile can hold items."""
        tile = Tile(x=0, y=0, z=7, ground=415)
        tile.items.append(Item(itemid=2050))
        tile.items.append(Item(itemid=1503))
        assert len(tile.items) == 2

    def test_tile_with_spawn(self):
        """Tile can hold a spawn."""
        tile = Tile(x=0, y=0, z=7)
        tile.spawn = Spawn(monster="Dragon", respawn=60, radius=5)
        assert tile.spawn.monster == "Dragon"
        assert tile.spawn.respawn == 60
        assert tile.spawn.radius == 5

    def test_tile_with_zone(self):
        """Tile can have a zone label."""
        tile = Tile(x=0, y=0, z=7, zone="temple")
        assert tile.zone == "temple"

    def test_tile_key_property(self):
        """Tile.key returns 'x:y:z' formatted string."""
        tile = Tile(x=100, y=200, z=7)
        assert tile.key == "100:200:7"

    def test_tile_make_key_static(self):
        """Tile.make_key is a static method."""
        key = TileClass.make_key(100, 200, 7)
        assert key == "100:200:7"

    def test_tile_serialization_round_trip(self):
        """to_dict + from_dict round-trips correctly."""
        tile = Tile(x=10, y=20, z=7, ground=817)
        tile.items.append(Item(itemid=2050, count=1))
        tile.spawn = Spawn(monster="Demon", respawn=120, radius=7)
        tile.zone = "boss_room"

        data = tile.to_dict()
        restored = Tile.from_dict(data)

        assert restored.x == 10
        assert restored.y == 20
        assert restored.z == 7
        assert restored.ground == 817
        assert len(restored.items) == 1
        assert restored.items[0].itemid == 2050
        assert restored.spawn.monster == "Demon"
        assert restored.zone == "boss_room"

    def test_tile_repr(self):
        """Tile repr includes key info."""
        tile = Tile(x=1, y=2, z=7, ground=817)
        tile.items.append(Item(itemid=100))
        s = repr(tile)
        assert "Tile" in s
        assert "x=1" in s
        assert "y=2" in s
        assert "z=7" in s
        assert "ground=817" in s

    def test_z_is_required(self):
        """Z is a required parameter."""
        with pytest.raises(TypeError):
            Tile(x=0, y=0)  # z is required


class TestItem:
    """Test the Item dataclass."""

    def test_item_creation(self):
        """Create a basic item."""
        item = Item(itemid=2050)
        assert item.itemid == 2050
        assert item.count == 1
        assert item.actionid is None
        assert item.uniqueid is None

    def test_item_with_count(self):
        """Create an item with count."""
        item = Item(itemid=2050, count=5)
        assert item.count == 5

    def test_item_with_actionid(self):
        """Create an item with actionid."""
        item = Item(itemid=1945, actionid=100)
        assert item.actionid == 100

    def test_item_with_uniqueid(self):
        """Create an item with uniqueid."""
        item = Item(itemid=1740, uniqueid=5000)
        assert item.uniqueid == 5000

    def test_item_serialization(self):
        """Item to_dict and from_dict round-trip."""
        item = Item(itemid=2050, count=3, actionid=100, uniqueid=5000)
        data = item.to_dict()
        restored = Item.from_dict(data)
        assert restored.itemid == 2050
        assert restored.count == 3
        assert restored.actionid == 100
        assert restored.uniqueid == 5000

    def test_item_from_dict_with_id_key(self):
        """from_dict accepts 'id' as fallback key."""
        data = {"id": 1512, "count": 1}
        item = Item.from_dict(data)
        assert item.itemid == 1512

    def test_item_repr(self):
        """Item repr includes itemid."""
        s = repr(Item(itemid=2050))
        assert "itemid=2050" in s
        assert "Item" in s


class TestSpawn:
    """Test the Spawn dataclass."""

    def test_spawn_creation(self):
        """Create a basic spawn."""
        spawn = Spawn(monster="Dragon")
        assert spawn.monster == "Dragon"
        assert spawn.respawn == 60
        assert spawn.radius == 5

    def test_spawn_custom_values(self):
        """Create a spawn with custom values."""
        spawn = Spawn(monster="Demon", respawn=120, radius=7)
        assert spawn.monster == "Demon"
        assert spawn.respawn == 120
        assert spawn.radius == 7

    def test_spawn_serialization(self):
        """Spawn to_dict and from_dict round-trip."""
        spawn = Spawn(monster="Orc Berserker", respawn=90, radius=4)
        data = spawn.to_dict()
        restored = Spawn.from_dict(data)
        assert restored.monster == "Orc Berserker"
        assert restored.respawn == 90
        assert restored.radius == 4

    def test_spawn_from_dict_with_name_fallback(self):
        """from_dict accepts 'name' as fallback key."""
        data = {"name": "Dragon Lord", "respawn": 60, "radius": 5}
        spawn = Spawn.from_dict(data)
        assert spawn.monster == "Dragon Lord"

    def test_spawn_repr(self):
        """Spawn repr includes monster name."""
        s = repr(Spawn(monster="Dragon"))
        assert "Dragon" in s
        assert "Spawn" in s