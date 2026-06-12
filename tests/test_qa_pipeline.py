from validators.qa_pipeline import QAPipeline


def test_qa_pipeline_valid_script():
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
    qa = QAPipeline()
    report = qa.run(lua)
    assert report["status"] == "success"
    assert len(report["errors"]) == 0
    for stage, result in report["stages"].items():
        assert result == "passed", f"Stage {stage} failed"


def test_qa_pipeline_forbidden_api():
    lua = """
    Map.addItem(Position(100,100,7),2160)
    """
    qa = QAPipeline()
    report = qa.run(lua)
    assert report["status"] == "failure"
    assert report["stages"]["rme_validator"] == "failed"
    # Pipeline should stop at RME validator
    assert "asset_validator" not in report["stages"]


def test_qa_pipeline_unknown_monster():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:addItem(9043)
    tile:setCreature("MonsterQueNoExiste", 60, Direction.SOUTH)
    """
    qa = QAPipeline()
    report = qa.run(lua)
    assert report["status"] == "failure"
    assert report["stages"]["rme_validator"] == "passed"
    assert report["stages"]["monster_validator"] == "failed"


def test_qa_pipeline_unknown_item():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile:addItem(999999)
    tile:setCreature("Frazzlemaw", 60, Direction.SOUTH)
    """
    qa = QAPipeline()
    report = qa.run(lua)
    assert report["status"] == "failure"
    assert report["stages"]["asset_validator"] == "failed"


def test_qa_pipeline_invalid_z():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,99)
    tile:addItem(9043)
    """
    qa = QAPipeline()
    report = qa.run(lua)
    assert report["status"] == "failure"
    assert report["stages"]["tile_validator"] == "failed"


def test_qa_pipeline_report_structure():
    lua = """
    app.transaction()
    local tile = map:getOrCreateTile(1000,1000,7)
    tile.ground = 817
    """
    qa = QAPipeline()
    report = qa.run(lua)
    assert "status" in report
    assert "errors" in report
    assert "stages" in report
    assert "rme_validator" in report["stages"]
    assert "asset_validator" in report["stages"]
    assert "monster_validator" in report["stages"]
    assert "tile_validator" in report["stages"]
