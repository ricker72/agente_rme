from __future__ import annotations

from typing import Dict, Optional


class BiomePlanner:
    STYLE_TO_BIOME = {
        "issavi": "desert",
        "roshamuul": "shadow_land",
        "yalahar": "coastal",
        "library": "arcane",
        "ankrahmun": "sand",
        "soulwar": "infernal",
    }

    def place_biome(self, theme: str, region: Optional[str] = None) -> Dict[str, object]:
        biome = self.STYLE_TO_BIOME.get(theme.lower(), "generic")
        return {
            "theme": theme,
            "biome": biome,
            "region": region or "central",
        }
