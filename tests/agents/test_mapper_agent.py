"""
Tests for MapperAgent.
"""

import pytest
from agente_rme.core.agents import MapperAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestMapperAgent:
    def test_agent_id(self):
        agent = MapperAgent()
        assert agent.agent_id == "mapper"

    def test_execute_with_prompt(self):
        agent = MapperAgent()
        request = AgentRequest(prompt="Generate Issavi map")
        response = agent.execute(request)
        assert response.success is True
        assert response.agent_id == "mapper"

    def test_execute_empty_request(self):
        agent = MapperAgent()
        request = AgentRequest()
        response = agent.execute(request)
        assert response.success is True

    def test_execute_with_world_plan(self):
        agent = MapperAgent()
        request = AgentRequest(
            prompt="Generate map",
            input_data={"primary_theme": "issavi", "themes": ["issavi"]},
        )
        response = agent.execute(request)
        assert response.success is True

    def test_metrics_contains_execution_time(self):
        agent = MapperAgent()
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics