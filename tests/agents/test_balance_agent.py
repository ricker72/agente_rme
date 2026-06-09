"""
Tests for BalanceAgent.
"""

import pytest
from agente_rme.core.agents import BalanceAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestBalanceAgent:
    def test_agent_id(self):
        agent = BalanceAgent()
        assert agent.agent_id == "balance"

    def test_execute_with_prompt(self):
        agent = BalanceAgent()
        request = AgentRequest(prompt="Balance Issavi map")
        response = agent.execute(request)
        assert response.success is True

    def test_execute_with_world_data(self):
        agent = BalanceAgent()
        request = AgentRequest(
            prompt="Balance",
            input_data={"tiles": {}, "structures": [], "regions": []},
            parameters={"player_level": 200},
        )
        response = agent.execute(request)
        assert response.success is True

    def test_metrics_contains_execution_time(self):
        agent = BalanceAgent()
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics