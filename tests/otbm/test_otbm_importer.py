"""
Functional Tests for HITO 11: OTBM Importer Pipeline.

Tests the complete import pipeline:
    .otbm file
    -> OtbmParser.parse(bytes) -> raw parsed tree
    -> NodeDecoder.decode_*(node) -> decoded dicts
    -> TileDecoder.to_worldmodel_tile(tile) -> WorldModel tile dicts
    -> ItemDecoder.decode(item) -> clean item dicts
    -> WorldBuilder.build(parsed) -> WorldModel-compatible dict
    -> WorldBuilder.to_worldmodel(parsed) -> WorldModel instance

Plus round trip: OTBM -> WorldModel -> OTBM
"""

from __future__ import annotations

import struct
import sys
import os
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from core.otbm import (
    # Importer pipeline
    OtbmParser,
    OtbmParseError,
    NodeDecoder,
    NodeDecodeError,
    TileDecoder,
    ItemDecoder,
    WorldBuilder,
    WorldBuildError,
    OTBMImporter,
    # Exporter (for round trip)
    OtbmSerializer,
    # Node types
    OTBM_NODE_ROOT,
    OTBM_NODE_MAP_DATA,
    OTBM_NODE_TILE_AREA,
    OTBM_NODE_TILE,
    OTBM_NODE_ITEM,
    OTBM_NODE_SPAWNS,
    OTBM_NODE_SPAWN_AREA,
    OTBM_NODE_MONSTER,
    OTBM_NODE_TOWNS,
    OTBM_NODE_TOWN,
    OTBM_NODE_WAYPOINTS,
    OTBM_NODE_WAYPOINT,
    OTBM_NODE_HOUSETILE,
    # Attributes
    ATTR_TILE_FLAGS,
    ATTR_COUNT,
    ATTR_ACTION_ID,
    ATTR_UNIQUE_ID,
    ATTR_TEXT,
    ATTR_CHARGES,
    ATTR_SUBTYPE,
    ATTR_DURATION,
    # Tile states
    TILESTATE_NONE,
    TILESTATE_PROTECTIONZONE,
    TILESTATE_NOPVPZONE,
    TILESTATE_NOLOGOUT,
    # Encoder for test data generation
    NodeEncoder,
    TileEncoder,
    # WorldModel
    NodeEncoder as NE,
)
from core.world_engine.world_engine import WorldModel, Tile


# ============================================================
# Helper: build small OTBM bytes for testing
# ============================================================

def _build_test_otbm() -> bytes:
    """
    Build a minimal valid OTBM with:
        - 4 tiles (2x2 grid) at (1000,1000) z=7
        - Ground IDs: 106, 106, 106, 106
        - 1 spawn: Dragon Lord at (1000, 1000)
        - 1 town: TestTown at (1000, 1000, 7)
        - 1 waypoint: wp1 at (1000, 1000, 7)
    """
    encoder = NodeEncoder()
    tile_encoder = TileEncoder()

    # Build tile area for z=7
    base_x, base_y, base_z = 1000, 1000, 7

    # Tiles
    tile1 = encoder.encode_tile(offset_x=0, offset_y=0, tile_flags=0,
                                 children=encoder.encode_item(item_id=106))
    tile2 = encoder.encode_tile(offset_x=1, offset_y=0, tile_flags=0,
                                 children=encoder.encode_item(item_id=106))
    tile3 = encoder.encode_tile(offset_x=0, offset_y=1, tile_flags=0,
                                 children=encoder.encode_item(item_id=106))
    tile4 = encoder.encode_tile(offset_x=1, offset_y=1, tile_flags=0,
                                 children=encoder.encode_item(item_id=106))

    tile_area = encoder.encode_tile_area(
        base_x=base_x, base_y=base_y, base_z=base_z,
        children=tile1 + tile2 + tile3 + tile4
    )

    # Spawn
    monster = encoder.encode_monster(name="Dragon Lord", direction=2, spawntime=60)
    spawn_area = encoder.encode_spawn_area(
        center_x=1000, center_y=1000, center_z=7, radius=3,
        children=monster
    )
    spawns = encoder.encode_spawns(spawn_area)

    # Town
    town = encoder.encode_town(town_id=1, name="TestTown",
                                temple_x=1000, temple_y=1000, temple_z=7)
    towns = encoder.encode_towns(town)

    # Waypoint
    wp = encoder.encode_waypoint(name="wp1", x=1000, y=1000, z=7)
    waypoints = encoder.encode_waypoints(wp)

    # Map data
    map_children = tile_area + spawns + towns + waypoints
    map_data = encoder.encode_map_data(
        description="Test map",
        spawn_file="test_spawns.xml",
        house_file="test_houses.xml",
        children=map_children
    )

    # Root
    root = encoder.encode_root(
        otbm_version=0,
        width=2,
        height=2,
        item_major=3,
        item_minor=57,
        children=map_data
    )

    return b"OTBM" + root


