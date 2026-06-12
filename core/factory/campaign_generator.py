from __future__ import annotations

from typing import Dict, List


class CampaignGenerator:
    SIZE_PROFILES = {
        "small": {"cities": 1, "hunts": 2, "dungeons": 1, "bosses": 3, "quests": 10},
        "medium": {"cities": 2, "hunts": 4, "dungeons": 2, "bosses": 6, "quests": 14},
        "large": {"cities": 2, "hunts": 5, "dungeons": 3, "bosses": 8, "quests": 20},
        "epic": {"cities": 3, "hunts": 6, "dungeons": 4, "bosses": 10, "quests": 24},
    }

    def generate(
        self, theme: str, level_range: str, map_size: str
    ) -> Dict[str, object]:
        theme_name = self._normalize_theme(theme)
        profile = self.SIZE_PROFILES.get(map_size.lower(), self.SIZE_PROFILES["large"])

        cities = self._design_cities(theme_name, profile["cities"])
        dungeons = self._design_dungeons(theme_name, profile["dungeons"], level_range)
        bosses = self._design_bosses(theme_name, profile["bosses"], dungeons)
        hunts = self._design_hunts(theme_name, profile["hunts"], level_range)
        quests = self._design_quests(theme_name, profile["quests"], dungeons, hunts)
        roads = self._design_roads(cities, dungeons)
        loot_tables = self._design_loot_tables(theme_name, bosses)
        spawns = self._design_spawns(hunts, bosses)

        return {
            "theme": theme_name,
            "level_range": level_range,
            "map_size": map_size,
            "cities": cities,
            "dungeons": dungeons,
            "boss_zones": bosses,
            "hunts": hunts,
            "quest_zones": quests["zones"],
            "quests": quests["metadata"],
            "roads": roads,
            "loot_tables": loot_tables,
            "spawns": spawns,
        }

    def _normalize_theme(self, theme: str) -> str:
        parts = [
            part.strip().capitalize()
            for part in theme.replace("+", ",").split(",")
            if part.strip()
        ]
        return " ".join(parts) if parts else "Mythic"

    def _design_cities(self, theme: str, count: int) -> List[Dict[str, object]]:
        cities = []
        for index in range(1, count + 1):
            cities.append(
                {
                    "name": f"{theme} City {index}",
                    "theme": theme,
                    "population": 1200 + index * 300,
                    "districts": ["Market", "Temple", "Harbor"],
                    "description": f"A major urban hub within the {theme} expansion.",
                }
            )
        return cities

    def _design_dungeons(
        self, theme: str, count: int, level_range: str
    ) -> List[Dict[str, object]]:
        dungeons = []
        for index in range(1, count + 1):
            difficulty = self._dungeon_difficulty(index, level_range)
            dungeons.append(
                {
                    "name": f"{theme} Depths {index}",
                    "theme": theme,
                    "floors": 2 + index,
                    "difficulty": difficulty,
                    "description": f"A layered dungeon built into the wilds of {theme}.",
                    "connections": [],
                }
            )
        return dungeons

    def _design_bosses(
        self, theme: str, count: int, dungeons: List[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        bosses = []
        for index in range(1, count + 1):
            dungeon = dungeons[min(index - 1, len(dungeons) - 1)]
            bosses.append(
                {
                    "name": f"{theme} Warlord {index}",
                    "arena": f"{theme} Arena {index}",
                    "difficulty": dungeon.get("difficulty", "hard"),
                    "mechanics": [
                        "phase-based attacks",
                        "environmental hazards",
                        "summon adds",
                    ],
                    "loot": [
                        {"item": f"{theme} Relic {index}", "rarity": "epic"},
                        {"item": f"{theme} Essence", "rarity": "rare"},
                    ],
                    "zone_type": "BossZone",
                    "x": 100 + index * 8,
                    "y": 20 + index * 10,
                    "width": 18,
                    "height": 16,
                    "purpose": "boss_encounter",
                }
            )
        return bosses

    def _design_hunts(
        self, theme: str, count: int, level_range: str
    ) -> List[Dict[str, object]]:
        hunts = []
        for index in range(1, count + 1):
            hunts.append(
                {
                    "name": f"{theme} Hunt {index}",
                    "recommended_level": self._recommended_level(level_range, index),
                    "monster_pool": [
                        f"{theme} Scout",
                        f"{theme} Ravager",
                        f"{theme} Warden",
                    ],
                    "loot_profile": {
                        "common": ["gold coins", "healing potion"],
                        "rare": [f"{theme} Claw", f"{theme} Essence"],
                        "epic": [f"{theme} Trophy"],
                    },
                    "respawn_density": "dense" if index <= 2 else "moderate",
                    "zone_type": "HuntingZone",
                    "difficulty": self._hunt_difficulty(index, level_range),
                    "x": 30 + (index - 1) * 8,
                    "y": 40 + (index - 1) * 6,
                    "width": 16,
                    "height": 12,
                    "purpose": "hunt",
                }
            )
        return hunts

    def _design_quests(
        self,
        theme: str,
        count: int,
        dungeons: List[Dict[str, object]],
        hunts: List[Dict[str, object]],
    ) -> Dict[str, object]:
        metadata = []
        zones = []
        for index in range(1, count + 1):
            zone_type = "QuestZone"
            description = f"Complete the mission {index} in the {theme} expansion."
            metadata.append(
                {
                    "title": f"{theme} Quest {index}",
                    "type": (
                        "story"
                        if index % 5 == 1
                        else (
                            "exploration"
                            if index % 5 == 2
                            else (
                                "collection"
                                if index % 5 == 3
                                else "boss"
                                if index % 5 == 4
                                else "puzzle"
                            )
                        )
                    ),
                    "description": description,
                    "reward": "experience",
                    "index": index,
                }
            )
            zones.append(
                {
                    "name": f"{theme} Quest Site {index}",
                    "zone_type": zone_type,
                    "difficulty": "moderate" if index <= 10 else "hard",
                    "x": 20 + (index % 4) * 10,
                    "y": 10 + (index // 4) * 12,
                    "width": 14,
                    "height": 10,
                    "purpose": "quest",
                }
            )
        return {"metadata": metadata, "zones": zones}

    def _design_roads(
        self, cities: List[Dict[str, object]], dungeons: List[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        roads = []
        if cities and dungeons:
            for index, dungeon in enumerate(dungeons, start=1):
                city = cities[index % len(cities)]
                roads.append(
                    {
                        "from": city["name"],
                        "to": dungeon["name"],
                        "type": "main_road",
                        "path": [
                            {"x": 12 + index * 3, "y": 12 + index * 4},
                            {"x": 14 + index * 6, "y": 18 + index * 3},
                            {"x": 18 + index * 8, "y": 24 + index * 2},
                        ],
                    }
                )
        return roads

    def _design_loot_tables(
        self, theme: str, bosses: List[Dict[str, object]]
    ) -> Dict[str, object]:
        return {
            "common": ["gold coins", "minor potion", f"{theme} Shard"],
            "uncommon": [f"{theme} Cloak", f"{theme} Ring"],
            "rare": [f"{theme} Relic", f"{theme} Artifact"],
            "legendary": [f"{theme} Crown", f"{theme} Heart"],
            "boss_drops": [
                {"boss": boss["name"], "drops": boss.get("loot", [])} for boss in bosses
            ],
        }

    def _design_spawns(
        self, hunts: List[Dict[str, object]], bosses: List[Dict[str, object]]
    ) -> List[Dict[str, object]]:
        spawns = []
        for hunt in hunts:
            spawns.append(
                {
                    "zone": hunt["name"],
                    "monster_pool": hunt["monster_pool"],
                    "respawn_density": hunt["respawn_density"],
                    "difficulty": hunt["difficulty"],
                }
            )
        for boss in bosses:
            spawns.append(
                {
                    "zone": boss["arena"],
                    "monster_pool": [boss["name"]],
                    "respawn_density": "sparse",
                    "difficulty": boss["difficulty"],
                }
            )
        return spawns

    def _recommended_level(self, level_range: str, index: int) -> str:
        return level_range if index <= 3 else level_range

    def _hunt_difficulty(self, index: int, level_range: str) -> str:
        return "hard" if index > 3 else "moderate"

    def _dungeon_difficulty(self, index: int, level_range: str) -> str:
        if index == 1:
            return "challenging"
        if index == 2:
            return "hard"
        return "deadly"
