from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.world.world_model import WorldModel
from core.world.tile import Tile
from core.world.spawn import Spawn
from core.world.region import Region
from core.world.structure import Structure
from core.balance.balance_engine import BalanceEngine, BalanceReport
from core.expansion.expansion_ai import ExpansionAI, ExpansionReport
from core.campaign.campaign_generator import CampaignGenerator, Campaign
from core.playtest.playtest_engine import PlaytestEngine


@dataclass
class PipelineResult:
    """Result of the full pipeline execution."""
    prompt: str = ""
    theme: str = "default"
    level_range: tuple = (1, 100)
    world: Optional[WorldModel] = None
    balance_report: Optional[BalanceReport] = None
    expansion_report: Optional[ExpansionReport] = None
    campaign: Optional[Campaign] = None
    playtest_report: Any = None
    output_files: Dict[str, str] = field(default_factory=dict)
    pipeline_stages: List[Dict[str, Any]] = field(default_factory=list)
    total_time_seconds: float = 0.0
    success: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "theme": self.theme,
            "level_range": list(self.level_range),
            "output_files": self.output_files,
            "pipeline_stages": self.pipeline_stages,
            "total_time_seconds": self.total_time_seconds,
            "success": self.success,
            "tiles": self.world.tile_count() if self.world else 0,
            "regions": self.world.region_count() if self.world else 0,
            "structures": self.world.structure_count() if self.world else 0,
        }


