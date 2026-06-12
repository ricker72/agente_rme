import json
from pathlib import Path
from typing import Dict


class DatasetBuilder:
    CATEGORIES = [
        "cities",
        "dungeons",
        "boss_rooms",
        "temples",
        "depots",
        "roads",
        "bridges",
    ]

    def __init__(self, root: str = "dataset"):
        self.root = Path(root)
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        for category in self.CATEGORIES:
            (self.root / category).mkdir(exist_ok=True)

    def build_from_analysis(
        self, analysis: Dict[str, object], category: str, name: str
    ) -> str:
        if category not in self.CATEGORIES:
            raise ValueError(f"Unsupported category: {category}")
        target = self.root / category / f"{name}.json"
        with open(target, "w", encoding="utf-8") as handle:
            json.dump(analysis, handle, ensure_ascii=False, indent=2)
        return str(target)

    def save_template(
        self, template: Dict[str, object], category: str, name: str
    ) -> str:
        return self.build_from_analysis(template, category, name)

    def list_dataset(self) -> Dict[str, int]:
        return {
            category: len(list((self.root / category).glob("*.json")))
            for category in self.CATEGORIES
        }
