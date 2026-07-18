"""Expose editor brush families from loaded OpenTibia assets."""

from __future__ import annotations

from .asset_database import OpenTibiaAsset, OpenTibiaBrush


BRUSH_FAMILIES = {
    "Terrain Brush": {"Grounds", "Terrain"},
    "Wall Brush": {"Walls", "Buildings"},
    "Nature Brush": {"Nature"},
    "Mountain Brush": {"Mountains"},
    "Water Brush": {"Water"},
    "Border Brush": {"Borders"},
    "Raw Item Brush": {"Raw Items", "Decoration", "Furniture", "Depot", "Containers", "Roads"},
}


class BrushLoader:
    def __init__(self, assets: list[OpenTibiaAsset]) -> None:
        self.assets = assets

    def load(self) -> list[OpenTibiaBrush]:
        brushes: list[OpenTibiaBrush] = []
        for name, categories in BRUSH_FAMILIES.items():
            candidate = next((asset for asset in self.assets if asset.category in categories), None)
            brushes.append(
                OpenTibiaBrush(
                    name=name,
                    brush_type=name.replace(" Brush", "").lower(),
                    item_id=candidate.asset_id if candidate else None,
                    category=next(iter(categories)),
                    source_file=candidate.source_file if candidate else "asset registry",
                )
            )
        return brushes
