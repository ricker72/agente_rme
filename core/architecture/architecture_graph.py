from __future__ import annotations

from typing import Dict, List, Optional


class ArchitectureGraph:
    def __init__(self):
        self.graph: Dict[str, Dict[str, List[str]]] = {}

    def add_structure(self, category: str, components: List[str]) -> None:
        key = category.title()
        self.graph.setdefault(key, {})
        self.graph[key]["components"] = list(dict.fromkeys(components))

    def add_connection(self, category: str, relation: str, target: str) -> None:
        key = category.title()
        self.graph.setdefault(key, {})
        self.graph[key].setdefault("connections", [])
        if target not in self.graph[key]["connections"]:
            self.graph[key]["connections"].append(target)

    def get_hierarchy(self, category: str) -> Dict[str, object]:
        return self.graph.get(category.title(), {})

    def merge_graph(self, other: "ArchitectureGraph") -> None:
        for category, details in other.graph.items():
            self.graph.setdefault(category, {})
            for key, values in details.items():
                existing = set(self.graph[category].get(key, []))
                existing.update(values)
                self.graph[category][key] = list(existing)

    def as_dict(self) -> Dict[str, object]:
        return self.graph.copy()
