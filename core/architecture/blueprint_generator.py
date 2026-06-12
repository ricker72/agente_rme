from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from .pattern_library import PatternLibrary


class BlueprintGenerator:
    def __init__(self, pattern_library: Optional[PatternLibrary] = None):
        self.pattern_library = pattern_library or PatternLibrary()
        self.blueprint_dir = Path("blueprints")
        self.blueprint_dir.mkdir(parents=True, exist_ok=True)

    def create_blueprint(
        self,
        name: str,
        category: str,
        theme: str,
        tiles: List[Dict[str, object]],
        metadata: Optional[Dict[str, object]] = None,
    ) -> Dict[str, object]:
        blueprint = {
            "name": name,
            "category": category,
            "theme": theme,
            "tiles": tiles,
            "metadata": metadata or {},
        }
        self.pattern_library.register_pattern(category, blueprint)
        file_path = self.blueprint_dir / f"{name}.json"
        file_path.write_text(
            json.dumps(blueprint, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return blueprint

    def _default_tile_grid(
        self, width: int, height: int, tile_type: str
    ) -> List[Dict[str, object]]:
        return [
            {"x": x, "y": y, "type": tile_type}
            for y in range(height)
            for x in range(width)
        ]

    def _default_blueprint(
        self, name: str, category: str, theme: str, width: int, height: int
    ) -> Dict[str, object]:
        tiles = self._default_tile_grid(width, height, "floor")
        return self.create_blueprint(
            name, category, theme, tiles, metadata={"width": width, "height": height}
        )

    def _generate_building(
        self, category: str, theme: str, size: Optional[Dict[str, int]] = None
    ) -> Dict[str, object]:
        width = size.get("width", 16) if size else 16
        height = size.get("height", 12) if size else 12
        candidate = self.pattern_library.choose_pattern(category, theme)
        if candidate:
            return self.expand_blueprint(candidate, factor=1.0)
        return self._default_blueprint(
            f"{theme.lower()}_{category.lower()}", category, theme, width, height
        )

    def generate_temple(
        self, theme: str = "issavi", size: Optional[Dict[str, int]] = None
    ) -> Dict[str, object]:
        return self._generate_building(
            "Temple", theme, size or {"width": 22, "height": 22}
        )

    def generate_depot(
        self, theme: str = "issavi", size: Optional[Dict[str, int]] = None
    ) -> Dict[str, object]:
        return self._generate_building(
            "Depot", theme, size or {"width": 14, "height": 10}
        )

    def generate_house(
        self, theme: str = "issavi", size: Optional[Dict[str, int]] = None
    ) -> Dict[str, object]:
        return self._generate_building(
            "House", theme, size or {"width": 10, "height": 8}
        )

    def generate_guildhall(
        self, theme: str = "issavi", size: Optional[Dict[str, int]] = None
    ) -> Dict[str, object]:
        return self._generate_building(
            "Guildhall", theme, size or {"width": 16, "height": 14}
        )

    def generate_market(
        self, theme: str = "issavi", size: Optional[Dict[str, int]] = None
    ) -> Dict[str, object]:
        return self._generate_building(
            "Market", theme, size or {"width": 18, "height": 14}
        )

    def expand_blueprint(
        self, blueprint: Dict[str, object], factor: float = 1.2
    ) -> Dict[str, object]:
        width = int(blueprint.get("metadata", {}).get("width", 0) * factor)
        height = int(blueprint.get("metadata", {}).get("height", 0) * factor)
        return self._default_blueprint(
            f"{blueprint['name']}_expanded",
            blueprint["category"],
            blueprint["theme"],
            max(width, 1),
            max(height, 1),
        )

    def reduce_blueprint(
        self, blueprint: Dict[str, object], factor: float = 0.75
    ) -> Dict[str, object]:
        width = int(blueprint.get("metadata", {}).get("width", 1) * factor)
        height = int(blueprint.get("metadata", {}).get("height", 1) * factor)
        return self._default_blueprint(
            f"{blueprint['name']}_reduced",
            blueprint["category"],
            blueprint["theme"],
            max(width, 1),
            max(height, 1),
        )

    def rotate_blueprint(
        self, blueprint: Dict[str, object], clockwise: bool = True
    ) -> Dict[str, object]:
        metadata = blueprint.get("metadata", {})
        width = int(metadata.get("width", 0))
        height = int(metadata.get("height", 0))
        tiles = blueprint.get("tiles", [])
        if not tiles or width == 0 or height == 0:
            return blueprint
        rotated = [
            (
                {"x": height - 1 - tile["y"], "y": tile["x"], "type": tile["type"]}
                if clockwise
                else {"x": tile["y"], "y": width - 1 - tile["x"], "type": tile["type"]}
            )
            for tile in tiles
        ]
        return self.create_blueprint(
            f"{blueprint['name']}_rotated",
            blueprint["category"],
            blueprint["theme"],
            rotated,
            metadata={"width": height, "height": width},
        )

    def mirror_blueprint(self, blueprint: Dict[str, object]) -> Dict[str, object]:
        metadata = blueprint.get("metadata", {})
        width = int(metadata.get("width", 0))
        tiles = blueprint.get("tiles", [])
        if not tiles or width == 0:
            return blueprint
        mirrored = [
            {"x": width - 1 - tile["x"], "y": tile["y"], "type": tile["type"]}
            for tile in tiles
        ]
        return self.create_blueprint(
            f"{blueprint['name']}_mirrored",
            blueprint["category"],
            blueprint["theme"],
            mirrored,
            metadata=metadata,
        )