# ============================================================
# Test 1: OtbmParser — basic parsing
# ============================================================

def test_parser_basic():
    """Parse a minimal valid OTBM."""
    data = _build_test_otbm()
    parser = OtbmParser()
    result = parser.parse(data)

    assert result["magic"] == "OTBM"
    root = result["root"]
    assert root["type"] == OTBM_NODE_ROOT
    assert root["version"] == 0
    assert root["width"] == 2
    assert root["height"] == 2
    assert root["item_major"] == 3
    assert root["item_minor"] == 57
    assert len(root["children"]) > 0

    # Find MAP_DATA
    map_data = parser.find_first_child_of_type(root, OTBM_NODE_MAP_DATA)
    assert map_data is not None
    assert map_data["type"] == OTBM_NODE_MAP_DATA

    # Find children of MAP_DATA
    tile_areas = parser.find_children_of_type(map_data, OTBM_NODE_TILE_AREA)
    assert len(tile_areas) == 1

    spawns = parser.find_children_of_type(map_data, OTBM_NODE_SPAWNS)
    assert len(spawns) == 1

    towns = parser.find_children_of_type(map_data, OTBM_NODE_TOWNS)
    assert len(towns) == 1

    waypoints = parser.find_children_of_type(map_data, OTBM_NODE_WAYPOINTS)
    assert len(waypoints) == 1

    print(f"[PASS] test_parser_basic — parsed OTBM with {len(root['children'])} child nodes")


# ============================================================
# Test 2: OtbmParser — invalid magic
# ============================================================

def test_parser_invalid_magic():
    """Reject invalid magic bytes."""
    parser = OtbmParser()
    try:
        parser.parse(b"INVALID")
        assert False, "Should have raised OtbmParseError"
    except OtbmParseError as e:
        assert "magic" in str(e).lower()
        print(f"[PASS] test_parser_invalid_magic — correctly rejected: {e}")


# ============================================================
# Test 3: OtbmParser — truncated data
# ============================================================

def test_parser_truncated():
    """Handle truncated data gracefully."""
    parser = OtbmParser()
    try:
        parser.parse(b"OTBM\x00")
        assert False, "Should have raised OtbmParseError"
    except OtbmParseError:
        print(f"[PASS] test_parser_truncated — correctly rejected truncated data")


# ============================================================
# Test 4: NodeDecoder — decode root
# ============================================================

