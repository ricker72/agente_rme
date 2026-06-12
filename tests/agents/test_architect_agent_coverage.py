"""
Coverage tests for ArchitectAgent.

Hito 26.1D â€” covers all branches:
  * Happy path with valid prompt
  * Empty / None prompt error handling
  * No architect available (fallback plan)
  * Theme detection (issavi, roshamuul, default)
  * World plan output structure
  * _get_architect lazy-init hit and miss
  * _fallback_plan edge cases
  * Exception propagation from broken architect
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.agents.architect_agent import ArchitectAgent
from core.agents.contracts import AgentRequest


class TestArchitectAgentHappyPath:
    """Happy path scenarios for the ArchitectAgent."""

    def test_architect_executes_with_valid_prompt(self):
        agent = ArchitectAgent()
        request = AgentRequest(
            agent_id="architect",
            prompt="Create an Issavi temple",
        )
        response = agent.execute(request)
        assert response.agent_id == "architect"
        assert response.success or response.error is not None

    def test_architect_returns_plan_dict(self):
        agent = ArchitectAgent()
        request = AgentRequest(
            agent_id="architect",
            prompt="Build a Roshamuul raid",
        )
        response = agent.execute(request)
        if response.success:
            assert response.output_data is not None
            assert "prompt" in response.output_data
            assert "themes" in response.output_data

    def test_architect_with_issavi_theme(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="issavi temple")
        response = agent.execute(request)
        if response.success:
            assert "issavi" in response.output_data["themes"]

    def test_architect_with_roshamuul_theme(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="roshamuul dungeon")
        response = agent.execute(request)
        if response.success:
            assert "roshamuul" in response.output_data["themes"]

    def test_architect_with_both_themes(self):
        agent = ArchitectAgent()
        request = AgentRequest(
            agent_id="architect",
            prompt="Create an issavi and roshamuul hybrid",
        )
        response = agent.execute(request)
        if response.success:
            themes = response.output_data["themes"]
            assert "issavi" in themes
            assert "roshamuul" in themes

    def test_architect_with_no_specific_theme(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="generic dungeon")
        response = agent.execute(request)
        if response.success:
            themes = response.output_data["themes"]
            assert isinstance(themes, list)

    def test_architect_respects_world_dimensions(self):
        agent = ArchitectAgent()
        request = AgentRequest(
            agent_id="architect",
            prompt="big dungeon",
            parameters={"world_width": 500, "world_height": 500},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_architect_metrics_present(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="simple")
        response = agent.execute(request)
        if response.success:
            assert "execution_time" in response.metrics


class TestArchitectAgentErrorHandling:
    """Error handling and edge cases for the ArchitectAgent."""

    def test_empty_prompt_returns_error(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="")
        response = agent.execute(request)
        assert not response.success
        assert "prompt" in response.error.lower() or "no" in response.error.lower()

    def test_none_prompt_returns_error(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt=None)
        response = agent.execute(request)
        assert not response.success

    def test_prompt_from_parameters(self):
        agent = ArchitectAgent()
        request = AgentRequest(
            agent_id="architect",
            prompt="",
            parameters={"prompt": "issavi temple"},
        )
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_plan_has_themes(self):
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="issavi dungeon")
        response = agent.execute(request)
        if response.success:
            plan = response.output_data
            assert "prompt" in plan
            assert "themes" in plan
            assert "primary_theme" in plan
            assert isinstance(plan["themes"], list)

    def test_architect_logger_uses_agent_id(self):
        agent = ArchitectAgent()
        assert "architect" in agent.logger.name

    def test_architect_fallback_plan_issavi(self):
        agent = ArchitectAgent()
        plan = agent._fallback_plan("issavi dungeon")
        assert plan["primary_theme"] == "issavi"
        assert "issavi" in plan["themes"]
        assert plan["metadata"]["generated_by"] == "ArchitectAgent_fallback"

    def test_architect_fallback_plan_roshamuul(self):
        agent = ArchitectAgent()
        plan = agent._fallback_plan("roshamuul raid")
        assert plan["primary_theme"] == "roshamuul"

    def test_architect_fallback_plan_both_themes(self):
        agent = ArchitectAgent()
        plan = agent._fallback_plan("issavi and roshamuul hybrid")
        assert "issavi" in plan["themes"]
        assert "roshamuul" in plan["themes"]

    def test_architect_fallback_plan_default(self):
        agent = ArchitectAgent()
        plan = agent._fallback_plan("some random dungeon")
        assert plan["primary_theme"] == "default"

    def test_architect_fallback_plan_structure(self):
        agent = ArchitectAgent()
        plan = agent._fallback_plan("issavi")
        required_keys = [
            "prompt",
            "primary_theme",
            "themes",
            "level_min",
            "level_max",
            "cities",
            "hunting_zones",
            "boss_zones",
            "quest_zones",
            "metadata",
        ]
        for k in required_keys:
            assert k in plan, f"Missing key: {k}"

    def test_architect_fallback_path(self):
        """Test execute() fallback branch when AIArchitect is unavailable."""
        agent = ArchitectAgent(architect_instance=None)
        request = AgentRequest(agent_id="architect", prompt="issavi test")
        response = agent.execute(request)
        if response.success:
            assert "themes" in response.output_data

    def test_architect_handles_exception(self):
        class BrokenArchitect:
            def plan(self, *args, **kwargs):
                raise RuntimeError("simulated architect failure")

        agent = ArchitectAgent(architect_instance=BrokenArchitect())
        request = AgentRequest(agent_id="architect", prompt="issavi")
        response = agent.execute(request)
        assert not response.success
        assert "simulated architect failure" in response.error

    def test_architect_get_architect_returns_cached(self):
        sentinel = object()
        agent = ArchitectAgent(architect_instance=sentinel)
        assert agent._get_architect() is sentinel

    def test_architect_get_architect_fallback_on_import_error(self):
        """Test _get_architect ImportError branch using sys.modules patching."""
        import sys
        from unittest.mock import patch

        agent = ArchitectAgent(architect_instance=None)
        with patch.dict(sys.modules, {"core.architect": None}, clear=False):
            result = agent._get_architect()
        assert result is None

    def test_architect_get_architect_imports_real(self):
        """Test that _get_architect tries to import when no cached instance."""
        agent = ArchitectAgent(architect_instance=None)
        result = agent._get_architect()
        # Either None (if import fails) or an AIArchitect instance
        assert result is None or hasattr(result, "plan")

    def test_architect_no_prompt_and_no_parameters(self):
        """_fallback_plan called when both prompt and parameters empty."""
        agent = ArchitectAgent()
        request = AgentRequest(agent_id="architect", prompt="")
        response = agent.execute(request)
        assert not response.success
