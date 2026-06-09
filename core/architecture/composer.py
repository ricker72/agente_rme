from __future__ import annotations

from typing import Dict, List, Optional

from .architecture_graph import ArchitectureGraph
from .pattern_library import PatternLibrary
from .style_mixer import StyleMixer


class CityComposer:
    def __init__(
        self,
        pattern_library: Optional[PatternLibrary] = None,
        architecture_graph: Optional[ArchitectureGraph] = None,
        style_mixer: Optional[StyleMixer] = None,
    ):
        self.pattern_library = pattern_library or PatternLibrary()
        self.architecture_graph = architecture_graph or ArchitectureGraph()
        self.style_mixer = style_mixer or StyleMixer()

    def compose_city(self, name: str, style: str, components: Optional[List[str]] = None) -> Dict[str, object]:
        components = components or ["Temple", "Market", "House", "Depot", "Bridge"]
        layout = []
        for index, category in enumerate(components):
            blueprint = self.pattern_library.choose_pattern(category, style)
            if blueprint is None:
                blueprint = {
                    "name": f"{style.lower()}_{category.lower()}_{index}",
                    "category": category,
                    "theme": style,
                    "tiles": [{"x": 0, "y": 0, "type": "floor"}],
                    "metadata": {"width": 8, "height": 8},
                }
            layout.append({
                "category": category,
                "blueprint": blueprint,
                "position": {"x": index * 24, "y": index * 18},
            })
            self.architecture_graph.add_connection("City", "contains", category)
        return {
            "name": name,
            "style": style,
            "layout": layout,
            "graph": self.architecture_graph.as_dict(),
        }


class DungeonComposer:
    def __init__(
        self,
        pattern_library: Optional[PatternLibrary] = None,
        architecture_graph: Optional[ArchitectureGraph] = None,
        style_mixer: Optional[StyleMixer] = None,
    ):
        self.pattern_library = pattern_library or PatternLibrary()
        self.architecture_graph = architecture_graph or ArchitectureGraph()
        self.style_mixer = style_mixer or StyleMixer()

    def compose_dungeon(
        self,
        name: str,
        style: str,
        rooms: Optional[List[str]] = None,
    ) -> Dict[str, object]:
        rooms = rooms or ["Entrance", "QuestRoom", "BossRoom", "Shortcut", "TreasureRoom"]
        layout = []
        for index, category in enumerate(rooms):
            pattern_category = category if category in ["QuestRoom", "BossRoom"] else "Road"
            blueprint = self.pattern_library.choose_pattern(pattern_category, style)
            if blueprint is None:
                blueprint = {
                    "name": f"{style.lower()}_{category.lower()}_{index}",
                    "category": category,
                    "theme": style,
                    "tiles": [{"x": 0, "y": 0, "type": "floor"}],
                    "metadata": {"width": 12, "height": 10},
                }
            layout.append({
                "category": category,
                "blueprint": blueprint,
                "position": {"x": index * 20, "y": index * 14},
            })
            self.architecture_graph.add_connection("Dungeon", "contains", category)
        return {
            "name": name,
            "style": style,
            "layout": layout,
            "graph": self.architecture_graph.as_dict(),
        }
