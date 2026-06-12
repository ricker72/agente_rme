"""
Tests for the prompt â†’ campaign.json pipeline.

Validates the end-to-end flow:
    Prompt
        â†“
    QuestAgent (builds CampaignPackage)
        â†“
    ExportAgent (writes campaign.json unconditionally)
        â†“
    Validator (validates the resulting JSON)

These tests confirm that, at every step of the pipeline, the campaign
slot is never empty, never None, and always satisfies the Hito 26.1C
required-keys contract.
"""

import os
import sys
import json
import shutil
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.campaign import (
    CampaignGenerator,
    CampaignPackage,
    CampaignValidator,
    REQUIRED_KEYS,
)
from core.agents.contracts import AgentRequest
from core.agents.quest_agent import QuestAgent
from core.agents.export_agent import ExportAgent

# ----------------------------------------------------------------------
# Pipeline fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def output_dir():
    d = tempfile.mkdtemp(prefix="hito261c_pipeline_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


def _build_request(prompt: str, **params) -> AgentRequest:
    return AgentRequest(
        agent_id="quest",
        prompt=prompt,
        parameters=params,
    )


# ----------------------------------------------------------------------
# Prompt â†’ QuestAgent
# ----------------------------------------------------------------------


class TestPromptToQuestAgent:
    """The QuestAgent must always produce a CampaignPackage dict from a prompt."""

    def test_issavi_prompt(self):
        agent = QuestAgent()
        req = _build_request(
            "Issavi dungeon for levels 300-500",
            theme="issavi",
            level_min=300,
            level_max=500,
        )
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert isinstance(data, dict)
        for k in REQUIRED_KEYS:
            assert k in data, f"Missing {k!r} in QuestAgent output"
        assert data["theme"] == "issavi"
        assert data["level_range"] == [300, 500]

    def test_roshamuul_prompt(self):
        agent = QuestAgent()
        req = _build_request("Roshamuul raid content", theme="roshamuul")
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data["theme"] == "roshamuul"
        for k in REQUIRED_KEYS:
            assert k in data

    def test_darashia_prompt(self):
        agent = QuestAgent()
        req = _build_request("Darashia plains", theme="darashia")
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data["theme"] == "darashia"
        for k in REQUIRED_KEYS:
            assert k in data

    def test_prompt_without_parameters(self):
        """A prompt-only request should still produce a valid package."""
        agent = QuestAgent()
        req = _build_request("Build me a cool dungeon")
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        for k in REQUIRED_KEYS:
            assert k in data
        assert data["theme"] in ("default",)  # auto-extracted or default
        assert data["level_range"] == [1, 200]


# ----------------------------------------------------------------------
# QuestAgent â†’ ExportAgent
# ----------------------------------------------------------------------


class TestQuestAgentToExportAgent:
    """The output of QuestAgent feeds into ExportAgent â€” verify the chain."""

    def test_quest_output_is_export_ready(self):
        agent = QuestAgent()
        req = _build_request(
            "Issavi and Roshamuul for 300-500",
            theme="issavi",
            level_min=300,
            level_max=500,
        )
        quest_resp = agent.execute(req)
        assert quest_resp.success is True
        campaign_data = quest_resp.output_data

        # Now feed it into the export stage
        export_req = AgentRequest(
            agent_id="export",
            prompt="Export the campaign",
            context={"campaign": campaign_data},
        )
        exporter = ExportAgent(output_dir=output_dir_factory())
        export_resp = exporter.execute(export_req)
        assert export_resp.success is True
        # The campaign.json file must exist
        artifacts = export_resp.artifacts
        assert "campaign" in artifacts
        path = artifacts["campaign"]
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data, f"Required key {k!r} missing in exported JSON"


def output_dir_factory():
    """Return a fresh tmp dir for each test."""
    return tempfile.mkdtemp(prefix="hito261c_chain_")


# ----------------------------------------------------------------------
# ExportAgent â†’ campaign.json
# ----------------------------------------------------------------------


class TestExportAgentToFile:
    """The ExportAgent must write a valid campaign.json file."""

    def test_writes_valid_json(self, output_dir):
        gen = CampaignGenerator()
        campaign = gen.generate(theme="issavi", level_range=(300, 500))
        pkg = CampaignPackage.from_campaign(campaign)

        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="Export",
            context={"campaign": pkg.to_dict()},
        )
        resp = exporter.execute(req)
        assert resp.success is True
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        for k in REQUIRED_KEYS:
            assert k in data

    def test_writes_json_with_minimal_package(self, output_dir):
        """A minimal CampaignPackage should still serialize to a valid file."""
        pkg = CampaignPackage.minimal(theme="fallback-test", level_range=[1, 100])
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="Export minimal",
            context={"campaign": pkg.to_dict()},
        )
        resp = exporter.execute(req)
        assert resp.success is True
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data

    def test_writes_json_with_no_campaign(self, output_dir):
        """If no campaign data is supplied, the agent must still write a file."""
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="Export nothing",
            context={},
        )
        exporter.execute(req)
        # Even on partial failure, the file MUST exist
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path), "campaign.json MUST be written even without data"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data, f"Required key {k!r} missing from fallback campaign.json"


