from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, List, Optional

DEFAULT_CATEGORIES = [
    "Temple",
    "Depot",
    "Road",
    "Bridge",
    "House",
    "Market",
    "BossRoom",
    "Guildhall",
    "Library",
    "Arena",
    "Harbor",
    "QuestRoom",
]


class PatternLibrary:
    def __init__(self):
        self.patterns: Dict[str, List[Dict[str, object]]] = {
            category: [] for category in DEFAULT_CATEGORIES
        }

    def register_pattern(self, category: str, blueprint: Dict[str, object]) -> None:
        category_key = category.title()
        if category_key not in self.patterns:
            self.patterns[category_key] = []
        if blueprint not in self.patterns[category_key]:
            self.patterns[category_key].append(blueprint)

    def choose_pattern(
        self, category: str, theme: Optional[str] = None
    ) -> Optional[Dict[str, object]]:
        category_key = category.title()
        candidates = self.patterns.get(category_key, [])
        if theme:
            candidates = [
                pattern for pattern in candidates if pattern.get("theme") == theme
            ]
        return random.choice(candidates) if candidates else None

    def list_patterns(self, category: Optional[str] = None) -> List[Dict[str, object]]:
        if category is None:
            return [
                pattern for patterns in self.patterns.values() for pattern in patterns
            ]
        return list(self.patterns.get(category.title(), []))

    def load_blueprints(self, directory: str = "blueprints") -> None:
        directory_path = Path(directory)
        if not directory_path.exists():
            return
        for file_path in directory_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as handle:
                    blueprint = json.load(handle)
                    self.register_pattern(
                        blueprint.get("category", "Unknown"), blueprint
                    )
            except Exception:
                continue

    def clear(self) -> None:
        self.patterns = {category: [] for category in DEFAULT_CATEGORIES}