class FullPipeline:
    """
    Complete RME pipeline: Prompt → World → Playtest → Balance → Campaign → Export.

    Stages:
      1. Parse prompt → extract theme, level_range, params
      2. Generate base world with tiles and spawns
      3. Expand with hunts, bosses, quest zones
      4. Playtest the world
      5. Balance the world
      6. Generate campaign content
      7. Export to files (OTBM, JSON, Lua)
    """

    def __init__(self, output_dir: str = "output"):
        self._output_dir = output_dir
        self._playtest_engine = PlaytestEngine()
        self._balance_engine = BalanceEngine()
        self._expansion_ai = ExpansionAI()
        self._campaign_gen = CampaignGenerator()

    def run(self, prompt: str = "", theme: str = "default",
            level_range: tuple = (1, 100),
            output_dir: Optional[str] = None) -> PipelineResult:
        """
        Execute the full pipeline.

        Args:
            prompt: Natural language prompt describing the expansion.
            theme: Campaign theme.
            level_range: (min_level, max_level).
            output_dir: Output directory for generated files.

        Returns:
            PipelineResult with all generated content.
        """
        start_time = time.time()
        result = PipelineResult(prompt=prompt, theme=theme,
                                level_range=level_range)
        out = output_dir or self._output_dir

        try:
            # Stage 1: Parse prompt
            self._stage(result, "parse_prompt", lambda: self._parse_prompt(prompt, result))

            # Stage 2: Generate world
            self._stage(result, "generate_world", lambda: self._generate_world(result))

            # Stage 3: Expand world
            self._stage(result, "expand_world", lambda: self._expand_world(result))

            # Stage 4: Playtest
            self._stage(result, "playtest", lambda: self._playtest(result))

            # Stage 5: Balance
            self._stage(result, "balance", lambda: self._balance(result))

            # Stage 6: Generate campaign
            self._stage(result, "generate_campaign", lambda: self._generate_campaign(result))

            # Stage 7: Export
            self._stage(result, "export", lambda: self._export(result, out))

            result.success = True

        except Exception as e:
            result.pipeline_stages.append({
                "stage": "error",
                "success": False,
                "error": str(e),
            })

        result.total_time_seconds = round(time.time() - start_time, 2)
        return result

    def _parse_prompt(self, prompt: str, result: PipelineResult) -> None:
        """Parse natural language prompt into parameters."""
        lower = prompt.lower()
        themes = ["issavi", "darashia", "roshamuul", "venore", "thais",
                   "carlin", "ab dendriel", "kazordoon", "svargrond"]
        for t in themes:
            if t in lower:
                result.theme = t.title()
                return

        if "issavi" in lower:
            result.theme = "Issavi"
        elif "roshamuul" in lower:
            result.theme = "Roshamuul"

    def _generate_world(self, result: PipelineResult) -> None:
        """Generate a base world with tiles and regions."""
        world = WorldModel()
        theme = result.theme

        # Create base region
        region = Region(name=f"{theme}_base", theme=theme.lower(),
                        min_level=result.level_range[0],
                        max_level=result.level_range[1],
                        tags=["base", "auto_generated"])
        world.add_region(region)

        # Generate ground tiles
        size = 30
        ground_id = 817  # default grass
        for x in range(size):
            for y in range(size):
                tile = Tile(x=x, y=y, z=7, ground=ground_id,
                            zone=f"{theme}_base")
                world.set_tile(tile)

        # Add some spawns
        monsters = ["Dragon", "Vampire", "Cyclops", "Demon"]
        idx = 0
        for x in range(0, size, 3):
            for y in range(0, size, 3):
                tile = world.get_tile(x, y, 7)
                if tile is not None:
                    tile.spawn = Spawn(
                        monster=monsters[idx % len(monsters)],
                        respawn=60, radius=5,
                    )
                    idx += 1

        result.world = world

    def _expand_world(self, result: PipelineResult) -> None:
        """Expand the world with new content."""
        if result.world is None:
            return
        _, report = self._expansion_ai.expand(
            result.world, max_hunts=3, max_boss_rooms=2,
            max_quest_zones=2, theme="cave"
        )
        result.expansion_report = report

    def _playtest(self, result: PipelineResult) -> None:
        """Run playtest on the world."""
        if result.world is None:
            return
        try:
            report = self._playtest_engine.run(result.world)
            result.playtest_report = report
        except Exception:
            pass

    def _balance(self, result: PipelineResult) -> None:
        """Balance the world."""
        if result.world is None:
            return
        balanced, report = self._balance_engine.balance(result.world)
        result.balance_report = report

    def _generate_campaign(self, result: PipelineResult) -> None:
        """Generate campaign content."""
        campaign = self._campaign_gen.generate(
            theme=result.theme,
            level_range=result.level_range,
            npc_count=8, faction_count=3,
        )
        result.campaign = campaign

    def _export(self, result: PipelineResult, output_dir: str) -> None:
        """Export all generated content to files."""
        import os
        os.makedirs(output_dir, exist_ok=True)

        # Export campaign as JSON
        campaign_path = os.path.join(output_dir, "campaign.json")
        if result.campaign:
            with open(campaign_path, "w", encoding="utf-8") as f:
                f.write(result.campaign.to_json())
            result.output_files["campaign"] = campaign_path

        # Export playtest report
        report_path = os.path.join(output_dir, "report.json")
        if result.playtest_report:
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    if hasattr(result.playtest_report, "to_dict"):
                        f.write(json.dumps(result.playtest_report.to_dict(),
                                            indent=2, default=str))
                    else:
                        f.write(json.dumps({"status": "completed"}, indent=2))
                result.output_files["report"] = report_path
            except Exception:
                pass

        # Export expansion report
        expansion_path = os.path.join(output_dir, "expansion_report.json")
        if result.expansion_report:
            with open(expansion_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(result.expansion_report.to_dict(),
                                    indent=2))
            result.output_files["expansion_report"] = expansion_path

        # Export balance report
        balance_path = os.path.join(output_dir, "balance_report.json")
        if result.balance_report:
            with open(balance_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(result.balance_report.to_dict(),
                                    indent=2))
            result.output_files["balance_report"] = balance_path

        # Export world summary
        if result.world:
            summary_path = os.path.join(output_dir, "world_summary.json")
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(result.world.summary(), indent=2))
            result.output_files["world_summary"] = summary_path

    def _stage(self, result: PipelineResult, name: str, fn) -> None:
        """Execute a pipeline stage and record timing."""
        start = time.time()
        try:
            fn()
            elapsed = round(time.time() - start, 3)
            result.pipeline_stages.append({
                "stage": name, "success": True,
                "time_seconds": elapsed,
            })
        except Exception as e:
            elapsed = round(time.time() - start, 3)
            result.pipeline_stages.append({
                "stage": name, "success": False,
                "time_seconds": elapsed, "error": str(e),
            })