from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.opentibia.assets.material_loader import BrushMaterialLoader
from core.opentibia.assets.asset_registry import resolve_asset_sources
from core.opentibia.assets.tileset_loader import TilesetLoader


@dataclass(frozen=True)
class MaterialBrushRef:
    name: str
    brush_type: str
    item_id: int | None
    category: str
    source_file: str


class RMEMaterialCatalog:
    def __init__(self, brushes: dict[str, MaterialBrushRef], tilesets: dict[str, set[str]]) -> None:
        self.brushes = brushes
        self.tilesets = tilesets

    @classmethod
    def load(cls, root: str | Path = ".") -> "RMEMaterialCatalog":
        materials = resolve_asset_sources(root).materials_root
        brush_root = materials / "brushs"
        tileset_root = materials / "tilesets"
        brushes = {}
        if brush_root.exists():
            for key, brush in BrushMaterialLoader(brush_root).load().items():
                brushes[key] = MaterialBrushRef(
                    name=brush.name,
                    brush_type=brush.brush_type.lower(),
                    item_id=brush.item_id,
                    category=brush.category,
                    source_file=brush.source_file,
                )
        tilesets = TilesetLoader(tileset_root).load() if tileset_root.exists() else {}
        return cls(brushes, tilesets)

    def brushes_by_type(self, brush_type: str) -> list[MaterialBrushRef]:
        normalized = brush_type.lower()
        return sorted(
            [brush for brush in self.brushes.values() if brush.brush_type == normalized],
            key=lambda brush: brush.name.lower(),
        )

    def brushes_for_tileset(self, tileset: str) -> list[MaterialBrushRef]:
        names = self.tilesets.get(tileset, set())
        return [self.brushes[name] for name in sorted(names) if name in self.brushes]

    def audit(self) -> dict[str, object]:
        type_counts: dict[str, int] = {}
        for brush in self.brushes.values():
            type_counts[brush.brush_type] = type_counts.get(brush.brush_type, 0) + 1
        return {
            "material_catalog_ready": True,
            "brush_count": len(self.brushes),
            "tileset_count": len(self.tilesets),
            "brush_type_counts": dict(sorted(type_counts.items())),
        }
