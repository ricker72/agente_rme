from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


@dataclass
class IndexedItem:
    """An indexed Tibia item with all known attributes."""
    id: int
    name: str = ""
    article: str = ""
    type_name: str = ""  # items.xml type: "ground", "container", "key", etc.
    attributes: Dict[str, Any] = field(default_factory=dict)
    sprite_ids: List[int] = field(default_factory=list)
    category: str = "unknown"
    theme_tags: Set[str] = field(default_factory=set)
    weight: int = 0
    value: int = 0
    stackable: bool = False
    weapon_type: str = ""
    armor_value: int = 0
    attack_value: int = 0
    defense_value: int = 0
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type_name": self.type_name,
            "category": self.category,
            "theme_tags": list(self.theme_tags),
            "weight": self.weight,
            "value": self.value,
            "stackable": self.stackable,
            "sprite_ids": self.sprite_ids,
        }


@dataclass
class IndexedMonster:
    """An indexed Tibia monster with all known attributes."""
    name: str
    race: str = ""
    experience: int = 0
    speed: int = 0
    health: int = 0
    look_type: int = 0
    corpse_id: int = 0
    theme_tags: Set[str] = field(default_factory=set)
    elements: Dict[str, int] = field(default_factory=dict)  # damage modifiers
    loot: List[Dict[str, Any]] = field(default_factory=list)
    voices: List[str] = field(default_factory=list)
    immunities: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "race": self.race,
            "experience": self.experience,
            "health": self.health,
            "speed": self.speed,
            "theme_tags": list(self.theme_tags),
            "elements": self.elements,
            "loot_count": len(self.loot),
        }


