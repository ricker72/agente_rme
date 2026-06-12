"""
Tests for ArchitectAgent.
"""

from core.agents import ArchitectAgent
from core.agents.contracts import AgentRequest


class TestArchitectAgent:
    def test_agent_id(self):
        agent = ArchitectAgent()
        assert agent.agent_id == "architect"

    def test_execute_with_prompt(self):
        agent = ArchitectAgent()
        request = AgentRequest(prompt="Generate Issavi city level 300")
        response = agent.execute(request)
        assert response.success is True
        assert response.agent_id == "architect"
        assert response.metrics.get("execution_time") is not None

    def test_execute_empty_prompt(self):
        agent = ArchitectAgent()
        request = AgentRequest(prompt="")
        response = agent.execute(request)
        assert response.success is False

    def test_execute_fallback_plan(self):
        agent = ArchitectAgent()
        request = AgentRequest(prompt="Create Issavi + Roshamuul expansion")
        response = agent.execute(request)
        assert response.success is True
        assert response.output_data is not None
        plan = response.output_data
        assert "prompt" in plan
        assert "themes" in plan

    def test_execute_recovery_after_error(self):
        agent = ArchitectAgent()
        # Should handle gracefully even without real AIArchitect
        request = AgentRequest(prompt="Some random generation")
        response = agent.execute(request)
        assert response.success is True  # Should use fallback

    def test_report_contains_summary(self):
        agent = ArchitectAgent()
        request = AgentRequest(prompt="Create Issavi")
        response = agent.execute(request)
        assert response.report is not None
        assert "summary" in response.report

    def test_metrics_contains_execution_time(self):
        agent = ArchitectAgent()
        request = AgentRequest(prompt="Create Issavi")
        response = agent.execute(request)
        assert "execution_time" in response.metrics