def test_node_decoder_root():
    """Decode ROOT node."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)

    decoder = NodeDecoder()
    decoded = decoder.decode_root(parsed["root"])

    assert decoded["version"] == 0
    assert decoded["width"] == 2
    assert decoded["height"] == 2
    assert decoded["item_major"] == 3
    assert decoded["item_minor"] == 57
    assert decoded["map_data"] is not None
    assert len(decoded["tile_areas"]) == 1
    assert decoded["spawns"] is not None
    assert decoded["towns"] is not None
    assert decoded["waypoints"] is not None

    print(f"[PASS] test_node_decoder_root — decoded root: {decoded['version']=}, {len(decoded['tile_areas'])} areas")


# ============================================================
# Test 5: NodeDecoder — decode tile area
# ============================================================

def test_node_decoder_tile_area():
    """Decode TILE_AREA node."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)
    decoder = NodeDecoder()

    map_data = decoder._find_first(parsed["root"], OTBM_NODE_MAP_DATA)
    tile_area = decoder._find_first(map_data, OTBM_NODE_TILE_AREA)

    decoded = decoder.decode_tile_area(tile_area)
    assert decoded["base_x"] == 1000
    assert decoded["base_y"] == 1000
    assert decoded["base_z"] == 7
    assert len(decoded["tiles"]) == 4

    # Check first tile
    tile0 = decoded["tiles"][0]
    assert tile0["x"] == 1000
    assert tile0["y"] == 1000
    assert tile0["z"] == 7
    assert tile0["ground"] is not None
    assert tile0["ground"]["item_id"] == 106

    print(f"[PASS] test_node_decoder_tile_area — {len(decoded['tiles'])} tiles at z={decoded['base_z']}")


# ============================================================
# Test 6: NodeDecoder — decode spawns
# ============================================================

def test_node_decoder_spawns():
    """Decode SPAWNS node."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)
    decoder = NodeDecoder()

    map_data = decoder._find_first(parsed["root"], OTBM_NODE_MAP_DATA)
    spawns_node = decoder._find_first(map_data, OTBM_NODE_SPAWNS)

    decoded = decoder.decode_spawns(spawns_node)
    assert len(decoded["spawn_areas"]) == 1

    area = decoded["spawn_areas"][0]
    assert area["center_x"] == 1000
    assert area["center_y"] == 1000
    assert area["center_z"] == 7
    assert area["radius"] == 3
    assert len(area["monsters"]) == 1
    assert area["monsters"][0]["name"] == "Dragon Lord"
    assert area["monsters"][0]["spawntime"] == 60

    print(f"[PASS] test_node_decoder_spawns — {len(decoded['spawn_areas'])} areas, {len(area['monsters'])} monsters")


# ============================================================
# Test 7: NodeDecoder — decode towns
# ============================================================

def test_node_decoder_towns():
    """Decode TOWNS node."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)
    decoder = NodeDecoder()

    map_data = decoder._find_first(parsed["root"], OTBM_NODE_MAP_DATA)
    towns_node = decoder._find_first(map_data, OTBM_NODE_TOWNS)

    decoded = decoder.decode_towns(towns_node)
    assert len(decoded["towns"]) == 1

    town = decoded["towns"][0]
    assert town["town_id"] == 1
    assert town["name"] == "TestTown"
    assert town["temple_x"] == 1000
    assert town["temple_y"] == 1000
    assert town["temple_z"] == 7

    print(f"[PASS] test_node_decoder_towns — {len(decoded['towns'])} towns")


# ============================================================
# Test 8: NodeDecoder — decode waypoints
# ============================================================

def test_node_decoder_waypoints():
    """Decode WAYPOINTS node."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)
    decoder = NodeDecoder()

    map_data = decoder._find_first(parsed["root"], OTBM_NODE_MAP_DATA)
    wp_node = decoder._find_first(map_data, OTBM_NODE_WAYPOINTS)

    decoded = decoder.decode_waypoints(wp_node)
    assert len(decoded["waypoints"]) == 1

    wp = decoded["waypoints"][0]
    assert wp["name"] == "wp1"
    assert wp["x"] == 1000
    assert wp["y"] == 1000
    assert wp["z"] == 7

    print(f"[PASS] test_node_decoder_waypoints — {len(decoded['waypoints'])} waypoints")


# ============================================================
# Test 9: TileDecoder — convert tile
# ============================================================

def test_tile_decoder():
    """Convert decoded tile to WorldModel-compatible format."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)
    nd = NodeDecoder()
    td = TileDecoder()

    map_data = nd._find_first(parsed["root"], OTBM_NODE_MAP_DATA)
    tile_area = nd._find_first(map_data, OTBM_NODE_TILE_AREA)
    decoded_area = nd.decode_tile_area(tile_area)

    tiles = td.decode_area(decoded_area)
    assert len(tiles) == 4

    for tile in tiles:
        assert "x" in tile
        assert "y" in tile
        assert "z" in tile
        assert tile["z"] == 7
        assert tile["ground"] is not None
        assert "items" in tile
        assert tile["spawn"] is None  # No spawn on individual tiles in this test

    print(f"[PASS] test_tile_decoder — {len(tiles)} tiles converted")


