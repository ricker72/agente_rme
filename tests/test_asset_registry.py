import pytest

from core.assets.asset_registry import AssetRegistry


@pytest.fixture
def registry():
    reg = AssetRegistry()
    reg.load(monster_path="monster - npc/monster.xml")
    return reg


def test_registry_loaded(registry):
    assert registry.is_loaded()


def test_item_exists(registry):
    assert registry.item_exists(9043)
    assert registry.item_exists(2160)
    assert registry.item_exists(817)
    assert registry.item_exists(1495)


def test_item_not_exists(registry):
    assert not registry.item_exists(999999)


def test_get_item(registry):
    item = registry.get_item(9043)
    assert item is not None
    assert item["name"] == "flower"


def test_monster_exists(registry):
    assert registry.monster_exists("Frazzlemaw")
    assert registry.monster_exists("Dragon")
    assert registry.monster_exists("Shrieker")
    assert registry.monster_exists("Rat")


def test_monster_not_exists(registry):
    assert not registry.monster_exists("MonsterQueNoExiste999")
    assert not registry.monster_exists("")


def test_get_monster(registry):
    monster = registry.get_monster("Frazzlemaw")
    assert monster is not None


def test_get_all_monsters(registry):
    names = registry.get_all_monsters()
    assert len(names) > 100
    assert "Frazzlemaw" in names
    assert "Shrieker" in names


def test_grounds(registry):
    grounds = registry.get_grounds()
    assert len(grounds) > 0
    assert 817 in grounds
    assert 415 in grounds


def test_walls(registry):
    walls = registry.get_walls()
    assert len(walls) > 0
    assert 1495 in walls


def test_decorations(registry):
    decorations = registry.get_decorations()
    assert len(decorations) > 0
    assert 1700 in decorations


def test_is_ground(registry):
    assert registry.is_ground(817)
    assert registry.is_ground(415)


def test_is_wall(registry):
    assert registry.is_wall(1495)


def test_is_decoration(registry):
    assert registry.is_decoration(1700)


def test_summary(registry):
    summary = registry.summary()
    assert summary["items"] > 0
    assert summary["monsters"] > 100