# ----------------------------------------------------------------------
# File â†’ Validator
# ----------------------------------------------------------------------


class TestFileToValidator:
    """The campaign.json file must pass the CampaignValidator."""

    def test_exported_file_passes_validator(self, output_dir):
        gen = CampaignGenerator()
        campaign = gen.generate(theme="issavi", level_range=(300, 500))
        pkg = CampaignPackage.from_campaign(campaign)
        pkg.save(os.path.join(output_dir, "campaign.json"))

        path = os.path.join(output_dir, "campaign.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        v = CampaignValidator()
        result = v.validate(data)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.summary["counts"]["bosses"] >= 2
        assert result.summary["counts"]["raids"] >= 1
        assert result.summary["counts"]["quests"] >= 3

    def test_fallback_file_passes_validator(self, output_dir):
        """Even an empty fallback should pass validation (with maybe a warning)."""
        pkg = CampaignPackage.minimal(theme="default", level_range=[1, 200])
        pkg.save(os.path.join(output_dir, "campaign.json"))
        with open(
            os.path.join(output_dir, "campaign.json"), "r", encoding="utf-8"
        ) as f:
            data = json.load(f)
        v = CampaignValidator()
        result = v.validate(data)
        # The required keys exist (just empty), so the validator should pass
        assert result.is_valid is True


# ----------------------------------------------------------------------
# Full end-to-end test
# ----------------------------------------------------------------------


class TestEndToEndPipeline:
    """Prompt â†’ CampaignPackage â†’ campaign.json â†’ Validator."""

    PROMPTS = [
        "Issavi dungeon for levels 300-500, 3 hunts, 2 bosses, 1 raid, quest principal",
        "Roshamuul raid for high levels",
        "Darashia plains with desert bosses",
        "Soul War campaign with the choirs",
        "Library expedition for scholars",
    ]

    @pytest.mark.parametrize("prompt", PROMPTS)
    def test_prompt_produces_valid_campaign_json(self, prompt, output_dir):
        # 1) Quest stage
        quest_agent = QuestAgent()
        req = _build_request(prompt)
        quest_resp = quest_agent.execute(req)
        assert quest_resp.success is True
        campaign_data = quest_resp.output_data
        assert campaign_data is not None

        # 2) Export stage
        export_agent = ExportAgent(output_dir=output_dir)
        export_req = AgentRequest(
            agent_id="export",
            prompt=prompt,
            context={"campaign": campaign_data},
        )
        export_resp = export_agent.execute(export_req)
        assert export_resp.success is True
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)

        # 3) Validate the file
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        v = CampaignValidator()
        result = v.validate(data)
        assert result.is_valid is True, result.to_dict()
        for k in REQUIRED_KEYS:
            assert k in data


# ----------------------------------------------------------------------
# Required-keys spot checks
# ----------------------------------------------------------------------


class TestRequiredKeys:
    """The exported campaign.json must always contain the required keys."""

    def test_quests_key_present(self, output_dir):
        run_pipeline_and_assert(output_dir, "issavi", has_key="quests", is_list=True)

    def test_bosses_key_present(self, output_dir):
        run_pipeline_and_assert(output_dir, "roshamuul", has_key="bosses", is_list=True)

    def test_raids_key_present(self, output_dir):
        run_pipeline_and_assert(output_dir, "darashia", has_key="raids", is_list=True)

    def test_story_key_present(self, output_dir):
        run_pipeline_and_assert(output_dir, "issavi", has_key="story", is_dict=True)

    def test_rewards_key_present(self, output_dir):
        run_pipeline_and_assert(output_dir, "default", has_key="rewards", is_dict=True)


def run_pipeline_and_assert(output_dir, theme, has_key, is_list=False, is_dict=False):
    """Helper: run the pipeline and assert a required key's shape."""
    gen = CampaignGenerator()
    campaign = gen.generate(theme=theme, level_range=(300, 500))
    pkg = CampaignPackage.from_campaign(campaign)

    exporter = ExportAgent(output_dir=output_dir)
    req = AgentRequest(
        agent_id="export",
        prompt=f"Export {theme}",
        context={"campaign": pkg.to_dict()},
    )
    exporter.execute(req)
    path = os.path.join(output_dir, "campaign.json")
    assert os.path.exists(path)
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert has_key in data
    if is_list:
        assert isinstance(data[has_key], list)
    if is_dict:
        assert isinstance(data[has_key], dict)
