from dataclasses import dataclass, field
from typing import List

@dataclass
class Monster:
    name: str
    health: int
    experience: int
    speed: int
    race: str
    elements: List[str]
    loot: List[str]
    classification: str = field(init=False)

    def __post_init__(self):
        self.classification = self._classify()

    def _classify(self) -> str:
        if self.experience < 300:
            return "low_level"
        if self.experience < 800:
            return "mid_level"
        if self.experience < 2200:
            return "high_level"
        return "endgame"

MONSTERS = [
    Monster(
        name="Frazzlemaw",
        health=3700,
        experience=2800,
        speed=90,
        race="undead",
        elements=["ice", "physical"],
        loot=["fishbone", "crystal coin", "dragon ham"],
    ),
    Monster(
        name="Sphinx",
        health=4200,
        experience=3500,
        speed=85,
        race="undead",
        elements=["physical", "energy"],
        loot=["sphinx amulet", "giant emerald"],
    ),
    Monster(
        name="Cloak Of Terror",
        health=2600,
        experience=2400,
        speed=90,
        race="undead",
        elements=["physical", "death"],
        loot=["red piece of cloth", "demon horn"],
    ),
    Monster(
        name="Demon",
        health=2500,
        experience=2100,
        speed=90,
        race="demon",
        elements=["fire", "physical"],
        loot=["demon horn", "soul orb"],
    ),
    Monster(
        name="Vampire",
        health=1500,
        experience=1400,
        speed=120,
        race="undead",
        elements=["physical", "drain"],
        loot=["vampire teeth", "garlic necklace"],
    ),
    Monster(
        name="Jungle Troll",
        health=1100,
        experience=700,
        speed=100,
        race="orc",
        elements=["physical"],
        loot=["troll green", "gold coin"],
    ),
    Monster(
        name="Hydra",
        health=2600,
        experience=2400,
        speed=90,
        race="hydra",
        elements=["physical", "fire"],
        loot=["hydra head", "dragon ham"],
    ),
]

MONSTER_BY_NAME = {monster.name.lower(): monster for monster in MONSTERS}


def get_monster(name: str):
    return MONSTER_BY_NAME.get(name.lower())
