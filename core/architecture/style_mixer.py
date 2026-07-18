from __future__ import annotations

from typing import Dict, Optional


class StyleMixer:
    def mix_styles(self, style_a: str, style_b: str) -> str:
        if style_a == style_b:
            return style_a
        return f"{style_a}_{style_b}".lower()

    def blend_blueprints(
        self,
        blueprint_a: Dict[str, object],
        blueprint_b: Dict[str, object],
        name: Optional[str] = None,
    ) -> Dict[str, object]:
        theme_a = blueprint_a.get("theme", "unknown")
        theme_b = blueprint_b.get("theme", "unknown")
        category = blueprint_a.get("category", blueprint_b.get("category", "Mixed"))
        mixed_name = (
            name or f"{blueprint_a.get('name')}_{blueprint_b.get('name')}_blend"
        )
        tiles_a = blueprint_a.get("tiles", [])
        tiles_b = blueprint_b.get("tiles", [])
        combined = []
        for index, tile in enumerate(tiles_a):
            combined.append(
                {**tile, "source": "a", "x": tile.get("x"), "y": tile.get("y")}
            )
        for index, tile in enumerate(tiles_b):
            combined.append(
                {
                    **tile,
                    "source": "b",
                    "x": tile.get("x", 0) + 1,
                    "y": tile.get("y", 0) + 1,
                }
            )
        return {
            "name": mixed_name,
            "category": category,
            "theme": self.mix_styles(theme_a, theme_b),
            "tiles": combined,
            "metadata": {
                "source_a": blueprint_a.get("name"),
                "source_b": blueprint_b.get("name"),
                "width": max(
                    blueprint_a.get("metadata", {}).get("width", 0),
                    blueprint_b.get("metadata", {}).get("width", 0),
                ),
                "height": max(
                    blueprint_a.get("metadata", {}).get("height", 0),
                    blueprint_b.get("metadata", {}).get("height", 0),
                ),
            },
        }