class AssetIndexer:
    """
    Indexes Tibia game assets (items, monsters, NPCs, sprites) into
    a searchable knowledge base.

    Reads:
      - items.xml  → IndexedItem entries
      - monsters/  → IndexedMonster entries
      - NPC files  → basic NPC registry
      - Theme templates → theme-to-item associations

    Provides fast lookup by ID, name, category, and theme tag.
    """

    # Known ground item substrings for initial classification
    GROUND_KEYWORDS = {
        "floor", "ground", "grass", "dirt", "sand", "stone", "pavement",
        "road", "marble", "wooden floor", "tile", "earth", "gravel",
        "snow", "ice floor", "lava", "water", "swamp", "mud",
        "carpet", "plank", "cobblestone", "parchment",
    }

    # Known wall/blocking item substrings
    WALL_KEYWORDS = {
        "wall", "fence", "window", "door", "gate", "bars",
        "pillar", "column", "archway", "tunnel",
    }

    # Known decoration substrings
    DECORATION_KEYWORDS = {
        "torch", "lamp", "candle", "statue", "vase", "urn",
        "painting", "tapestry", "banner", "flag", "plant",
        "flower", "bush", "tree", "fern", "mushroom", "reed",
        "rock", "stone", "crystal", "gem", "pearl",
        "skull", "bone", "skeleton decoration",
        "barrel", "crate", "chest", "box", "barrel",
        "chair", "table", "bed", "bench", "throne",
        "sign", "notice", "board", "blackboard",
        "fountain", "well", "trough",
        "book", "scroll", "parchment", "letter",
        "instrument", "harp", "lute", "drum",
        "trophy", "trophy", "statuette",
        "dustbin", "rubbish",
    }

    # Nature-specific substrings
    NATURE_KEYWORDS = {
        "tree", "bush", "flower", "grass tuft", "reed", "fern",
        "mushroom", "cactus", "vine", "root", "leaf", "branch",
        "log", "stump", "moss", "lichen", "algae",
        "rock", "stone", "pebble", "boulder", "stalagmite", "stalactite",
        "water", "river", "pond", "lake", "waterfall",
    }

    # Magic/effect items
    MAGIC_KEYWORDS = {
        "rune", "spell", "scroll", "wand", "rod", "staff",
        "potion", "elixir", "fluid", "antidote",
        "ring", "amulet", "necklace", "orb", "crystal ball",
        "magic", "enchanted", "holy", "cursed", "blessed",
        "fire field", "energy field", "poison field",
    }

    # Library/quest items
    LIBRARY_KEYWORDS = {
        "book", "parchment", "scroll", "document", "letter",
        "note", "diary", "journal", "tome", "manuscript",
        "library", "bookshelf", "bookcase",
    }

    def __init__(self):
        self._items: Dict[int, IndexedItem] = {}
        self._items_by_name: Dict[str, IndexedItem] = {}
        self._monsters: Dict[str, IndexedMonster] = {}
        self._npcs: Dict[str, Dict[str, Any]] = {}
        self._theme_items: Dict[str, Set[int]] = {}  # theme → set of item IDs
        self._theme_monsters: Dict[str, Set[str]] = {}  # theme → set of monster names
        self._indexed = False

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_items_xml(self, path: str | Path) -> int:
        """Index items from an items.xml file. Returns count indexed."""
        root = ET.parse(str(path)).getroot()
        count = 0

        for elem in root.findall("item"):
            item_id = int(elem.get("id", 0))
            name = elem.get("name", "")
            article = elem.get("article", "")
            type_name = elem.get("type", "")

            if item_id == 0:
                continue

            # Parse attributes
            item = IndexedItem(
                id=item_id,
                name=name,
                article=article,
                type_name=type_name,
            )

            # Attributes sub-element
            attr_elem = elem.find("attribute")
            if attr_elem is not None:
                for a in attr_elem:
                    key = a.get("key", "")
                    val = a.get("value", "")
                    item.attributes[key] = val

                    if key == "weight":
                        try:
                            item.weight = int(val)
                        except ValueError:
                            pass
                    elif key == "armor":
                        try:
                            item.armor_value = int(val)
                        except ValueError:
                            pass
                    elif key == "attack":
                        try:
                            item.attack_value = int(val)
                        except ValueError:
                            pass
                    elif key == "defense":
                        try:
                            item.defense_value = int(val)
                        except ValueError:
                            pass
                    elif key == "description":
                        item.description = val
                    elif key == "weapontype":
                        item.weapon_type = val

            # Stackable flag
            item.stackable = elem.get("stackable", "no") == "yes"

            # Initial classification
            item.category = self._classify_item(item)

            self._items[item_id] = item
            self._items_by_name[name.lower()] = item
            count += 1

        self._indexed = True
        return count

    def index_monsters_xml(self, path: str | Path) -> int:
        """Index monsters from a monsters.xml file. Returns count indexed."""
        root = ET.parse(str(path)).getroot()
        count = 0

        for elem in root.findall("monster"):
            name = elem.get("name", "")
            if not name:
                continue

            monster = IndexedMonster(
                name=name,
                race=elem.get("race", ""),
            )

            # Experience
            exp_elem = elem.find("experience")
            if exp_elem is not None and exp_elem.text:
                try:
                    monster.experience = int(exp_elem.text)
                except ValueError:
                    pass

            # Health
            health_elem = elem.find("health")
            if health_elem is not None:
                try:
                    monster.health = int(health_elem.get("max", 0))
                except (ValueError, TypeError):
                    pass

            # Speed
            speed_elem = elem.find("speed")
            if speed_elem is not None and speed_elem.text:
                try:
                    monster.speed = int(speed_elem.text)
                except ValueError:
                    pass

            # Look
            look_elem = elem.find("look")
            if look_elem is not None:
                try:
                    monster.look_type = int(look_elem.get("type", 0))
                    monster.corpse_id = int(look_elem.get("corpse", 0))
                except (ValueError, TypeError):
                    pass

            # Immunities
            for imm in elem.findall("immunity"):
                imm_name = imm.get("name", "")
                if imm_name:
                    monster.immunities.append(imm_name)

            # Elements
            for el in elem.findall("element"):
                el_name = el.get("name", "")
                el_val = el.get("percent", "100")
                try:
                    monster.elements[el_name] = int(el_val)
                except ValueError:
                    pass

            # Loot
            loot_elem = elem.find("loot")
            if loot_elem is not None:
                for item in loot_elem.findall("item"):
                    loot_entry = {
                        "id": int(item.get("id", 0)),
                        "name": item.get("name", ""),
                        "chance": item.get("chance", "0"),
                        "countmax": int(item.get("countmax", 1)),
                    }
                    monster.loot.append(loot_entry)

            self._monsters[name] = monster
            count += 1

        return count

    def index_theme(self, theme_name: str, theme_data: Dict[str, Any]) -> None:
        """Index item/monster associations for a theme from its template."""
        item_ids = set()

        for gid in theme_data.get("grounds", []):
            item_ids.add(gid)
        for wid in theme_data.get("walls", []):
            item_ids.add(wid)
        for did in theme_data.get("decorations", []):
            item_ids.add(did)

        self._theme_items[theme_name] = item_ids

        # Tag items with this theme; create stub items if not yet indexed
        for iid in theme_data.get("grounds", []):
            if iid in self._items:
                self._items[iid].theme_tags.add(theme_name)
                self._items[iid].category = "ground"
            else:
                stub = IndexedItem(id=iid, name=f"Ground_{iid}", type_name="ground", category="ground")
                stub.theme_tags.add(theme_name)
                self._items[iid] = stub
                self._items_by_name[stub.name.lower()] = stub

        for iid in theme_data.get("walls", []):
            if iid in self._items:
                self._items[iid].theme_tags.add(theme_name)
                self._items[iid].category = "wall"
            else:
                stub = IndexedItem(id=iid, name=f"Wall_{iid}", type_name="wall", category="wall")
                stub.theme_tags.add(theme_name)
                self._items[iid] = stub
                self._items_by_name[stub.name.lower()] = stub

        for iid in theme_data.get("decorations", []):
            if iid in self._items:
                self._items[iid].theme_tags.add(theme_name)
                self._items[iid].category = "decoration"
            else:
                stub = IndexedItem(id=iid, name=f"Decor_{iid}", type_name="decoration", category="decoration")
                stub.theme_tags.add(theme_name)
                self._items[iid] = stub
                self._items_by_name[stub.name.lower()] = stub

        # Tag monsters
        monster_names = set()
        for mname in theme_data.get("monsters", []):
            monster_names.add(mname)
            if mname in self._monsters:
                self._monsters[mname].theme_tags.add(theme_name)
            else:
                stub_monster = IndexedMonster(name=mname)
                stub_monster.theme_tags.add(theme_name)
                self._monsters[mname] = stub_monster
        self._theme_monsters[theme_name] = monster_names

    def index_template_file(self, path: str | Path) -> None:
        """Index a JSON theme template file."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        theme_name = data.get("theme", Path(path).stem)
        self.index_theme(theme_name, data)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get_item(self, item_id: int) -> Optional[IndexedItem]:
        """Get an indexed item by ID."""
        return self._items.get(item_id)

    def get_item_by_name(self, name: str) -> Optional[IndexedItem]:
        """Get an indexed item by name (case-insensitive)."""
        return self._items_by_name.get(name.lower())

    def get_monster(self, name: str) -> Optional[IndexedMonster]:
        """Get an indexed monster by name."""
        return self._monsters.get(name)

    def get_items_by_category(self, category: str) -> List[IndexedItem]:
        """Get all items of a specific category."""
        return [i for i in self._items.values() if i.category == category]

    def get_items_by_theme(self, theme: str) -> List[IndexedItem]:
        """Get all items associated with a theme."""
        ids = self._theme_items.get(theme, set())
        return [self._items[i] for i in ids if i in self._items]

    def get_monsters_by_theme(self, theme: str) -> List[IndexedMonster]:
        """Get all monsters associated with a theme."""
        names = self._theme_monsters.get(theme, set())
        return [self._monsters[n] for n in names if n in self._monsters]

    def search_items(self, query: str, limit: int = 20) -> List[IndexedItem]:
        """Fuzzy search items by name or type."""
        lower = query.lower()
        results = []
        for item in self._items.values():
            score = 0
            if lower in item.name.lower():
                score += 10
            if lower in item.type_name.lower():
                score += 5
            if lower in " ".join(item.theme_tags):
                score += 3
            if score > 0:
                results.append((score, item))
        results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in results[:limit]]

    def search_monsters(self, query: str, limit: int = 20) -> List[IndexedMonster]:
        """Fuzzy search monsters by name."""
        lower = query.lower()
        results = []
        for monster in self._monsters.values():
            score = 0
            if lower in monster.name.lower():
                score += 10
            if lower in " ".join(monster.theme_tags):
                score += 3
            if score > 0:
                results.append((score, monster))
        results.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in results[:limit]]

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(self) -> Dict[str, Any]:
        """Return a summary of indexed assets."""
        cats = {}
        for item in self._items.values():
            cats[item.category] = cats.get(item.category, 0) + 1

        return {
            "total_items": len(self._items),
            "total_monsters": len(self._monsters),
            "total_npcs": len(self._npcs),
            "themes_indexed": list(self._theme_items.keys()),
            "items_by_category": cats,
            "items_by_theme": {t: len(ids) for t, ids in self._theme_items.items()},
            "monsters_by_theme": {t: len(names) for t, names in self._theme_monsters.items()},
        }

    # ------------------------------------------------------------------
    # Auto-classification
    # ------------------------------------------------------------------

    def _classify_item(self, item: IndexedItem) -> str:
        """Auto-classify an item based on name and type."""
        name_lower = item.name.lower()
        type_lower = item.type_name.lower()

        # Type-based classification first
        if type_lower in ("ground", "floor"):
            return "ground"
        if type_lower in ("container", "depot"):
            return "container"
        if type_lower == "key":
            return "key"
        if type_lower in ("magicfield", "rune"):
            return "magic"

        # Keyword-based classification
        if any(kw in name_lower for kw in self.GROUND_KEYWORDS):
            return "ground"
        if any(kw in name_lower for kw in self.WALL_KEYWORDS):
            return "wall"
        if any(kw in name_lower for kw in self.MAGIC_KEYWORDS):
            return "magic"
        if any(kw in name_lower for kw in self.LIBRARY_KEYWORDS):
            return "library"
        if any(kw in name_lower for kw in self.NATURE_KEYWORDS):
            return "nature"
        if any(kw in name_lower for kw in self.DECORATION_KEYWORDS):
            return "decoration"

        # Default: use type from XML
        if type_lower:
            return type_lower
        return "unknown"

    @property
    def all_items(self) -> List[IndexedItem]:
        return list(self._items.values())

    @property
    def all_monsters(self) -> List[IndexedMonster]:
        return list(self._monsters.values())

    @property
    def categories(self) -> List[str]:
        cats = set(item.category for item in self._items.values())
        return sorted(cats)

    @property
    def themes(self) -> List[str]:
        return sorted(self._theme_items.keys())