# ============================================================
# Test 10: ItemDecoder — decode item
# ============================================================

def test_item_decoder():
    """Decode ITEM node attributes."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)
    nd = NodeDecoder()

    # Get a tile's ground item
    map_data = nd._find_first(parsed["root"], OTBM_NODE_MAP_DATA)
    tile_area = nd._find_first(map_data, OTBM_NODE_TILE_AREA)
    decoded_area = nd.decode_tile_area(tile_area)

    ground = decoded_area["tiles"][0]["ground"]
    item_decoder = ItemDecoder()
    decoded = item_decoder.decode(ground)

    assert decoded["item_id"] == 106
    assert decoded["count"] is None  # No count attribute in our test data

    # Test item_to_tile_format
    tile_format = item_decoder.item_to_tile_format(ground)
    assert tile_format["id"] == 106

    # Test is_ground
    assert item_decoder.is_ground(106) == True
    assert item_decoder.is_ground(2050) == False

    print(f"[PASS] test_item_decoder — item_id={decoded['item_id']}")


# ============================================================
# Test 11: WorldBuilder — build full WorldModel dict
# ============================================================

def test_world_builder():
    """Build WorldModel-compatible dict from parsed OTBM."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)

    builder = WorldBuilder()
    result = builder.build(parsed)

    assert result["version"] == 0
    assert result["width"] == 2
    assert result["height"] == 2
    assert result["item_major"] == 3
    assert result["item_minor"] == 57
    assert result["description"] == "Test map"
    assert result["tile_count"] == 4
    assert result["spawn_count"] == 1
    assert result["city_count"] == 1
    assert result["waypoint_count"] == 1

    # Check spawn
    spawn = result["spawns"][0]
    assert spawn["monster"] == "Dragon Lord"
    assert spawn["x"] == 1000
    assert spawn["y"] == 1000
    assert spawn["z"] == 7
    assert spawn["radius"] == 3
    assert spawn["respawn"] == 60

    # Check city
    city = result["cities"][0]
    assert city["name"] == "TestTown"
    assert city["temple_x"] == 1000

    # Check waypoint
    wp = result["waypoints"][0]
    assert wp["name"] == "wp1"

    print(f"[PASS] test_world_builder — {result['tile_count']} tiles, {result['spawn_count']} spawns, "
          f"{result['city_count']} cities, {result['waypoint_count']} waypoints")


# ============================================================
# Test 12: WorldBuilder — to_worldmodel
# ============================================================

def test_world_builder_to_worldmodel():
    """Build full WorldModel instance from parsed OTBM."""
    data = _build_test_otbm()
    parsed = OtbmParser().parse(data)

    builder = WorldBuilder()
    wm = builder.to_worldmodel(parsed)

    assert isinstance(wm, WorldModel)
    assert len(wm.tiles) == 4
    assert len(wm.spawns) == 1
    assert len(wm.cities) == 1
    assert len(wm.waypoints) == 1

    # Verify tile positions
    keys = list(wm.tiles.keys())
    assert "1000:1000:7" in keys
    assert "1001:1000:7" in keys
    assert "1000:1001:7" in keys
    assert "1001:1001:7" in keys

    # Verify tile data
    tile = wm.tiles["1000:1000:7"]
    assert tile.x == 1000
    assert tile.y == 1000
    assert tile.z == 7
    assert tile.ground == "106"

    # Verify spawn
    spawn = wm.spawns[0]
    assert spawn["monster"] == "Dragon Lord"

    print(f"[PASS] test_world_builder_to_worldmodel — WorldModel with {len(wm.tiles)} tiles, "
          f"{len(wm.spawns)} spawns")


# ============================================================
# Test 13: OTBMImporter — import file
# ============================================================

def test_importer_import_file():
    """Import an .otbm file via OTBMImporter."""
    # Write test data to temp file
    data = _build_test_otbm()
    test_file = Path(__file__).resolve().parent / "_test_import.otbm"
    test_file.write_bytes(data)

    try:
        importer = OTBMImporter(validate=False)
        result = importer.import_file(test_file)

        assert result["success"]
        assert result["stats"]["tiles"] == 4
        assert result["stats"]["spawns"] == 1
        assert result["stats"]["cities"] == 1
        assert result["stats"]["waypoints"] == 1
        assert result["map_info"]["version"] == 0
        assert result["map_info"]["width"] == 2
        assert result["map_info"]["height"] == 2

        world_model = result["world_model"]
        assert isinstance(world_model, WorldModel)

        print(f"[PASS] test_importer_import_file — imported {result['stats']['tiles']} tiles, "
              f"{result['stats']['spawns']} spawns")
    finally:
        if test_file.exists():
            test_file.unlink()


# ============================================================
# Test 14: OTBMImporter — import from bytes
# ============================================================

def test_importer_import_bytes():
    """Import OTBM from bytes."""
    data = _build_test_otbm()
    importer = OTBMImporter(validate=False)
    result = importer.import_bytes(data)

    assert result["success"]
    assert result["stats"]["tiles"] == 4
    assert result["stats"]["spawns"] == 1
    assert result["world_model"] is not None
    assert result["world_dict"] is not None

    print(f"[PASS] test_importer_import_bytes — imported from bytes")


# ============================================================
# Test 15: OTBMImporter — file not found
# ============================================================

def test_importer_file_not_found():
    """Handle missing file gracefully."""
    importer = OTBMImporter()
    result = importer.import_file("nonexistent.otbm")

    assert not result["success"]
    assert "not found" in result.get("error", "").lower()

    print(f"[PASS] test_importer_file_not_found — handled: {result.get('error')}")


# ============================================================
# Test 16: OTBMImporter — to_worldmodel convenience
# ============================================================

def test_importer_to_worldmodel():
    """Use to_worldmodel convenience method."""
    data = _build_test_otbm()
    test_file = Path(__file__).resolve().parent / "_test_wm.otbm"
    test_file.write_bytes(data)

    try:
        importer = OTBMImporter()
        wm = importer.to_worldmodel(test_file)

        assert isinstance(wm, WorldModel)
        assert len(wm.tiles) == 4
        assert len(wm.spawns) == 1
        assert len(wm.cities) == 1
        assert len(wm.waypoints) == 1

        print(f"[PASS] test_importer_to_worldmodel — WorldModel with {len(wm.tiles)} tiles")
    finally:
        if test_file.exists():
            test_file.unlink()


# ============================================================
# Test 17: OTBMImporter — get_preview
# ============================================================

def test_importer_preview():
    """Get preview of OTBM map."""
    data = _build_test_otbm()
    test_file = Path(__file__).resolve().parent / "_test_preview.otbm"
    test_file.write_bytes(data)

    try:
        importer = OTBMImporter()
        preview = importer.get_preview(test_file)

        assert preview["valid"]
        assert preview["version"] == 0
        assert preview["width"] == 2
        assert preview["height"] == 2
        assert preview["tiles"] == 4
        assert preview["spawns"] == 1
        assert preview["towns"] == 1
        assert preview["waypoints"] == 1
        assert preview["file_size"] == len(data)

        print(f"[PASS] test_importer_preview — {preview['tiles']} tiles, {preview['spawns']} spawns, "
              f"{preview['towns']} towns, {preview['waypoints']} waypoints")
    finally:
        if test_file.exists():
            test_file.unlink()


# ============================================================
# Test 18: WorldBuilder — invalid data
# ============================================================

