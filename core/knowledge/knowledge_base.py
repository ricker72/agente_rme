import json
from typing import Dict, List

from .biomes import BIOMES, get_biome
from .cities import CITIES, get_city
from .monsters import MONSTERS, get_monster
from .npcs import NPCS, get_npc
from .progression import HUNTING_RANGES, get_hunting_range
from .themes import THEMES, get_theme
from core.architecture import ArchitectureGraph, PatternLibrary


class KnowledgeGraph:
    def __init__(
        self,
        pattern_library: PatternLibrary | None = None,
        architecture_graph: ArchitectureGraph | None = None,
    ):
        self.biomes = {biome.name.lower(): biome for biome in BIOMES}
        self.themes = {theme.name.lower(): theme for theme in THEMES}
        self.monsters = {monster.name.lower(): monster for monster in MONSTERS}
        self.cities = {city.name.lower(): city for city in CITIES}
        self.npcs = {npc.name.lower(): npc for npc in NPCS}
        self.analysis_store: dict[str, dict] = {}
        self.pattern_library = pattern_library or PatternLibrary()
        self.architecture_graph = architecture_graph or ArchitectureGraph()

    def ingest_analysis(self, source: str, analysis_data: dict) -> None:
        self.analysis_store[source] = analysis_data
        graph_data = analysis_data.get("architecture_graph") if isinstance(analysis_data, dict) else None
        if isinstance(graph_data, dict):
            self.architecture_graph.graph.update(graph_data)

    def query_temple_average_size(self, style: str) -> float:
        sizes = []
        for analysis in self.analysis_store.values():
            if analysis.get("style") == style:
                for room in analysis.get("houses", []):
                    if "temple" in room.get("name", "").lower():
                        sizes.append(int(room.get("size", 0)))
        return sum(sizes) / len(sizes) if sizes else 0.0

    def query_monster_distribution(self, style: str) -> dict:
        distribution = {}
        for analysis in self.analysis_store.values():
            if analysis.get("style") == style:
                for spawn in analysis.get("spawns", []):
                    monster = spawn.get("monster") or spawn.get("type")
                    if monster:
                        distribution[monster] = distribution.get(monster, 0) + 1
        return distribution

    def find_biome(self, name: str):
        return self.biomes.get(name.lower())

    def find_theme(self, name: str):
        return self.themes.get(name.lower())

    def find_monster(self, name: str):
        return self.monsters.get(name.lower())

    def find_city(self, name: str):
        return self.cities.get(name.lower())

    def build_context(
        self,
        description: str,
        monster_names: List[str] | None = None,
        npc_names: List[str] | None = None,
        level_hint: int | None = None,
    ) -> Dict[str, object]:
        monster_names = monster_names or []
        npc_names = npc_names or []
        context: Dict[str, object] = {
            "description": description,
            "detected_biomes": self._detect_biomes(description),
            "preferred_themes": self._detect_themes(description),
            "monsters": self._resolve_monsters(monster_names),
            "npcs": self._resolve_npcs(npc_names),
            "recommended_hunting": self._recommend_hunting(level_hint),
            "city_styles": self._detect_cities(description),
            "analysis_summary": self._build_analysis_summary(),
            "pattern_library": self._build_pattern_summary(),
            "architecture_graph": self.architecture_graph.as_dict(),
        }
        return context

    def _detect_biomes(self, description: str) -> List[str]:
        found = [name for name in self.biomes if name in description.lower()]
        return [self.biomes[name].name for name in found]

    def _detect_themes(self, description: str) -> List[str]:
        found = [name for name in self.themes if name in description.lower()]
        return [self.themes[name].name for name in found]

    def _detect_cities(self, description: str) -> List[str]:
        found = [name for name in self.cities if name in description.lower()]
        return [self.cities[name].name for name in found]

    def _resolve_monsters(self, monster_names: List[str]) -> List[Dict[str, object]]:
        resolved = []
        for name in monster_names:
            monster = self.find_monster(name)
            if monster:
                resolved.append({
                    "name": monster.name,
                    "classification": monster.classification,
                    "health": monster.health,
                    "experience": monster.experience,
                    "race": monster.race,
                })
        return resolved

    def _resolve_npcs(self, npc_names: List[str]) -> List[Dict[str, object]]:
        resolved = []
        for name in npc_names:
            npc = self.find_npc(name)
            if npc:
                resolved.append({
                    "name": npc.name,
                    "role": npc.role,
                    "location": npc.location,
                    "type": npc.type,
                })
        return resolved

    def find_npc(self, name: str):
        return self.npcs.get(name.lower())

    def _recommend_hunting(self, level_hint: int | None) -> Dict[str, object]:
        if level_hint is None:
            return {"level_hint": None, "range": None, "recommended_monsters": []}
        range_info = get_hunting_range(level_hint)
        return {
            "level_hint": level_hint,
            "range": range_info.label,
            "recommended_monsters": range_info.recommended_monsters,
        }

    def _build_analysis_summary(self) -> Dict[str, object]:
        summary = {
            "templates": list(self.analysis_store.keys()),
            "styles": {},
        }
        for source, analysis in self.analysis_store.items():
            style = analysis.get("style", "unknown")
            summary["styles"][style] = summary["styles"].get(style, 0) + 1
        return summary

    def _build_pattern_summary(self) -> Dict[str, object]:
        return {
            "categories": {category: len(patterns) for category, patterns in self.pattern_library.patterns.items()},
            "total_patterns": sum(len(patterns) for patterns in self.pattern_library.patterns.values()),
        }

    def to_json(self, data: Dict[str, object]) -> str:
        return json.dumps(data, ensure_ascii=False, indent=2)
