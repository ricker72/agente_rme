import pytest

from core.assets.monster_indexer import MonsterIndexer


def test_index_fallback():
    indexer = MonsterIndexer()
    count = indexer.index_fallback_monsters()
    assert count > 0
    assert "Frazzlemaw" in indexer._monsters


def test_index_monsters_xml():
    indexer = MonsterIndexer()
    count = indexer.index_monsters_xml("monster - npc/monster.xml")
    assert count >= 1750
    assert "Frazzlemaw" in indexer._monsters


def test_get_monster():
    indexer = MonsterIndexer()
    indexer.index_fallback_monsters()
    monster = indexer.get_monster("Frazzlemaw")
    assert monster is not None
    assert monster["name"] == "Frazzlemaw"


def test_get_monster_case_insensitive():
    indexer = MonsterIndexer()
    indexer.index_fallback_monsters()
    monster = indexer.get_monster("frazzlemaw")
    assert monster is not None


def test_get_monster_not_found():
    indexer = MonsterIndexer()
    indexer.index_fallback_monsters()
    monster = indexer.get_monster("MonsterQueNoExiste999")
    assert monster is None


def test_all_monster_names():
    indexer = MonsterIndexer()
    indexer.index_fallback_monsters()
    names = indexer.all_monster_names()
    assert len(names) > 0
    assert "Frazzlemaw" in names


def test_fallback_includes_shrieker():
    indexer = MonsterIndexer()
    indexer.index_monsters_xml("monster - npc/monster.xml")
    assert indexer.get_monster("Shrieker") is not None


def test_to_dict_from_dict():
    indexer = MonsterIndexer()
    indexer.index_fallback_monsters()
    data = indexer.to_dict()
    assert "monsters" in data

    indexer2 = MonsterIndexer()
    indexer2.from_dict(data)
    assert indexer2.get_monster("Frazzlemaw") is not None


def test_xml_plus_fallback():
    """Ensure that XML indexing + fallback includes all monsters."""
    indexer = MonsterIndexer()
    indexer.index_monsters_xml("monster - npc/monster.xml")
    names = indexer.all_monster_names()
    assert "Frazzlemaw" in names
    assert "Shrieker" in names
    assert "Dragon" in names