from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .campaign_generator import CampaignGenerator
from .season_generator import SeasonGenerator
from .world_builder import ExpansionWorldBuilder


class ExpansionFactory:
    def __init__(self, knowledge_graph: Any = None, architecture_graph: Any = None):
        self.campaign_generator = CampaignGenerator()
        self.season_generator = SeasonGenerator()
        self.world_builder = ExpansionWorldBuilder(knowledge_graph, architecture_graph)

    def create_expansion(
        self,
        theme: str,
        level_range: str,
        map_size: str,
        output_path: str | Path | None = None,
    ) -> Dict[str, object]:
        campaign = self.campaign_generator.generate(theme, level_range, map_size)
        campaign = self.season_generator.generate(campaign)
        world_model = self.world_builder.build_model(campaign)
        lua_code = self.world_builder.export_lua(world_model)

        output_dir = Path(output_path) if output_path else Path.cwd() / "expansion_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = campaign.get("theme", "expansion").replace(" ", "_").lower()
        otbm_path = self.world_builder.export_otbm(world_model, output_dir / f"{filename}.otbm")

        return {
            "expansion": campaign,
            "world_plan": self.world_builder.build_plan(campaign),
            "world_model": world_model,
            "lua": lua_code,
            "otbm_path": str(otbm_path),
            "template_dir": str(output_dir),
            "summary": {
                "cities": len(campaign.get("cities", [])),
                "hunts": len(campaign.get("hunts", [])),
                "dungeons": len(campaign.get("dungeons", [])),
                "bosses": len(campaign.get("boss_zones", [])),
                "quests": len(campaign.get("quests", [])),
                "loot_tables": list(campaign.get("loot_tables", {}).keys()),
                "spawns": len(campaign.get("spawns", [])),
            },
        }
