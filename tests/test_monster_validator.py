from validators.monster_validator import validate_monster


def test_valid_monster():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:setCreature("Frazzlemaw", 60, Direction.SOUTH)
    """
    valid, errors = validate_monster(lua)
    assert valid
    assert len(errors) == 0


def test_valid_monster_from_xml():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:setCreature("Dragon", 60, Direction.SOUTH)
    """
    valid, errors = validate_monster(lua)
    assert valid


def test_unknown_monster():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:setCreature("MonsterQueNoExiste", 60, Direction.SOUTH)
    """
    valid, errors = validate_monster(lua)
    assert not valid
    assert any("MonsterQueNoExiste" in e for e in errors)


def test_multiple_monsters_some_invalid():
    lua = """
    app.transaction()
    local t1 = map:getOrCreateTile(1000,1000,7)
    t1:setCreature("Frazzlemaw", 60, Direction.SOUTH)
    local t2 = map:getOrCreateTile(1010,1000,7)
    t2:setCreature("UnknownMonsterX", 60, Direction.SOUTH)
    """
    valid, errors = validate_monster(lua)
    assert not valid
    assert any("UnknownMonsterX" in e for e in errors)


def test_no_creature_call():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile.ground = 817
    """
    valid, errors = validate_monster(lua)
    assert valid
    assert len(errors) == 0
