from __future__ import annotations

from typing import Dict

from .building_classifier import BuildingClassifier


class StructureExtractor:
    def __init__(self):
        self.classifier = BuildingClassifier()

    def extract_structure(self, raw_structure: Dict[str, object]) -> Dict[str, object]:
        width = int(raw_structure.get("width", 0))
        height = int(raw_structure.get("height", 0))
        if width == 0 and "x1" in raw_structure and "x2" in raw_structure:
            width = (
                int(raw_structure.get("x2", 0)) - int(raw_structure.get("x1", 0)) + 1
            )
        if height == 0 and "y1" in raw_structure and "y2" in raw_structure:
            height = (
                int(raw_structure.get("y2", 0)) - int(raw_structure.get("y1", 0)) + 1
            )

        structure = {
            "name": raw_structure.get("name", raw_structure.get("id", "unknown")),
            "width": width,
            "height": height,
            "floors": raw_structure.get("floors", []),
            "walls": raw_structure.get("walls", []),
            "decorations": raw_structure.get("decorations", []),
            "connectivity": raw_structure.get("connectivity", {}),
        }
        structure["type"] = self.classifier.classify(structure)
        return structure

    def normalize_structure(self, structure: Dict[str, object]) -> Dict[str, object]:
        return self.extract_structure(
            {
                "width": structure.get("width", 0),
                "height": structure.get("height", 0),
                "floors": structure.get("floors", []),
                "walls": structure.get("walls", []),
                "decorations": structure.get("decorations", []),
                "connectivity": structure.get("connectivity", {}),
                "name": structure.get("name", "unknown"),
            }
        )
