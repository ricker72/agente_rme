from dataclasses import dataclass
from typing import List

@dataclass
class NPC:
    name: str
    role: str
    location: str
    type: str

NPCS = [
    NPC(name="Thais Guard", role="guard", location="Thais", type="city"),
    NPC(name="Venore Merchant", role="merchant", location="Venore", type="city"),
    NPC(name="Carlin Priest", role="priest", location="Carlin", type="city"),
    NPC(name="Yalahar Traitor", role="spy", location="Yalahar", type="city"),
    NPC(name="Issavi Guide", role="guide", location="Issavi", type="biome"),
]

NPC_BY_NAME = {npc.name.lower(): npc for npc in NPCS}

def get_npc(name: str):
    return NPC_BY_NAME.get(name.lower())
