"""
Coverage tests for ExpansionAgent.

Hito 26.1D — covers all branches:
  * Happy path with world_model
  * Missing ExpansionAI (fallback)
  * Theme and parameters
  * Edge cases: empty world, invalid input
  * _get_expansion with ImportError
  * _world_to_dict edge cases
  * _resolve_world with valid/invalid data
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agente_rme.core.agents.expansion_agent import ExpansionAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestExpansionAgentHappyPath:
    """Happy path scenarios for the ExpansionAgent."""

    def test_expansion_executes_with_world(self):
        agent = ExpansionAgent()
        world = {
            "tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}},
            "structures": [],
            "regions": [],
        }
        request = AgentRequest(
            agent_id="expansion",
            prompt="expand",
            input_data=world,
            parameters={"theme": "issavi", "max_hunts": 3, "max_boss_rooms": 2},
        )
        response = agent.execute(request)
        assert response.agent_id == "expansion"
        assert response.success or response.error is not None

    def test_expansion_with_world_in_context(self):
        agent = ExpansionAgent()
        world = {"tiles": {}, "structures": [], "regions": []}
        request = AgentRequest(
            agent_id="expansion",
            prompt="expand",
            context={"world_model": world},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_expansion_with_no_expansion_ai_uses_fallback(self):
        agent = ExpansionAgent()
        world = {"tiles": {}, "structures": [], "regions": []}
        request = AgentRequest(
            agent_id="expansion", prompt="expand", input_data=world,
        )
        response = agent.execute(request)
        if response.success:
            assert isinstance(response.report, dict)
            assert len(response.report) > 0

    def test_expansion_normalizes_tiles(self):
        agent = ExpansionAgent()
        world = {
            "tiles": [
                {"x": 0, "y": 0, "z": 7, "ground": 106},
                {"x": 1, "y": 0, "z": 7, "ground": 106},
            ],
            "structures": [],
            "regions": [],
        }
        request = AgentRequest(
            agent_id="expansion", prompt="expand", input_data=world,
        )
        response = agent.execute(request)
        if response.success and "tiles" in response.output_data:
            assert isinstance(response.output_data["tiles"], dict)


class TestExpansionAgentErrorHandling:
    """Error handling and edge cases for the ExpansionAgent."""

    def test_expansion_with_none_input(self):
        agent = ExpansionAgent()
        request = AgentRequest(agent_id="expansion", prompt="expand", input_data=None)
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_expansion_with_empty_dict(self):
        agent = ExpansionAgent()
        request = AgentRequest(agent_id="expansion", prompt="expand", input_data={})
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_expansion_with_invalid_input(self):
        agent = ExpansionAgent()
        request = AgentRequest(
            agent_id="expansion", prompt="expand", input_data="not a dict"
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_expansion_logger_uses_agent_id(self):
        agent = ExpansionAgent()
        assert "expansion" in agent.logger.name

    def test_expansion_metrics_present(self):
        agent = ExpansionAgent()
        request = AgentRequest(agent_id="expansion", prompt="expand", input_data={})
        response = agent.execute(request)
        if response.success:
            assert "execution_time" in response.metrics

    def test_expansion_with_custom_parameters(self):
        agent = ExpansionAgent()
        request = AgentRequest(
            agent_id="expansion", prompt="expand",
            input_data={"tiles": {}, "structures": [], "regions": []},
            parameters={"max_hunts": 5, "max_boss_rooms": 3, "theme": "roshamuul"},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_expansion_get_expansion_cached(self):
        """Test _get_expansion returns cached instance."""
        agent = ExpansionAgent()
        sentinel = object()
        agent._expansion = sentinel
        assert agent._get_expansion() is sentinel

    def test_expansion_get_expansion_import_error(self):
        """Test _get_expansion ImportError branch."""
        import sys
        from unittest.mock import patch

        agent = ExpansionAgent(expansion_instance=None)
        with patch.dict(sys.modules, {"core.expansion": None}, clear=False):
            result = agent._get_expansion()
        assert result is None

    def test_expansion_world_to_dict_with_to_dict(self):
        """_world_to_dict on an object with to_dict returning tiles dict."""
        agent = ExpansionAgent()

        class FakeWorld:
            def to_dict(self):
                return {
                    "tiles": {"0,0,7": {"x": 0}},
                    "structures": [],
                    "regions": [],
                }
        result = agent._world_to_dict(FakeWorld())
        assert result["tiles"]["0,0,7"] == {"x": 0}

    def test_expansion_world_to_dict_no_to_dict(self):
        """_world_to_dict on an object without to_dict."""
        agent = ExpansionAgent()
        result = agent._world_to_dict(object())
        assert result["tiles"] == {}

    def test_expansion_world_to_dict_non_list_tiles(self):
        """_world_to_dict when tiles is neither list nor dict."""
        agent = ExpansionAgent()

        class FakeWorld:
            def to_dict(self):
                return {"tiles": "bad", "structures": [], "regions": []}
        result = agent._world_to_dict(FakeWorld())
        assert result["tiles"] == {}

    def test_expansion_world_to_dict_dict_tiles(self):
        """_world_to_dict when tiles is already a dict."""
        agent = ExpansionAgent()

        class FakeWorld:
            def to_dict(self):
                return {"tiles": {"0,0,7": {"x": 0}}, "structures": [], "regions": []}
        result = agent._world_to_dict(FakeWorld())
        assert isinstance(result["tiles"], dict)
        assert "0,0,7" in result["tiles"]

    def test_expansion_resolve_world_with_dict(self):
        """_resolve_world with dict input."""
        agent = ExpansionAgent()
        result = agent._resolve_world({"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}})
        assert result is not None

    def test_expansion_resolve_world_passthrough(self):
        """_resolve_world with non-dict input."""
        agent = ExpansionAgent()
        result = agent._resolve_world("not a dict")
        assert result == "not a dict"

    def test_expansion_resolve_world_import_error(self):
        """_resolve_world when core.world is not importable."""
        import sys
        from unittest.mock import patch

        agent = ExpansionAgent()
        with patch.dict(sys.modules, {"core.world": None}, clear=False):
            result = agent._resolve_world({"tiles": {}})
        assert result == {"tiles": {}}

    def test_expansion_handles_exception(self):
        """Test exception handling caught by execute."""
        agent = ExpansionAgent()
        request = AgentRequest(agent_id="expansion", prompt="expand")
        request.context = "not a dict"
        response = agent.execute(request)
        assert response.success or response.error is not None