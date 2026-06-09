"""
Tests for the Hito 26.1C fallback contract.

The contract: if the campaign generator fails, the campaign slot is
``None`` or an empty dict, the system must still produce a valid
``campaign.json`` with the required keys.  These tests deliberately
induce failure modes and verify the safety net holds.
"""

import os
import sys
import json
import shutil
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.campaign import (
    Campaign,
    CampaignGenerator,
    CampaignPackage,
    CampaignValidator,
    PackageStatus,
    REQUIRED_KEYS,
)
from agente_rme.core.agents.contracts import AgentRequest
from agente_rme.core.agents.quest_agent import QuestAgent
from agente_rme.core.agents.export_agent import ExportAgent


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def output_dir():
    d = tempfile.mkdtemp(prefix="hito261c_fallback_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


# ----------------------------------------------------------------------
# CampaignPackage fallback
# ----------------------------------------------------------------------


class TestCampaignPackageFallback:
    """``CampaignPackage.ensure`` and ``CampaignPackage.minimal`` contracts."""

    def test_minimal_returns_valid_package(self):
        pkg = CampaignPackage.minimal()
        assert isinstance(pkg, CampaignPackage)
        d = pkg.to_dict()
        for k in REQUIRED_KEYS:
            assert k in d
        assert d["status"] == "empty"

    def test_minimal_carries_errors(self):
        pkg = CampaignPackage.minimal(errors=["boom", "kaboom"])
        assert "boom" in pkg.errors
        assert "kaboom" in pkg.errors

    def test_ensure_none_returns_minimal(self):
        for value in [None, "", 0, False, [], {}]:
            pkg = CampaignPackage.ensure(value, theme="x")
            assert isinstance(pkg, CampaignPackage)
            assert pkg.theme == "x"
            assert pkg.status == PackageStatus.EMPTY

    def test_ensure_dict_wraps_correctly(self):
        data = {"theme": "test", "quests": [{"title": "Q"}], "bosses": [], "raids": []}
        pkg = CampaignPackage.ensure(data, theme="test")
        assert isinstance(pkg, CampaignPackage)
        assert pkg.status == PackageStatus.OK
        assert len(pkg.quests) >= 1

    def test_ensure_package_passes_through(self):
        original = CampaignPackage.minimal(theme="orig")
        result = CampaignPackage.ensure(original)
        assert result is original  # identity preserved

    def test_ensure_string_wraps(self):
        pkg = CampaignPackage.ensure("not a package", theme="x")
        assert isinstance(pkg, CampaignPackage)
        # The string becomes the "campaign" field
        assert pkg.campaign == "not a package"

    def test_minimal_serialization(self):
        pkg = CampaignPackage.minimal(theme="minimal", level_range=(1, 100))
        j = pkg.to_json()
        # JSON must be parseable
        data = json.loads(j)
        for k in REQUIRED_KEYS:
            assert k in data
        assert data["theme"] == "minimal"

    def test_minimal_save_load(self, output_dir):
        path = os.path.join(output_dir, "campaign.json")
        pkg = CampaignPackage.minimal(theme="min", level_range=(1, 50))
        pkg.save(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data


# ----------------------------------------------------------------------
# QuestAgent fallback paths
# ----------------------------------------------------------------------


class TestQuestAgentFallback:
    """QuestAgent must always return a CampaignPackage, even on bad input."""

    def test_quest_agent_with_no_parameters(self):
        agent = QuestAgent()
        req = AgentRequest(agent_id="quest", prompt="", parameters={})
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data is not None
        for k in REQUIRED_KEYS:
            assert k in data

    def test_quest_agent_with_none_world(self):
        agent = QuestAgent()
        req = AgentRequest(
            agent_id="quest",
            prompt="issavi",
            input_data=None,
            parameters={"theme": "issavi", "level_min": 1, "level_max": 200},
        )
        resp = agent.execute(req)
        assert resp.success is True
        data = resp.output_data
        assert data is not None
        for k in REQUIRED_KEYS:
            assert k in data

    def test_quest_agent_with_garbage_parameters(self):
        agent = QuestAgent()
        req = AgentRequest(
            agent_id="quest",
            prompt="issavi",
            parameters={"theme": None, "level_min": "junk", "level_max": None},
        )
        resp = agent.execute(req)
        # Should not raise
        assert resp.success is True
        data = resp.output_data
        assert data is not None
        for k in REQUIRED_KEYS:
            assert k in data

    def test_quest_agent_output_is_never_none(self):
        agent = QuestAgent()
        for params in [
            {},
            {"theme": "issavi"},
            {"theme": "roshamuul", "level_min": 100, "level_max": 200},
            {"theme": "unknown-theme-xyz"},
            {"theme": None},
        ]:
            req = AgentRequest(agent_id="quest", prompt="X", parameters=params)
            resp = agent.execute(req)
            assert resp.output_data is not None
            for k in REQUIRED_KEYS:
                assert k in resp.output_data


# ----------------------------------------------------------------------
# ExportAgent fallback paths
# ----------------------------------------------------------------------


class TestExportAgentFallback:
    """ExportAgent must always write campaign.json."""

    def test_export_with_no_context(self, output_dir):
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(agent_id="export", prompt="X", context={})
        resp = exporter.execute(req)
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path), "campaign.json must be written even without context"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data, f"Required key {k!r} missing"

    def test_export_with_none_campaign(self, output_dir):
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="X",
            context={"campaign": None},
        )
        resp = exporter.execute(req)
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data

    def test_export_with_empty_dict(self, output_dir):
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="X",
            context={"campaign": {}},
        )
        resp = exporter.execute(req)
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data

    def test_export_with_malformed_campaign(self, output_dir):
        """A campaign that is just a string is malformed but must still export."""
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="X",
            context={"campaign": "this is not a campaign"},
        )
        resp = exporter.execute(req)
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Even in the worst case the file must be valid JSON with the
        # required keys present (possibly empty).
        for k in REQUIRED_KEYS:
            assert k in data

    def test_export_fallback_passes_validator(self, output_dir):
        """A campaign produced from empty context must still validate."""
        exporter = ExportAgent(output_dir=output_dir)
        req = AgentRequest(
            agent_id="export",
            prompt="Empty export",
            context={},
        )
        exporter.execute(req)
        path = os.path.join(output_dir, "campaign.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        v = CampaignValidator()
        result = v.validate(data)
        # Even the fallback should validate (no errors) - it just may have warnings.
        assert result.is_valid is True


# ----------------------------------------------------------------------
# Generator fallback
# ----------------------------------------------------------------------


class TestGeneratorFallback:
    """``CampaignGenerator.generate`` is guaranteed to never return None."""

    def test_generate_with_none_theme(self):
        gen = CampaignGenerator()
        c = gen.generate(theme=None)
        assert c is not None
        assert isinstance(c, Campaign)

    def test_generate_with_empty_string_theme(self):
        gen = CampaignGenerator()
        c = gen.generate(theme="")
        assert c is not None
        assert isinstance(c, Campaign)

    def test_generate_with_garbage_level_range(self):
        gen = CampaignGenerator()
        c = gen.generate(level_range="not a range")
        assert c is not None
        assert isinstance(c, Campaign)

    def test_generate_with_zero_npcs(self):
        gen = CampaignGenerator()
        c = gen.generate(npc_count=0)
        assert c is not None
        assert isinstance(c, Campaign)
        assert c.npcs == []

    def test_load_corrupt_json_returns_minimal(self, tmp_path):
        gen = CampaignGenerator()
        path = tmp_path / "broken.json"
        path.write_text("{not valid json", encoding="utf-8")
        c = gen.load(str(path))
        assert c is not None
        assert isinstance(c, Campaign)

    def test_load_missing_file_returns_minimal(self, tmp_path):
        gen = CampaignGenerator()
        c = gen.load(str(tmp_path / "nope.json"))
        assert c is not None
        assert isinstance(c, Campaign)


# ----------------------------------------------------------------------
# End-to-end fallback
# ----------------------------------------------------------------------


class TestEndToEndFallback:
    """Run the whole pipeline with broken inputs and verify campaign.json."""

    def test_broken_input_still_produces_campaign_json(self, output_dir):
        # 1) QuestAgent with broken params
        quest_agent = QuestAgent()
        req = AgentRequest(
            agent_id="quest",
            prompt="X",
            parameters={"theme": None, "level_min": None, "level_max": None},
        )
        quest_resp = quest_agent.execute(req)
        assert quest_resp.output_data is not None
        # 2) ExportAgent with the broken-pipeline output
        export_agent = ExportAgent(output_dir=output_dir)
        export_req = AgentRequest(
            agent_id="export",
            prompt="X",
            context={"campaign": quest_resp.output_data},
        )
        export_resp = export_agent.execute(export_req)
        path = os.path.join(output_dir, "campaign.json")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k in REQUIRED_KEYS:
            assert k in data
        v = CampaignValidator()
        result = v.validate(data)
        assert result.is_valid is True