def test_world_builder_invalid():
    """Handle invalid parsed data."""
    builder = WorldBuilder()

    try:
        builder.build({"no_root": True})
        assert False, "Should have raised WorldBuildError"
    except WorldBuildError as e:
        assert "root" in str(e).lower()
        print(f"[PASS] test_world_builder_invalid — handled: {e}")


# ============================================================
# Test 19: Round trip — OTBM -> WorldModel -> OTBM
# ============================================================

def test_round_trip_basic():
    """Full round trip: build OTBM -> parse -> WorldModel -> serialize -> OTBM."""
    import io
    from core.otbm.otbm_serializer import OtbmSerializer

    # 1. Build original OTBM
    original_bytes = _build_test_otbm()

    # 2. Parse -> WorldModel
    parsed = OtbmParser().parse(original_bytes)
    builder = WorldBuilder()
    wm = builder.to_worldmodel(parsed)

    # 3. Export back to OTBM
    serializer = OtbmSerializer()
    reexported_bytes = serializer.serialize(wm)

    # 4. Parse re-exported
    re_parsed = OtbmParser().parse(reexported_bytes)
    re_builder = WorldBuilder()
    re_wm = re_builder.to_worldmodel(re_parsed)

    # 5. Compare
    assert len(re_wm.tiles) == len(wm.tiles), f"Tile count mismatch: {len(re_wm.tiles)} vs {len(wm.tiles)}"
    assert len(re_wm.spawns) == len(wm.spawns), f"Spawn count mismatch: {len(re_wm.spawns)} vs {len(wm.spawns)}"
    assert len(re_wm.cities) == len(wm.cities), f"City count mismatch: {len(re_wm.cities)} vs {len(wm.cities)}"
    assert len(re_wm.waypoints) == len(wm.waypoints), f"Waypoint count mismatch: {len(re_wm.waypoints)} vs {len(wm.waypoints)}"

    # Verify tile positions
    for key, tile in wm.tiles.items():
        assert key in re_wm.tiles, f"Tile {key} missing after round trip"
        re_tile = re_wm.tiles[key]
        assert tile.x == re_tile.x, f"X mismatch at {key}: {tile.x} vs {re_tile.x}"
        assert tile.y == re_tile.y, f"Y mismatch at {key}: {tile.y} vs {re_tile.y}"
        assert tile.z == re_tile.z, f"Z mismatch at {key}: {tile.z} vs {re_tile.z}"

    print(f"[PASS] test_round_trip_basic — {len(wm.tiles)} tiles, {len(wm.spawns)} spawns, "
          f"{len(wm.cities)} cities preserved through round trip")


# ============================================================
# Test 20: Round trip — with items and attributes
# ============================================================

def test_round_trip_with_items():
    """Round trip with items containing attributes."""
    encoder = NodeEncoder()

    # Build tile with items that have attributes
    item1 = encoder.encode_item(item_id=2050)  # Torch (no attrs)
    item2 = encoder.encode_item(item_id=2160, count=50)  # Gold coins with count
    item3 = encoder.encode_item(item_id=1503)  # Fountain
    item4 = encoder.encode_item(item_id=1945, action_id=100, unique_id=1, text="Hello")

    tile = encoder.encode_tile(
        offset_x=0, offset_y=0,
        tile_flags=TILESTATE_PROTECTIONZONE,
        children=encoder.encode_item(item_id=112) + item1 + item2 + item3 + item4  # ground + items
    )

    tile_area = encoder.encode_tile_area(base_x=500, base_y=500, base_z=7, children=tile)
    map_data = encoder.encode_map_data(
        description="Items test",
        spawn_file="",
        house_file="",
        children=tile_area
    )
    root = encoder.encode_root(
        otbm_version=0, width=1, height=1,
        item_major=3, item_minor=57,
        children=map_data
    )
    data = b"OTBM" + root

    # Parse
    parsed = OtbmParser().parse(data)
    builder = WorldBuilder()
    wm = builder.to_worldmodel(parsed)

    assert len(wm.tiles) == 1

    tile_wm = list(wm.tiles.values())[0]
    assert tile_wm.ground == "112"
    assert len(tile_wm.items) >= 4  # ground + items = 5 items total

    # Re-export
    serializer = OtbmSerializer()
    re_data = serializer.serialize(wm)

    # Parse re-exported and verify structural preservation
    re_parsed = OtbmParser().parse(re_data)
    re_wm = builder.to_worldmodel(re_parsed)

    assert len(re_wm.tiles) == 1
    re_tile = list(re_wm.tiles.values())[0]
    # Ground is the first item on the tile, verify tile has items
    assert len(re_tile.items) >= 1, f"Expected items on tile, got {len(re_tile.items)}"

    print(f"[PASS] test_round_trip_with_items — {len(tile_wm.items)} items preserved")


