from __future__ import annotations

from typing import Dict


class LoreGenerator:
    def generate(
        self, expansion_name: str, theme: str, content: Dict[str, object]
    ) -> Dict[str, str]:
        cities = content.get("cities", [])
        bosses = content.get("bosses", [])
        [boss.get("arena") for boss in bosses[:2] if boss.get("arena")]
        return {
            "city_origin": (
                f"{cities[0].get('name', theme)} was founded to protect the sacred "
                f"{theme} relics and funnel trade through the new expansion."
            ),
            "dungeon_reason": (
                f"The dungeons exist because ancient powers beneath {theme} "
                f"have awakened and threaten the realm with corrupting forces."
            ),
            "boss_purpose": (
                f"Each boss defends a shard of the lost {theme} artifact, "
                f"making them central to the expansion's story."
            ),
            "expansion_legacy": (
                f"{expansion_name} ties together old Tibia myth and "
                f"emerging endgame conflict across Issavi and Roshamuul influences."
            ),
        }
