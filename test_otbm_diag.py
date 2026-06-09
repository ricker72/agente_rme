"""Diagnostic script for OTBM byte range bug."""
import sys
sys.path.insert(0, '.')

from core.otbm.otbm_serializer import OtbmSerializer


class FakeTile:
    def __init__(self, x, y, z, ground=106, items=None, flags=0):
        self.x = x
        self.y = y
        self.z = z
        self.ground = ground
        self.items = items or []
        self.flags = flags
        self.spawn = None
        self.creature = None

    def to_dict(self):
        return {
            'x': self.x, 'y': self.y, 'z': self.z,
            'ground': self.ground, 'items': self.items, 'flags': self.flags,
        }


class FakeWorld:
    def __init__(self, tiles):
        self.tiles = tiles
        self.spawns = []
        self.cities = []
        self.waypoints = []
        self.structures = []
        self.regions = []


ser = OtbmSerializer()

# Test 1: tile with very large ground ID (e.g., 9999999)
world = FakeWorld({'0:0:7': FakeTile(0, 0, 7, ground=9999999)})
try:
    data = ser.serialize(world)
    print(f'TEST 1: OK ground=9999999 -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 1 FAIL: {type(e).__name__}: {e}')

# Test 2: tile with ground=0 (no ground)
world = FakeWorld({'0:0:7': FakeTile(0, 0, 7, ground=0)})
try:
    data = ser.serialize(world)
    print(f'TEST 2: OK ground=0 -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 2 FAIL: {type(e).__name__}: {e}')

# Test 3: tile with very large x (offset > 255 from base)
world = FakeWorld({'500:500:7': FakeTile(500, 500, 7, ground=106)})
try:
    data = ser.serialize(world)
    print(f'TEST 3: OK x=500 -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 3 FAIL: {type(e).__name__}: {e}')

# Test 4: tile with z=999 (out of byte range)
world = FakeWorld({'0:0:999': FakeTile(0, 0, 999, ground=106)})
try:
    data = ser.serialize(world)
    print(f'TEST 4: OK z=999 -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 4 FAIL: {type(e).__name__}: {e}')

# Test 5: tile with large spawntime interval
world = FakeWorld({})
world.tiles = {'0:0:7': FakeTile(0, 0, 7, ground=106)}
world.spawns = [{'x': 0, 'y': 0, 'z': 7, 'monster': 'Dragon', 'interval': 999999, 'radius': 999}]
try:
    data = ser.serialize(world)
    print(f'TEST 5: OK spawn=999999 -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 5 FAIL: {type(e).__name__}: {e}')

# Test 6: tile with city that has a very large temple coord
world = FakeWorld({})
world.tiles = {'0:0:7': FakeTile(0, 0, 7, ground=106)}
world.cities = [{'name': 'TestCity', 'temple_x': 99999, 'temple_y': 99999, 'temple_z': 7}]
try:
    data = ser.serialize(world)
    print(f'TEST 6: OK city large -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 6 FAIL: {type(e).__name__}: {e}')

# Test 7: empty world
world = FakeWorld({})
try:
    data = ser.serialize(world)
    print(f'TEST 7: OK empty world -> {len(data)} bytes')
except Exception as e:
    print(f'TEST 7 FAIL: {type(e).__name__}: {e}')
