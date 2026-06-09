import pytest

from validators.rme_validator import (
    validate,
    RMEValidationError
)


# ---- Casos válidos ----

def test_valid_getOrCreateTile():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(100,100,7)
    tile.ground = 817
    """
    assert validate(lua)


def test_valid_addItem():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(100,100,7)
    tile:addItem(9043)
    """
    assert validate(lua)


def test_valid_setCreature():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(100,100,7)
    tile:setCreature("Dragon", 60, Direction.SOUTH)
    """
    assert validate(lua)


def test_valid_setSpawn():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(100,100,7)
    tile:setSpawn(60)
    """
    assert validate(lua)


def test_valid_borderize():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(100,100,7)
    tile:borderize()
    """
    assert validate(lua)


def test_valid_full_script():
    lua = """
    if not app.hasMap() then
        return
    end

    local map = app.map

    app.transaction()

    local tile = map:getOrCreateTile(1000,1000,7)
    tile.ground = 817
    tile:addItem(9043)
    tile:setCreature("Frazzlemaw", 60, Direction.SOUTH)
    tile:borderize()
    """
    assert validate(lua)


# ---- Casos inválidos ----

def test_invalid_Map_addItem():
    lua = """
    Map.addItem(Position(100,100,7),2160)
    """
    with pytest.raises(RMEValidationError):
        validate(lua)


def test_invalid_Map_addCreature():
    lua = """
    Map.addCreature("Dragon", Position(100,100,7))
    """
    with pytest.raises(RMEValidationError):
        validate(lua)


def test_invalid_Map_addNpc():
    lua = """
    Map.addNpc("Sam", Position(50,50,7))
    """
    with pytest.raises(RMEValidationError):
        validate(lua)


def test_invalid_Map_setTile():
    lua = """
    Map.setTile(100,100,7,415)
    """
    with pytest.raises(RMEValidationError):
        validate(lua)


def test_invalid_Position():
    lua = """
    local pos = Position(100,100,7)
    """
    with pytest.raises(RMEValidationError):
        validate(lua)


def test_invalid_Game_createTile():
    lua = """
    Game.createTile(100,100,7)
    """
    with pytest.raises(RMEValidationError):
        validate(lua)


def test_invalid_mixed():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(100,100,7)
    tile.ground = 817
    Map.addItem(200,200,7,415)
    """
    with pytest.raises(RMEValidationError):
        validate(lua)