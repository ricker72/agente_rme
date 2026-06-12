"""
Tests for PlaytestAgent.
"""

from core.agents import PlaytestAgent
from core.agents.contracts import AgentRequest


class TestPlaytestAgent:
    def test_agent_id(self):
        agent = PlaytestAgent()
        assert agent.agent_id == "playtest"

    def test_execute_with_prompt(self):
        agent = PlaytestAgent()
        request = AgentRequest(prompt="Playtest Issavi map")
        response = agent.execute(request)
        assert response.success is True

    def test_execute_fallback_report(self):
        agent = PlaytestAgent()
        request = AgentRequest(
            prompt="Test",
            parameters={"player_level": 300},
        )
        response = agent.execute(request)
        assert response.success is True
        assert response.output_data is not None
        assert "player_level" in response.output_data

    def test_metrics_contains_execution_time(self):
        agent = PlaytestAgent()
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics
