"""
Tests for ExpansionAgent.
"""

import pytest
from agente_rme.core.agents import ExpansionAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestExpansionAgent:
    def test_agent_id(self):
        agent = ExpansionAgent()
        assert agent.agent_id == "expansion"

    def test_execute_with_prompt(self):
        agent = ExpansionAgent()
        request = AgentRequest(prompt="Expand Issavi map")
        response = agent.execute(request)
        assert response.success is True

    def test_execute_with_world_data(self):
        agent = ExpansionAgent()
        request = AgentRequest(
            prompt="Expand",
            input_data={"tiles": {}, "structures": [], "regions": []},
            parameters={"max_hunts": 2, "max_boss_rooms": 1},
        )
        response = agent.execute(request)
        assert response.success is True

    def test_metrics_contains_execution_time(self):
        agent = ExpansionAgent()
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics