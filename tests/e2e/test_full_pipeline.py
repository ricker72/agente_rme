from __future__ import annotations

import pytest
import json
import os
import tempfile
import shutil

from core.pipeline.full_pipeline import FullPipeline, PipelineResult
from core.balance.balance_engine import BalanceEngine, BalanceReport
from core.expansion.expansion_ai import ExpansionAI, ExpansionReport
from core.campaign.campaign_generator import CampaignGenerator, Campaign
from core.playtest.playtest_engine import PlaytestEngine
from core.world.world_model import WorldModel


class TestFullPipelineInit:
    def test_create(self):
        p = FullPipeline()
        assert p is not None

    def test_create_with_output_dir(self):
        p = FullPipeline(output_dir="/tmp/test_output")
        assert p._output_dir == "/tmp/test_output"


class TestFullPipelineRun:
    def test_run_default(self):
        p = FullPipeline()
        result = p.run()
        assert isinstance(result, PipelineResult)
        assert result.success is True
        assert result.world is not None
        assert result.campaign is not None

    def test_run_with_prompt(self):
        p = FullPipeline()
        result = p.run(prompt="Create Issavi expansion for levels 300-500")
        assert result.success is True
        assert result.theme == "Issavi"

    def test_run_creates_world(self):
        p = FullPipeline()
        result = p.run(theme="Issavi", level_range=(300, 500))
        assert result.world is not None
        assert result.world.tile_count() > 0
        assert result.world.region_count() > 0

    def test_run_expands_world(self):
        p = FullPipeline()
        result = p.run()
        assert result.expansion_report is not None
        assert result.expansion_report.tiles_final > 0

    def test_run_balances_world(self):
        p = FullPipeline()
        result = p.run()
        assert result.balance_report is not None
        assert result.balance_report.world_balanced is True

    def test_run_generates_campaign(self):
        p = FullPipeline()
        result = p.run(theme="Roshamuul")
        assert result.campaign is not None
        assert result.campaign.main_story is not None
        assert len(result.campaign.lore) > 0
        assert len(result.campaign.factions) > 0
        assert len(result.campaign.npcs) > 0

    def test_run_records_stages(self):
        p = FullPipeline()
        result = p.run()
        assert len(result.pipeline_stages) >= 6
        for stage in result.pipeline_stages:
            assert stage["success"] is True

    def test_run_records_time(self):
        p = FullPipeline()
        result = p.run()
        assert result.total_time_seconds > 0

    def test_run_produces_output_files(self):
        tmpdir = tempfile.mkdtemp()
        try:
            p = FullPipeline()
            result = p.run(output_dir=tmpdir)
            assert result.success is True
            assert "campaign" in result.output_files
            assert os.path.exists(result.output_files["campaign"])
        finally:
            shutil.rmtree(tmpdir)


class TestPipelineResult:
    def test_to_dict(self):
        p = FullPipeline()
        result = p.run()
        d = result.to_dict()
        assert "success" in d
        assert "tiles" in d
        assert "regions" in d
        assert "pipeline_stages" in d
        assert d["success"] is True
        assert d["tiles"] > 0


class TestPipelinePromptParsing:
    def test_parse_issavi(self):
        p = FullPipeline()
        result = p.run(prompt="Create Issavi expansion")
        assert result.theme == "Issavi"

    def test_parse_roshamuul(self):
        p = FullPipeline()
        result = p.run(prompt="Roshamuul hunt zone")
        assert result.theme == "Roshamuul"

    def test_parse_default(self):
        p = FullPipeline()
        result = p.run(prompt="Create a generic hunt zone")
        assert result.theme in ["default", "Default"]


class TestE2EIntegration:
    def test_full_pipeline_issavi_300_500(self):
        """E2E test matching the task specification."""
        p = FullPipeline()
        result = p.run(
            prompt="Create Issavi + Roshamuul expansion for levels 300-500 "
                   "with 3 hunts, 2 bosses, a raid and a quest main",
            theme="Issavi",
            level_range=(300, 500),
        )

        assert result.success is True
        assert result.world is not None
        assert result.world.tile_count() > 100
        assert result.campaign is not None
        assert result.campaign.main_story is not None
        assert len(result.campaign.bosses) > 0
        assert len(result.campaign.raids) > 0
        assert result.balance_report.world_balanced is True

    def test_all_subsystems_integrated(self):
        """Verify all subsystems are called."""
        p = FullPipeline()
        result = p.run()

        stage_names = [s["stage"] for s in result.pipeline_stages]
        assert "parse_prompt" in stage_names
        assert "generate_world" in stage_names
        assert "expand_world" in stage_names
        assert "playtest" in stage_names
        assert "balance" in stage_names
        assert "generate_campaign" in stage_names
        assert "export" in stage_names

    def test_output_files_written(self):
        """Verify all required output files are written."""
        tmpdir = tempfile.mkdtemp()
        try:
            p = FullPipeline()
            result = p.run(output_dir=tmpdir)

            assert os.path.exists(os.path.join(tmpdir, "campaign.json"))
            assert os.path.exists(os.path.join(tmpdir, "report.json"))
            assert os.path.exists(os.path.join(tmpdir, "balance_report.json"))
            assert os.path.exists(os.path.join(tmpdir, "world_summary.json"))
        finally:
            shutil.rmtree(tmpdir)

    def test_campaign_json_valid(self):
        """Verify campaign.json is valid JSON with required fields."""
        tmpdir = tempfile.mkdtemp()
        try:
            p = FullPipeline()
            result = p.run(output_dir=tmpdir, theme="Issavi")

            campaign_path = os.path.join(tmpdir, "campaign.json")
            with open(campaign_path, "r") as f:
                data = json.load(f)

            assert "theme" in data
            assert "lore" in data
            assert "factions" in data
            assert "npcs" in data
            assert "main_story" in data
            assert "economy" in data
        finally:
            shutil.rmtree(tmpdir)

    def test_world_has_spawns_after_pipeline(self):
        """Verify world has spawns after full pipeline."""
        p = FullPipeline()
        result = p.run()
        spawns = sum(1 for t in result.world.tiles.values()
                     if t.spawn is not None)
        assert spawns > 0

    def test_world_has_regions_after_pipeline(self):
        """Verify world has multiple regions after expansion."""
        p = FullPipeline()
        result = p.run()
        assert result.world.region_count() >= 2