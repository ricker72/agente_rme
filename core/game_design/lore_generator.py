from __future__ import annotations

from typing import Dict, List


class LoreGenerator:
    def generate(self, expansion_name: str, theme: str, content: Dict[str, object]) -> Dict[str, str]:
        cities = content.get("cities", [])
        bosses = content.get("bosses", [])
        dungeon_names = [boss.get("arena") for boss in bosses[:2] if boss.get("arena")]
        return {
            "city_origin": f"{cities[0].get('name', theme)} was founded to protect the sacred {theme} relics and funnel trade through the new expansion.",
            "dungeon_reason": f"The dungeons exist because ancient powers beneath {theme} have awakened and threaten the realm with corrupting forces.",
            "boss_purpose": f"Each boss defends a shard of the lost {theme} artifact, making them central to the expansion's story.",
            "expansion_legacy": f"{expansion_name} ties together old Tibia myth and emerging endgame conflict across Issavi and Roshamuul influences.",
        }
