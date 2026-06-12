from validators.tile_validator import validate_tile


def test_valid_tile():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    """
    valid, errors = validate_tile(lua)
    assert valid
    assert len(errors) == 0


def test_valid_edge_cases():
    lua = """
    app.transaction()
    local t1 = map:getOrCreateTile(0,0,0)
    local t2 = map:getOrCreateTile(65535,65535,15)
    """
    valid, errors = validate_tile(lua)
    assert valid


def test_invalid_z_negative():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,-1)
    """
    valid, errors = validate_tile(lua)
    assert not valid
    assert any("-1" in e for e in errors)


def test_invalid_z_too_high():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,99)
    """
    valid, errors = validate_tile(lua)
    assert not valid
    assert any("99" in e for e in errors)


def test_no_tile_calls():
    lua = """
    app.transaction()
    tile.ground = 817
    """
    valid, errors = validate_tile(lua)
    assert valid
    assert len(errors) == 0
