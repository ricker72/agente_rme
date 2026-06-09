from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from core.analyzer import MapAnalyzer

from .architecture_graph import ArchitectureGraph
from .blueprint_generator import BlueprintGenerator
from .pattern_library import PatternLibrary
from .structure_extractor import StructureExtractor


class ArchitectureAnalyzer:
    def __init__(
        self,
        pattern_library: Optional[PatternLibrary] = None,
        architecture_graph: Optional[ArchitectureGraph] = None,
    ):
        self.map_analyzer = MapAnalyzer()
        self.extractor = StructureExtractor()
        self.pattern_library = pattern_library or PatternLibrary()
        self.architecture_graph = architecture_graph or ArchitectureGraph()
        self.blueprint_generator = BlueprintGenerator(self.pattern_library)

    def learn_from_map(self, path: str) -> Dict[str, object]:
        analysis = self.map_analyzer.analyze(path)
        source = Path(path).stem
        theme = analysis.style or "unknown"
        blueprints = []

        if getattr(analysis, "houses", None):
            for index, house in enumerate(analysis.houses):
                raw = {
                    "name": house.get("name", f"house_{house.get('id', index)}"),
                    "width": house.get("width", 10) or 10,
                    "height": house.get("height", 8) or 8,
                    "floors": house.get("floors", []),
                    "walls": house.get("walls", []),
                    "decorations": house.get("decorations", ["table", "chair"]),
                    "connectivity": house.get("connectivity", {"doors": 1}),
                }
                structure = self.extractor.extract_structure(raw)
                blueprint = self.blueprint_generator.create_blueprint(
                    f"{source}_{structure['type'].lower()}_{index}",
                    structure["type"],
                    theme,
                    self._structure_tiles(structure),
                    metadata=structure,
                )
                self.architecture_graph.add_structure(structure["type"], ["walls", "decorations", "exits"])
                blueprints.append(blueprint)

        if getattr(analysis, "patterns", None):
            for index, pattern in enumerate(analysis.patterns):
                category = self._guess_category_from_pattern(pattern)
                blueprint = self.blueprint_generator.create_blueprint(
                    f"{source}_{category.lower()}_{index}",
                    category,
                    theme,
                    [{"x": 0, "y": 0, "type": "floor"}],
                    metadata={
                        "pattern_source": pattern.get("source"),
                        "category_guess": category,
                        "width": pattern.get("width", 0),
                        "height": pattern.get("height", 0),
                    },
                )
                self.architecture_graph.add_structure(category, ["floor", "walls", "decorations"])
                blueprints.append(blueprint)

        return {
            "source": path,
            "style": theme,
            "analysis": self._summarize_analysis(analysis),
            "blueprints": [bp["name"] for bp in blueprints],
            "architecture_graph": self.architecture_graph.as_dict(),
        }

    def _guess_category_from_pattern(self, pattern: Dict[str, object]) -> str:
        style = str(pattern.get("style", "unknown")).lower()
        width = int(pattern.get("width", 0) or 0)
        height = int(pattern.get("height", 0) or 0)
        if width >= 20 and height >= 20:
            return "Temple"
        if width >= 14 and height >= 10:
            return "Market"
        if width <= 8 and height <= 8:
            return "House"
        if "road" in pattern.get("source", "").lower() or width > height * 2 or height > width * 2:
            return "Road"
        return "Temple"

    def _summarize_analysis(self, analysis: object) -> Dict[str, object]:
        return {
            "map_size": getattr(analysis, "map_size", {}),
            "style": getattr(analysis, "style", "unknown"),
            "tile_count": sum(getattr(analysis, "tiles", {}).values()) if getattr(analysis, "tiles", None) else 0,
            "houses": len(getattr(analysis, "houses", [])),
            "patterns": len(getattr(analysis, "patterns", [])),
        }

    def _structure_tiles(self, structure: Dict[str, object]) -> List[Dict[str, object]]:
        width = int(structure.get("width", 1))
        height = int(structure.get("height", 1))
        tiles = []
        for y in range(height):
            for x in range(width):
                tile_type = "floor"
                if x == 0 or y == 0 or x == width - 1 or y == height - 1:
                    tile_type = "wall"
                tiles.append({"x": x, "y": y, "type": tile_type})
        return tiles
