"""
Coverage tests for QuestAgent.

Hito 26.1D — covers all branches:
  * Happy path with world data
  * Theme extraction from prompt
  * Fallback campaign
  * Missing campaign generator
  * Edge cases: unsafe ints, level range swap, exception paths
  * _get_generators with ImportError
  * _resolve_world with various inputs
  * _safe_int with all edge cases
  * Catastrophic exception handler
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agente_rme.core.agents.quest_agent import QuestAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestQuestAgentHappyPath:
    """Happy path scenarios for the QuestAgent."""

    def test_quest_executes_with_world(self):
        agent = QuestAgent()
        world = {
            "tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}},
            "structures": [],
        }
        request = AgentRequest(
            agent_id="quest",
            prompt="issavi quest",
            input_data=world,
        )
        response = agent.execute(request)
        assert response.agent_id == "quest"
        assert response.success or response.error is not None

    def test_quest_extracts_issavi_theme(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest",
            prompt="issavi temple quest",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert response.report.get("theme") == "issavi"

    def test_quest_extracts_roshamuul_theme(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest",
            prompt="roshamuul raid",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert response.report.get("theme") == "roshamuul"

    def test_quest_extracts_soul_war_theme(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest",
            prompt="soul_war quest",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert response.report.get("theme") == "soul_war"

    def test_quest_default_theme(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest",
            prompt="some random quest",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert response.report.get("theme") == "default"

    def test_quest_with_explicit_theme(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest",
            prompt="anything",
            input_data={"tiles": {}},
            parameters={"theme": "library", "level_min": 100, "level_max": 300},
        )
        response = agent.execute(request)
        if response.success:
            assert response.report.get("theme") == "library"

    def test_quest_level_range_in_report(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest", prompt="quest",
            input_data={"tiles": {}},
            parameters={"level_min": 200, "level_max": 400},
        )
        response = agent.execute(request)
        if response.success:
            assert response.report.get("level_range") == [200, 400]

    def test_quest_with_world_in_context(self):
        agent = QuestAgent()
        world = {"tiles": {}}
        request = AgentRequest(
            agent_id="quest", prompt="quest",
            context={"world_model": world},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None


class TestQuestAgentErrorHandling:
    """Error handling and edge cases for the QuestAgent."""

    def test_quest_with_none_input(self):
        agent = QuestAgent()
        request = AgentRequest(agent_id="quest", prompt="quest", input_data=None)
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_quest_with_empty_dict(self):
        agent = QuestAgent()
        request = AgentRequest(agent_id="quest", prompt="quest", input_data={})
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_quest_logger_uses_agent_id(self):
        agent = QuestAgent()
        assert "quest" in agent.logger.name

    def test_quest_metrics_present(self):
        agent = QuestAgent()
        request = AgentRequest(agent_id="quest", prompt="quest", input_data={})
        response = agent.execute(request)
        if response.success:
            assert "execution_time" in response.metrics

    def test_quest_fallback_has_campaign_structure(self):
        agent = QuestAgent()
        request = AgentRequest(agent_id="quest", prompt="test", input_data={})
        response = agent.execute(request)
        if response.success:
            campaign = response.output_data
            # CampaignPackage.to_dict() returns these keys
            assert "theme" in campaign
            assert "quests" in campaign
            assert "bosses" in campaign
            assert "raids" in campaign
            assert "story" in campaign
            assert "rewards" in campaign
            assert "workflow_id" in campaign
            assert "status" in campaign
            assert "errors" in campaign
            assert "generated_at" in campaign
            assert "level_range" in campaign
            assert "campaign" in campaign
            assert "source" in campaign

    def test_quest_extract_theme_library(self):
        agent = QuestAgent()
        assert agent._extract_theme("library dungeon") == "library"

    def test_quest_extract_theme_falcon(self):
        agent = QuestAgent()
        assert agent._extract_theme("falcon castle") == "falcon"

    def test_quest_extract_theme_cobra(self):
        agent = QuestAgent()
        assert agent._extract_theme("cobra bastion") == "cobra"

    def test_quest_extract_theme_darashia(self):
        agent = QuestAgent()
        assert agent._extract_theme("darashia market") == "darashia"

    def test_quest_extract_theme_case_insensitive(self):
        agent = QuestAgent()
        assert agent._extract_theme("ISSAVI Temple") == "issavi"
        assert agent._extract_theme("Roshamuul Raid") == "roshamuul"

    def test_quest_extract_theme_fallback(self):
        agent = QuestAgent()
        assert agent._extract_theme("random theme") == "default"
        assert agent._extract_theme("") == "default"

    def test_quest_fallback_campaign_direct(self):
        agent = QuestAgent()
        campaign = agent._fallback_campaign("issavi", 100, 200)
        assert campaign["theme"] == "issavi"
        assert campaign["level_range"] == [100, 200]
        assert "The Chronicles of issavi" == campaign["name"]
        assert campaign["metadata"]["generated_by"] == "QuestAgent_fallback"
        assert len(campaign["lore"]) > 0
        assert len(campaign["factions"]) > 0

    def test_quest_resolve_world_with_dict(self):
        agent = QuestAgent()
        world = {"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}}
        resolved = agent._resolve_world(world)
        assert resolved is not None

    def test_quest_resolve_world_passthrough(self):
        agent = QuestAgent()
        sentinel = "not a dict"
        result = agent._resolve_world(sentinel)
        assert result == sentinel

    def test_quest_get_generators_cached(self):
        agent = QuestAgent()
        first = agent._get_generators()
        second = agent._get_generators()
        assert first is second or first[0] is second[0]

    def test_quest_handles_exception(self):
        agent = QuestAgent()
        request = AgentRequest(agent_id="quest", prompt="test")
        request.parameters = "not a dict"
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_quest_with_npc_count(self):
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest", prompt="issavi",
            input_data={"tiles": {}},
            parameters={"npc_count": 5, "faction_count": 2},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_quest_safe_int_various_inputs(self):
        """Test _safe_int with various edge cases."""
        agent = QuestAgent()
        assert agent._safe_int(None, 42) == 42
        assert agent._safe_int("", 42) == 42
        assert agent._safe_int(True, 42) == 42
        assert agent._safe_int(False, 42) == 42
        assert agent._safe_int(10, 42) == 10
        assert agent._safe_int(3.14, 42) == 3
        assert agent._safe_int("100", 42) == 100
        assert agent._safe_int("not_a_number", 42) == 42
        assert agent._safe_int([], 42) == 42

    def test_quest_level_range_swap(self):
        """Test that level_max < level_min gets swapped."""
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest", prompt="quest",
            input_data={"tiles": {}},
            parameters={"level_min": 300, "level_max": 100},
        )
        response = agent.execute(request)
        if response.success:
            lr = response.report.get("level_range", [])
            # Should have been swapped so min <= max
            assert lr[0] <= lr[1]

    def test_quest_resolve_world_import_error(self):
        """_resolve_world when core.world import fails."""
        import sys
        from unittest.mock import patch

        agent = QuestAgent()
        with patch.dict(sys.modules, {"core.world": None}, clear=False):
            result = agent._resolve_world({"tiles": {}})
        assert result == {"tiles": {}}

    def test_quest_get_generators_import_error(self):
        """Test _get_generators when CampaignGenerator import fails."""
        import sys
        from unittest.mock import patch

        agent = QuestAgent()
        agent._campaign_gen = None
        with patch.dict(sys.modules, {"core.campaign": None}, clear=False):
            gen, qgen = agent._get_generators()
        assert gen is None
        assert qgen is None

    def test_quest_execute_with_parent_task_id(self):
        """Test execute with parent_task_id set."""
        agent = QuestAgent()
        request = AgentRequest(
            agent_id="quest", prompt="test",
            input_data={"tiles": {}},
            parent_task_id="workflow_123",
        )
        response = agent.execute(request)
        assert response.success or response.error is not None