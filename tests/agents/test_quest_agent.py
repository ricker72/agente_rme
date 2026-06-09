"""
Tests for QuestAgent.
"""

import pytest
from agente_rme.core.agents import QuestAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestQuestAgent:
    def test_agent_id(self):
        agent = QuestAgent()
        assert agent.agent_id == "quest"

    def test_execute_with_prompt(self):
        agent = QuestAgent()
        request = AgentRequest(prompt="Generate quests for Issavi")
        response = agent.execute(request)
        assert response.success is True

    def test_execute_fallback_campaign(self):
        agent = QuestAgent()
        request = AgentRequest(
            prompt="Create Issavi campaign",
            parameters={"theme": "issavi", "level_min": 300, "level_max": 500},
        )
        response = agent.execute(request)
        assert response.success is True
        assert response.output_data is not None
        assert "theme" in response.output_data

    def test_metrics_contains_execution_time(self):
        agent = QuestAgent()
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics

    def test_extract_theme_from_prompt(self):
        agent = QuestAgent()
        theme = agent._extract_theme("Create Issavi with Roshamuul")
        assert theme == "issavi"

    def test_extract_theme_default(self):
        agent = QuestAgent()
        theme = agent._extract_theme("Create a random map")
        assert theme == "default"