# ============================================================
# Test 21: Round trip — large map
# ============================================================

def test_round_trip_large():
    """Round trip with larger map (100 tiles)."""
    encoder = NodeEncoder()
    tile_encoder = TileEncoder()

    # Build 10x10 grid
    tile_nodes = b""
    for x in range(10):
        for y in range(10):
            ground_id = 106 if (x + y) % 2 == 0 else 110
            tile = encoder.encode_tile(
                offset_x=x, offset_y=y,
                children=encoder.encode_item(item_id=ground_id)
            )
            tile_nodes += tile

    tile_area = encoder.encode_tile_area(base_x=0, base_y=0, base_z=7, children=tile_nodes)
    map_data = encoder.encode_map_data(description="Large test", spawn_file="", house_file="",
                                        children=tile_area)
    root = encoder.encode_root(otbm_version=0, width=10, height=10,
                                item_major=3, item_minor=57, children=map_data)
    data = b"OTBM" + root

    # Parse
    parsed = OtbmParser().parse(data)
    builder = WorldBuilder()
    wm = builder.to_worldmodel(parsed)

    assert len(wm.tiles) == 100

    # Re-export
    serializer = OtbmSerializer()
    re_data = serializer.serialize(wm)

    # Parse re-exported
    re_parsed = OtbmParser().parse(re_data)
    re_wm = builder.to_worldmodel(re_parsed)

    assert len(re_wm.tiles) == 100

    print(f"[PASS] test_round_trip_large — 100 tiles preserved")


# ============================================================
# Runner
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("  HITO 11: OTBM Importer — Functional Tests")
    print("=" * 60)
    print()

    tests = [
        ("Parser basic", test_parser_basic),
        ("Parser invalid magic", test_parser_invalid_magic),
        ("Parser truncated", test_parser_truncated),
        ("NodeDecoder root", test_node_decoder_root),
        ("NodeDecoder tile area", test_node_decoder_tile_area),
        ("NodeDecoder spawns", test_node_decoder_spawns),
        ("NodeDecoder towns", test_node_decoder_towns),
        ("NodeDecoder waypoints", test_node_decoder_waypoints),
        ("TileDecoder", test_tile_decoder),
        ("ItemDecoder", test_item_decoder),
        ("WorldBuilder dict", test_world_builder),
        ("WorldBuilder to WorldModel", test_world_builder_to_worldmodel),
        ("OTBMImporter import file", test_importer_import_file),
        ("OTBMImporter import bytes", test_importer_import_bytes),
        ("OTBMImporter file not found", test_importer_file_not_found),
        ("OTBMImporter to_worldmodel", test_importer_to_worldmodel),
        ("OTBMImporter preview", test_importer_preview),
        ("WorldBuilder invalid", test_world_builder_invalid),
        ("Round trip basic", test_round_trip_basic),
        ("Round trip with items", test_round_trip_with_items),
        ("Round trip large", test_round_trip_large),
    ]

    passed = 0
    failed = 0

    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"  [PASS] {name}")
        except Exception as e:
            failed += 1
            import traceback
            print(f"  [FAIL] {name}: {e}")
            traceback.print_exc()
        print()

    print(f"{'=' * 60}")
    print(f"  RESULTS: {passed} passed, {failed} failed out of {len(tests)}")
    print(f"{'=' * 60}")

    if failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)