from __future__ import annotations

from typing import Dict, List


class SeasonGenerator:
    def generate(self, campaign: Dict[str, object]) -> Dict[str, object]:
        theme = campaign.get("theme", "Mythic")
        season_name = f"{theme} Convergence"
        seasonal_quests = self._design_seasonal_quests(theme)
        seasonal_events = self._design_seasonal_events(theme)
        seasonal_rewards = self._design_seasonal_rewards(theme)

        campaign = dict(campaign)
        campaign["season"] = {
            "name": season_name,
            "events": seasonal_events,
            "rewards": seasonal_rewards,
            "summary": f"A limited-time season amplifying the {theme} expansion storyline.",
        }

        existing_quests = list(campaign.get("quests", []))
        existing_quests.extend(seasonal_quests)
        campaign["quests"] = existing_quests

        seasonal_zones = self._build_seasonal_zones(theme)
        campaign["quest_zones"].extend(seasonal_zones)

        return campaign

    def _design_seasonal_quests(self, theme: str) -> List[Dict[str, object]]:
        return [
            {
                "title": f"Season of {theme} Renewal",
                "type": "seasonal",
                "description": f"Complete the seasonal rites to strengthen {theme} defenses.",
                "reward": "seasonal loot",
                "index": 101,
            },
            {
                "title": f"Echoes of {theme}",
                "type": "story",
                "description": f"Investigate the seasonal disturbances around {theme}.",
                "reward": "experience",
                "index": 102,
            },
        ]

    def _design_seasonal_events(self, theme: str) -> List[Dict[str, object]]:
        return [
            {"name": f"{theme} Skyfall", "description": "A skyborne assault that alters monster spawns temporarily."},
            {"name": f"{theme} Harvest", "description": "Gather special materials during the season."},
        ]

    def _design_seasonal_rewards(self, theme: str) -> List[str]:
        return [f"{theme} Season Banner", f"{theme} Event Mount"]

    def _build_seasonal_zones(self, theme: str) -> List[Dict[str, object]]:
        return [
            {
                "name": f"{theme} Seasonal Quest Site",
                "zone_type": "QuestZone",
                "difficulty": "hard",
                "x": 50,
                "y": 72,
                "width": 18,
                "height": 12,
                "purpose": "seasonal_quest",
            }
        ]
