from core.assets.item_indexer import ItemIndexer


def test_index_known_items():
    indexer = ItemIndexer()
    count = indexer.index_known_items()
    assert count > 0
    assert len(indexer.all_items()) > 0


def test_get_item():
    indexer = ItemIndexer()
    indexer.index_known_items()
    item = indexer.get_item(9043)
    assert item is not None
    assert item["name"] == "flower"


def test_get_item_not_found():
    indexer = ItemIndexer()
    indexer.index_known_items()
    item = indexer.get_item(999999)
    assert item is None


def test_get_item_by_name():
    indexer = ItemIndexer()
    indexer.index_known_items()
    item = indexer.get_item_by_name("grass")
    assert item is not None
    assert item["id"] == 415


def test_get_item_by_name_case_insensitive():
    indexer = ItemIndexer()
    indexer.index_known_items()
    item = indexer.get_item_by_name("GRASS")
    assert item is not None


def test_all_items():
    indexer = ItemIndexer()
    indexer.index_known_items()
    items = indexer.all_items()
    assert len(items) == len(indexer._items)


def test_to_dict_from_dict():
    indexer = ItemIndexer()
    indexer.index_known_items()
    data = indexer.to_dict()
    assert "items" in data

    indexer2 = ItemIndexer()
    indexer2.from_dict(data)
    assert indexer2.get_item(9043) is not None


def test_classify_ground():
    cat = ItemIndexer._classify("grass tile", "")
    assert cat == "ground"


def test_classify_wall():
    cat = ItemIndexer._classify("stone wall", "")
    assert cat == "wall"


def test_classify_decoration():
    cat = ItemIndexer._classify("vase", "")
    assert cat == "decoration"


def test_classify_unknown():
    cat = ItemIndexer._classify("gold coin", "")
    assert cat == "item"
