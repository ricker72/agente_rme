"""
Integration test for agent error recovery in the multi-agent pipeline.
"""

import pytest
from typing import Any, Dict, Optional
from agente_rme.core.agents import (
    OrchestratorAgent, AgentRegistry, BaseAgent, MultiAgentResult
)
from agente_rme.core.agents.contracts import AgentRequest, AgentResponse


class FailingAgent(BaseAgent):
    """Agent that always fails."""
    AGENT_ID = "failing"

    def execute(self, request: AgentRequest) -> AgentResponse:
        return AgentResponse.error_response(
            self.agent_id, "Intentional failure"
        )


class PartiallyFailingAgent(BaseAgent):
    """Agent that fails if parameter is set."""
    AGENT_ID = "conditional"

    def __init__(self, should_fail: bool = False) -> None:
        super().__init__()
        self.should_fail = should_fail

    def execute(self, request: AgentRequest) -> AgentResponse:
        if self.should_fail:
            return AgentResponse.error_response(
                self.agent_id, "Conditional failure"
            )
        return AgentResponse.success_response(
            self.agent_id,
            output_data={"status": "ok"},
        )


class TestAgentErrorRecovery:
    def test_pipeline_continues_after_agent_failure(self, tmpdir):
        """Pipeline should continue when a non-critical agent fails."""
        registry = AgentRegistry()

        # Create a pipeline where one agent fails
        class OkArchitect(BaseAgent):
            AGENT_ID = "architect"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id, output_data={"plan": "test"})

        class FailingMapper(BaseAgent):
            AGENT_ID = "mapper"
            def execute(self, request):
                return AgentResponse.error_response(self.agent_id, "Mapper failed")

        class OkExpansion(BaseAgent):
            AGENT_ID = "expansion"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id, output_data={"world": "expanded"})

        class OkQuest(BaseAgent):
            AGENT_ID = "quest"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id, output_data={"campaign": {}})

        class OkPlaytest(BaseAgent):
            AGENT_ID = "playtest"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id, output_data={"report": {}})

        class OkBalance(BaseAgent):
            AGENT_ID = "balance"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id, output_data={"world": "balanced"})

        class OkQA(BaseAgent):
            AGENT_ID = "qa"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id, output_data={"qa": "passed"})

        class OkExport(BaseAgent):
            AGENT_ID = "export"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id)

        registry.register(OkArchitect())
        registry.register(FailingMapper())
        registry.register(OkExpansion())
        registry.register(OkQuest())
        registry.register(OkPlaytest())
        registry.register(OkBalance())
        registry.register(OkQA())
        registry.register(OkExport())

        orch = OrchestratorAgent(
            registry=registry,
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        request = AgentRequest(prompt="Test pipeline recovery")
        response = orch.execute(request)
        result = response.output_data

        # Pipeline should complete (with errors)
        assert response.success is True
        assert result is not None
        assert result["metrics"]["total_agents"] == 8
        assert result["metrics"]["successful_agents"] == 7
        assert result["metrics"]["agent_failures"] == ["mapper"]

    def test_empty_registry_handling(self, tmpdir):
        """Orchestrator should handle empty registry gracefully."""
        registry = AgentRegistry()
        # Register only some agents
        class BasicAgent(BaseAgent):
            AGENT_ID = "architect"
            def execute(self, request):
                return AgentResponse.success_response(self.agent_id)

        registry.register(BasicAgent())

        orch = OrchestratorAgent(
            registry=registry,
            pipeline_order=["architect", "mapper", "quest"],
            output_dir=str(tmpdir),
        )
        request = AgentRequest(prompt="Test")
        response = orch.execute(request)
        assert response.success is True

    def test_all_agents_fail_gracefully(self, tmpdir):
        """Pipeline should complete even if all agents fail."""
        registry = AgentRegistry()

        for agent_id in ["architect", "mapper", "expansion", "quest",
                          "playtest", "balance", "qa", "export"]:
            class FailAll(BaseAgent):
                AGENT_ID = agent_id
                def execute(self, request):
                    return AgentResponse.error_response(self.agent_id, f"{agent_id} failed")

            registry.register(FailAll())

        orch = OrchestratorAgent(
            registry=registry,
            output_dir=str(tmpdir),
        )
        request = AgentRequest(prompt="Test all fail")
        response = orch.execute(request)
        result = response.output_data

        assert response.success is True
        assert result["metrics"]["successful_agents"] == 0
        assert len(result["metrics"]["agent_failures"]) == 8
        assert result["metrics"]["total_agents"] == 8
