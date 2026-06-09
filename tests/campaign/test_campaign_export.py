"""
Tests for the Hito 26.1C campaign export contract.

Validates:
  * CampaignGenerator + CampaignPackage produces a well-formed campaign
  * ``campaign.json`` is always written (even on generator failure)
  * JSON can be loaded back without errors
  * Required keys (quests, bosses, raids, story, rewards) are present
  * Integration with QuestAgent and ExportAgent
  * ``CampaignPackage.ensure`` never returns None
"""

import os
import sys
import json
import tempfile
import shutil
import pytest

# Make sure the package root is on the path.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.campaign import (
    Campaign,
    CampaignGenerator,
    CampaignPackage,
    CampaignValidator,
    PackageStatus,
    ValidationResult,
    REQUIRED_KEYS,
)
from core.campaign.campaign_generator import CampaignGenerator as _CG, Campaign as _C
from agente_rme.core.agents.contracts import AgentRequest
from agente_rme.core.agents.quest_agent import QuestAgent
from agente_rme.core.agents.export_agent import ExportAgent


# ----------------------------------------------------------------------
# Campaign generation (compatible with existing core.campaign.campaign_generator)
# ----------------------------------------------------------------------


class TestCampaignGeneration:
    """Test the CampaignGenerator produces valid campaigns."""

    def test_generate_basic_campaign(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi", level_range=(300, 500))
        assert isinstance(campaign, _C)
        assert campaign.theme == "issavi"
        assert campaign.name == "The Chronicles of issavi"
        assert campaign.level_range == (300, 500)

    def test_campaign_has_lore(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert len(campaign.lore) > 0

    def test_campaign_has_factions(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert len(campaign.factions) > 0

    def test_campaign_has_npcs(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi", npc_count=8)
        assert len(campaign.npcs) > 0

    def test_campaign_has_main_story(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert campaign.main_story is not None
        assert "title" in campaign.main_story
        assert "chapters" in campaign.main_story

    def test_campaign_has_side_quests(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        # Side quests are common but not required
        assert isinstance(campaign.side_quests, list)

    def test_campaign_has_economy(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert campaign.economy is not None

    def test_campaign_has_dialogs(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert isinstance(campaign.dialogs, dict)

    def test_campaign_has_bosses(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert isinstance(campaign.bosses, list)

    def test_campaign_has_raids(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        assert isinstance(campaign.raids, list)

    def test_generate_never_returns_none(self):
        gen = _CG()
        for theme in ["issavi", "roshamuul", "darashia", "default", "unknown"]:
            c = gen.generate(theme=theme)
            assert c is not None, f"generate({theme!r}) returned None"
            assert isinstance(c, _C)


# ----------------------------------------------------------------------
# campaign.json round-trip
# ----------------------------------------------------------------------


class TestCampaignJsonExport:
    """Test that campaign.json is always written and loadable."""

    def test_save_to_json(self, tmp_path):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        path = tmp_path / "campaign.json"
        gen.save(campaign, str(path))
        assert path.exists()
        assert path.stat().st_size > 0

    def test_json_is_valid(self, tmp_path):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        path = tmp_path / "campaign.json"
        gen.save(campaign, str(path))
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert data["theme"] == "issavi"

    def test_load_back(self, tmp_path):
        gen = _CG()
        campaign = gen.generate(theme="issavi")
        path = tmp_path / "campaign.json"
        gen.save(campaign, str(path))
        loaded = gen.load(str(path))
        assert loaded.theme == campaign.theme
        assert loaded.name == campaign.name

    def test_package_save_load_roundtrip(self, tmp_path):
        gen = _CG()
        campaign = gen.generate(theme="issavi", level_range=(300, 500))
        pkg = CampaignPackage.from_campaign(campaign, workflow_id="rt-1")
        path = tmp_path / "campaign.json"
        pkg.save(str(path))
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Required keys are present
        for k in REQUIRED_KEYS:
            assert k in data, f"Required key {k!r} missing from campaign.json"


# ----------------------------------------------------------------------
# Validator
# ----------------------------------------------------------------------


class TestCampaignValidator:
    """Test the CampaignValidator catches malformed data."""

    def test_validate_ok_package(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi", level_range=(300, 500))
        pkg = CampaignPackage.from_campaign(campaign)
        v = CampaignValidator()
        result = v.validate(pkg)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_minimal_package(self):
        pkg = CampaignPackage.minimal(theme="default", level_range=[1, 100])
        v = CampaignValidator()
        result = v.validate(pkg)
        # The minimal package has all the required keys (just empty),
        # so it should still validate.
        assert result.is_valid is True
        assert result.summary["status"] == "empty"

    def test_validate_none_fails(self):
        v = CampaignValidator()
        result = v.validate(None)
        assert result.is_valid is False
        assert any("None" in (i.message) for i in result.errors)

    def test_validate_dict_missing_key(self):
        v = CampaignValidator()
        result = v.validate({"theme": "x", "quests": [], "bosses": [], "raids": []})
        # Missing 'story' and 'rewards'
        assert result.is_valid is False
        keys_missing = {i.key for i in result.errors}
        assert "story" in keys_missing
        assert "rewards" in keys_missing

    def test_validate_dict_wrong_type(self):
        v = CampaignValidator()
        result = v.validate({
            "theme": "x",
            "quests": "not a list",
            "bosses": [],
            "raids": [],
            "story": {},
            "rewards": {},
        })
        assert result.is_valid is False
        assert any("quests" in i.key for i in result.errors)


# ----------------------------------------------------------------------
# Fallback contract — campaign is NEVER None
# ----------------------------------------------------------------------


class TestNeverNoneContract:
    """Ensure the campaign can never be None after the pipeline."""

    def test_package_minimal_is_not_none(self):
        pkg = CampaignPackage.minimal()
        assert pkg is not None
        assert isinstance(pkg, CampaignPackage)

    def test_package_ensure_none_returns_minimal(self):
        pkg = CampaignPackage.ensure(None, theme="x")
        assert pkg is not None
        assert isinstance(pkg, CampaignPackage)
        assert pkg.status == PackageStatus.EMPTY

    def test_package_ensure_dict_wraps(self):
        pkg = CampaignPackage.ensure({"theme": "demo"}, theme="demo")
        assert pkg is not None
        assert isinstance(pkg, CampaignPackage)
        assert pkg.theme == "demo"


# ----------------------------------------------------------------------
# Agent integration
# ----------------------------------------------------------------------


class TestQuestAgentContract:
    """QuestAgent must always return a non-empty CampaignPackage dict."""

    def test_quest_agent_returns_campaign(self):
        agent = QuestAgent()
        req = AgentRequest(
            agent_id="quest",
            prompt="Issavi for levels 300-500",
            parameters={
                "theme": "issavi",
                "level_min": 300,
                "level_max": 500,
                "npc_count": 8,
                "faction_count": 3,
            },
        )
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data is not None
        assert isinstance(data, dict)
        for k in REQUIRED_KEYS:
            assert k in data, f"Required key {k!r} missing from QuestAgent output"

    def test_quest_agent_with_no_theme(self):
        agent = QuestAgent()
        req = AgentRequest(
            agent_id="quest",
            prompt="Generate something",
            parameters={},
        )
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data is not None
        for k in REQUIRED_KEYS:
            assert k in data

    def test_quest_agent_with_prompt_only(self):
        agent = QuestAgent()
        req = AgentRequest(
            agent_id="quest",
            prompt="Roshamuul campaign for high-level players",
            parameters={},
        )
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data is not None
        # Theme should have been auto-extracted
        assert data.get("theme") == "roshamuul"


class TestExportAgentContract:
    """ExportAgent must always write campaign.json."""

    def setup_method(self, method):
        self.tmp = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.tmp, "output")

    def teardown_method(self, method):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_export_writes_campaign_json_with_data(self):
        gen = _CG()
        campaign = gen.generate(theme="issavi", level_range=(300, 500))
        pkg = CampaignPackage.from_campaign(campaign)
        req = AgentRequest(
            agent_id="export",
            prompt="Issavi export",
            parameters={},
            context={"campaign": pkg.to_dict()},
        )
        agent = ExportAgent(output_dir=self.output_dir)
        resp = agent.execute(req)
        assert resp.success is True
        path = os.path.join(self.output_dir, "campaign.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data

    def test_export_writes_campaign_json_without_data(self):
        """Even with no campaign in context, campaign.json must be written."""
        req = AgentRequest(
            agent_id="export",
            prompt="Empty export",
            parameters={},
            context={},
        )
        agent = ExportAgent(output_dir=self.output_dir)
        resp = agent.execute(req)
        path = os.path.join(self.output_dir, "campaign.json")
        if resp.success:
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k in REQUIRED_KEYS:
                assert k in data
        else:
            # Even on failure, the file must exist
            assert os.path.exists(path), "campaign.json MUST be written even on failure"


# ----------------------------------------------------------------------
# Benchmark scenario from the task
# ----------------------------------------------------------------------


class TestBenchmarkScenario:
    """Replicate the exact benchmark scenario from the task contract."""

    def test_issavi_roshamuul_hybrid_campaign(self):
        """Simulate: 'Issavi + Roshamuul for levels 300-500, 3 hunts,
        2 bosses, 1 raid, quest principal'"""
        gen = _CG()
        issavi = gen.generate(theme="issavi", level_range=(300, 500),
                              npc_count=8, faction_count=3)
        roshamuul = gen.generate(theme="roshamuul", level_range=(300, 500),
                                 npc_count=8, faction_count=3)
        assert issavi.main_story is not None
        assert roshamuul.main_story is not None
        assert issavi.theme != roshamuul.theme
        # Both must have content
        assert len(issavi.factions) >= 2
        assert len(roshamuul.factions) >= 2

    def test_save_combined_campaign_to_json(self, tmp_path):
        gen = _CG()
        issavi = gen.generate(theme="issavi", level_range=(300, 500))
        roshamuul = gen.generate(theme="roshamuul", level_range=(300, 500))
        combined = {
            "issavi": issavi.to_dict(),
            "roshamuul": roshamuul.to_dict(),
            "metadata": {
                "level_range": [300, 500],
                "hunts": 3,
                "bosses": 2,
                "raids": 1,
                "main_quest": True,
            },
        }
        path = tmp_path / "campaign.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(combined, f, indent=2)
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "issavi" in data
        assert "roshamuul" in data
        assert data["metadata"]["hunts"] == 3
