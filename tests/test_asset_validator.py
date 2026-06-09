import pytest

from validators.asset_validator import validate_asset


def test_valid_ground_id():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile.ground = 817
    """
    valid, errors = validate_asset(lua)
    assert valid
    assert len(errors) == 0


def test_valid_addItem():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:addItem(9043)
    """
    valid, errors = validate_asset(lua)
    assert valid
    assert len(errors) == 0


def test_invalid_item_id():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:addItem(999999)
    """
    valid, errors = validate_asset(lua)
    assert not valid
    assert any("999999" in e for e in errors)


def test_invalid_ground_id():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile.ground = 999999
    """
    valid, errors = validate_asset(lua)
    assert not valid
    assert any("999999" in e for e in errors)