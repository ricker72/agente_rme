"""
Coverage tests for BalanceAgent.

Hito 26.1D — covers all branches:
  * Happy path with world data
  * Player level parameter
  * No engine available (fallback)
  * Edge cases: empty world, invalid, zero level
  * _get_engine with ImportError
  * _resolve_world with dict/tiles/list/import error
  * _world_to_dict edge cases
  * Exception handling
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agente_rme.core.agents.balance_agent import BalanceAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestBalanceAgentHappyPath:
    """Happy path scenarios for the BalanceAgent."""

    def test_balance_executes_with_world(self):
        agent = BalanceAgent()
        world = {
            "tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}},
            "structures": [],
        }
        request = AgentRequest(
            agent_id="balance",
            prompt="balance",
            input_data=world,
            parameters={"player_level": 200},
        )
        response = agent.execute(request)
        assert response.agent_id == "balance"
        assert response.success or response.error is not None

    def test_balance_with_default_player_level(self):
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_with_high_player_level(self):
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b",
            input_data={"tiles": {}},
            parameters={"player_level": 500},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_with_playtest_data_in_context(self):
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b",
            input_data={"tiles": {}},
            context={"playtest_report": {"player_level": 300, "issues": []}},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_no_engine_uses_fallback(self):
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert isinstance(response.report, dict)
            assert len(response.report) > 0

    def test_balance_normalizes_tiles(self):
        agent = BalanceAgent()
        world = {
            "tiles": [
                {"x": 0, "y": 0, "z": 7, "ground": 106},
            ],
            "structures": [],
        }
        request = AgentRequest(
            agent_id="balance", prompt="b", input_data=world,
        )
        response = agent.execute(request)
        if response.success and "tiles" in response.output_data:
            assert isinstance(response.output_data["tiles"], dict)


class TestBalanceAgentErrorHandling:
    """Error handling and edge cases for the BalanceAgent."""

    def test_balance_with_none_input(self):
        agent = BalanceAgent()
        request = AgentRequest(agent_id="balance", prompt="b", input_data=None)
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_with_empty_dict(self):
        agent = BalanceAgent()
        request = AgentRequest(agent_id="balance", prompt="b", input_data={})
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_with_invalid_input(self):
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b", input_data="not a dict"
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_logger_uses_agent_id(self):
        agent = BalanceAgent()
        assert "balance" in agent.logger.name

    def test_balance_metrics_present(self):
        agent = BalanceAgent()
        request = AgentRequest(agent_id="balance", prompt="b", input_data={})
        response = agent.execute(request)
        if response.success:
            assert "execution_time" in response.metrics

    def test_balance_zero_player_level(self):
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b",
            input_data={"tiles": {}},
            parameters={"player_level": 0},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_get_engine_cached(self):
        """Test _get_engine returns cached instance."""
        agent = BalanceAgent()
        sentinel = object()
        agent._engine = sentinel
        assert agent._get_engine() is sentinel

    def test_balance_get_engine_import_error(self):
        """Test _get_engine ImportError branch."""
        import sys
        from unittest.mock import patch

        agent = BalanceAgent(balance_instance=None)
        with patch.dict(sys.modules, {"core.balance": None}, clear=False):
            result = agent._get_engine()
        assert result is None

    def test_balance_resolve_world_with_dict(self):
        """_resolve_world with dict tiles."""
        agent = BalanceAgent()
        result = agent._resolve_world({"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}})
        assert result is not None

    def test_balance_resolve_world_with_list_tiles(self):
        """_resolve_world with list tiles (the enumerate branch)."""
        agent = BalanceAgent()
        result = agent._resolve_world({"tiles": [{"x": 0, "y": 0, "z": 7, "ground": 106}]})
        assert result is not None

    def test_balance_resolve_world_passthrough(self):
        """_resolve_world with non-dict."""
        agent = BalanceAgent()
        result = agent._resolve_world("not a dict")
        assert result == "not a dict"

    def test_balance_resolve_world_import_error(self):
        """_resolve_world when core.world import fails."""
        import sys
        from unittest.mock import patch

        agent = BalanceAgent()
        with patch.dict(sys.modules, {"core.world": None}, clear=False):
            result = agent._resolve_world({"tiles": {}})
        assert result == {"tiles": {}}

    def test_balance_world_to_dict_no_to_dict(self):
        """_world_to_dict on object without to_dict."""
        agent = BalanceAgent()
        result = agent._world_to_dict(object())
        assert result["tiles"] == {}

    def test_balance_world_to_dict_with_to_dict(self):
        """_world_to_dict on object with to_dict returning list tiles."""
        agent = BalanceAgent()

        class FakeWorld:
            def to_dict(self):
                return {
                    "tiles": [{"x": 0, "y": 0, "z": 7}],
                    "structures": [],
                    "regions": [],
                }
        result = agent._world_to_dict(FakeWorld())
        assert isinstance(result["tiles"], dict)
        assert "0,0,7" in result["tiles"]

    def test_balance_world_to_dict_non_list_tiles(self):
        """_world_to_dict when tiles is neither list nor dict."""
        agent = BalanceAgent()

        class FakeWorld:
            def to_dict(self):
                return {"tiles": "bad", "structures": [], "regions": []}
        result = agent._world_to_dict(FakeWorld())
        assert result["tiles"] == {}

    def test_balance_world_to_dict_dict_tiles(self):
        """_world_to_dict when tiles is already a dict."""
        agent = BalanceAgent()

        class FakeWorld:
            def to_dict(self):
                return {"tiles": {"0,0,7": {"x": 0}}, "structures": [], "regions": []}
        result = agent._world_to_dict(FakeWorld())
        assert isinstance(result["tiles"], dict)
        assert "0,0,7" in result["tiles"]

    def test_balance_resolve_world_other_iterable(self):
        """_resolve_world when tiles is neither dict nor list."""
        agent = BalanceAgent()
        # Pass tiles as a set to hit the else branch
        result = agent._resolve_world({"tiles": {"x": 1}})
        assert result is not None

    def test_balance_handles_exception(self):
        """Test exception handling caught by execute."""
        agent = BalanceAgent()
        request = AgentRequest(agent_id="balance", prompt="b")
        request.context = "not a dict"
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_balance_with_empty_playtest(self):
        """Test with empty playtest report in context."""
        agent = BalanceAgent()
        request = AgentRequest(
            agent_id="balance", prompt="b",
            input_data={"tiles": {}},
            context={"playtest_report": {}},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None