"""
Tests for QAAgent.
"""

import pytest
from agente_rme.core.agents import QAAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestQAAgent:
    def test_agent_id(self):
        agent = QAAgent()
        assert agent.agent_id == "qa"

    def test_execute_with_prompt(self):
        agent = QAAgent()
        request = AgentRequest(prompt="QA Issavi map")
        response = agent.execute(request)
        assert response.success is True

    def test_execute_with_context_data(self):
        agent = QAAgent()
        request = AgentRequest(
            prompt="Validate",
            context={
                "world_model": {"tiles": {}, "regions": []},
                "campaign": {"theme": "issavi", "lore": [], "factions": []},
                "playtest_report": {"player_level": 300},
            },
        )
        response = agent.execute(request)
        assert response.success is True
        assert response.output_data is not None
        assert "overall" in response.output_data
        assert "world_model" in response.output_data

    def test_execute_empty_context(self):
        agent = QAAgent()
        request = AgentRequest(prompt="QA")
        response = agent.execute(request)
        assert response.success is True

    def test_metrics_contains_execution_time(self):
        agent = QAAgent()
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics