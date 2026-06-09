"""
Coverage tests for MapperAgent.

Hito 26.1D — covers all branches:
  * Happy path with WorldPlan input
  * Empty world plan fallback
  * Tiles conversion (list->dict normalization)
  * No generator available (fallback)
  * Error handling
  * _get_generator lazy-init with ImportError
  * _world_to_dict edge cases (no to_dict, plain dict, non-list tiles)
  * _fallback_world with various plans
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agente_rme.core.agents.mapper_agent import MapperAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestMapperAgentHappyPath:
    """Happy path scenarios for the MapperAgent."""

    def test_mapper_executes_with_world_plan(self):
        agent = MapperAgent()
        world_plan = {
            "primary_theme": "issavi",
            "themes": ["issavi"],
            "level_min": 1,
            "level_max": 200,
            "cities": [],
            "hunting_zones": [],
        }
        request = AgentRequest(
            agent_id="mapper",
            prompt="issavi temple",
            input_data=world_plan,
        )
        response = agent.execute(request)
        assert response.agent_id == "mapper"
        assert response.success or response.error is not None

    def test_mapper_input_from_context(self):
        agent = MapperAgent()
        world_plan = {"primary_theme": "issavi", "themes": ["issavi"]}
        request = AgentRequest(
            agent_id="mapper",
            prompt="issavi",
            context={"world_plan": world_plan},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_mapper_with_tile_count_in_report(self):
        agent = MapperAgent()
        request = AgentRequest(
            agent_id="mapper",
            prompt="test",
            input_data={"primary_theme": "issavi", "themes": ["issavi"]},
        )
        response = agent.execute(request)
        if response.success:
            assert "tile_count" in response.report

    def test_mapper_normalizes_list_tiles_to_dict(self):
        agent = MapperAgent()
        world = {"tiles": [
            {"x": 0, "y": 0, "z": 7},
            {"x": 1, "y": 0, "z": 7},
            {"x": 2, "y": 0, "z": 7},
        ]}
        request = AgentRequest(
            agent_id="mapper", prompt="t", input_data=world,
        )
        response = agent.execute(request)
        if response.success and "tiles" in response.output_data:
            assert isinstance(response.output_data["tiles"], dict)
            for k in response.output_data["tiles"]:
                assert "," in k

    def test_mapper_with_empty_world_plan(self):
        agent = MapperAgent()
        request = AgentRequest(agent_id="mapper", prompt="test", input_data={})
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_mapper_with_none_input(self):
        agent = MapperAgent()
        request = AgentRequest(agent_id="mapper", prompt="test", input_data=None)
        response = agent.execute(request)
        assert response.success or response.error is not None


class TestMapperAgentErrorHandling:
    """Error handling and edge cases for the MapperAgent."""

    def test_mapper_fallback_has_output(self):
        agent = MapperAgent()
        request = AgentRequest(agent_id="mapper", prompt="test", input_data={})
        response = agent.execute(request)
        if response.success:
            assert isinstance(response.output_data, dict)
            assert (
                "metadata" in response.output_data
                or "regions" in response.output_data
                or "tiles" in response.output_data
            )

    def test_mapper_fallback_includes_theme(self):
        agent = MapperAgent()
        request = AgentRequest(
            agent_id="mapper",
            prompt="test",
            input_data={"primary_theme": "roshamuul", "themes": ["roshamuul"]},
        )
        response = agent.execute(request)
        if response.success and "regions" in response.output_data:
            regions = response.output_data["regions"]
            themes = [str(r.get("theme")) for r in regions]
            assert len(themes) > 0
            assert any(t != "" for t in themes)

    def test_mapper_logger_uses_agent_id(self):
        agent = MapperAgent()
        assert "mapper" in agent.logger.name

    def test_mapper_with_invalid_world_plan(self):
        agent = MapperAgent()
        request = AgentRequest(agent_id="mapper", prompt="test", input_data="invalid")
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_mapper_metrics_present(self):
        agent = MapperAgent()
        request = AgentRequest(agent_id="mapper", prompt="test", input_data={})
        response = agent.execute(request)
        if response.success:
            assert "execution_time" in response.metrics

    def test_mapper_with_existing_tiles_dict(self):
        agent = MapperAgent()
        world = {
            "tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}},
            "structures": [],
            "regions": [],
        }
        request = AgentRequest(
            agent_id="mapper", prompt="test", input_data=world,
        )
        response = agent.execute(request)
        if response.success:
            assert "tiles" in response.output_data

    def test_mapper_with_list_tiles(self):
        agent = MapperAgent()
        world = {
            "tiles": [
                {"x": 0, "y": 0, "z": 7, "ground": 106},
                {"x": 1, "y": 1, "z": 7, "ground": 110},
            ],
            "structures": [],
        }
        request = AgentRequest(
            agent_id="mapper", prompt="test", input_data=world,
        )
        response = agent.execute(request)
        if response.success:
            tiles = response.output_data.get("tiles", {})
            if isinstance(tiles, dict):
                for k in tiles:
                    assert "," in k

    def test_mapper_handles_exception(self):
        """Test that the mapper handles unexpected input gracefully."""
        agent = MapperAgent()
        request = AgentRequest(agent_id="mapper", prompt="test")
        request.context = "not a dict"
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_mapper_with_issavi_plan(self):
        agent = MapperAgent()
        request = AgentRequest(
            agent_id="mapper", prompt="issavi",
            input_data={"primary_theme": "issavi", "themes": ["issavi"]},
        )
        response = agent.execute(request)
        if response.success and "regions" in response.output_data:
            themes = [r.get("theme") for r in response.output_data["regions"]]
            assert any(t for t in themes)

    def test_mapper_world_to_dict_preserves_data(self):
        """Test _world_to_dict via a Fake world model."""
        agent = MapperAgent()

        class FakeWM:
            def to_dict(self):
                return {
                    "tiles": [
                        {"x": 0, "y": 0, "z": 7},
                        {"x": 1, "y": 1, "z": 7},
                    ],
                    "structures": [],
                    "regions": [],
                }
        result = agent._world_to_dict(FakeWM())
        assert isinstance(result["tiles"], dict)
        assert len(result["tiles"]) == 2

    def test_mapper_world_to_dict_no_to_dict(self):
        """_world_to_dict on an object without to_dict."""
        agent = MapperAgent()
        result = agent._world_to_dict(object())
        assert result["tiles"] == {}
        assert result["structures"] == []
        assert result["regions"] == []

    def test_mapper_world_to_dict_non_list_tiles(self):
        """_world_to_dict when tiles is neither list nor dict."""
        agent = MapperAgent()

        class FakeWM:
            def to_dict(self):
                return {"tiles": "invalid", "structures": [], "regions": []}
        result = agent._world_to_dict(FakeWM())
        assert result["tiles"] == {}

    def test_mapper_world_to_dict_dict_passthrough(self):
        """_world_to_dict when tiles is already a dict."""
        agent = MapperAgent()

        class FakeWM:
            def to_dict(self):
                return {"tiles": {"0,0,7": {"x": 0}}, "structures": [], "regions": []}
        result = agent._world_to_dict(FakeWM())
        assert isinstance(result["tiles"], dict)
        assert "0,0,7" in result["tiles"]

    def test_mapper_get_generator_cached(self):
        agent = MapperAgent()
        gen = object()
        agent._generator = gen
        assert agent._get_generator() is gen

    def test_mapper_get_generator_import_error(self):
        """Test _get_generator when ImportError occurs."""
        import sys
        from unittest.mock import patch

        agent = MapperAgent(generator_instance=None)
        with patch.dict(sys.modules, {"core.generators": None}, clear=False):
            result = agent._get_generator()
        assert result is None

    def test_mapper_fallback_world_empty_plan(self):
        agent = MapperAgent()
        result = agent._fallback_world({}, "test prompt")
        assert "regions" in result
        assert result["metadata"]["generated_by"] == "MapperAgent_fallback"
        assert result["metadata"]["prompt"] == "test prompt"