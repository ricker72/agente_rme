"""
Tests for OrchestratorAgent.
"""

import pytest
import os
from agente_rme.core.agents import (
    OrchestratorAgent, AgentRegistry, BaseAgent, MultiAgentResult
)
from agente_rme.core.agents.contracts import AgentRequest, AgentResponse


class TestOrchestratorAgent:
    def test_agent_id(self):
        orch = OrchestratorAgent()
        assert orch.agent_id == "orchestrator"

    def test_execute_with_prompt(self):
        orch = OrchestratorAgent()
        request = AgentRequest(prompt="Generate Issavi city")
        response = orch.execute(request)
        assert response.success is True
        result = response.output_data
        assert result is not None
        assert "workflow_id" in result
        assert "metrics" in result

    def test_execute_empty_prompt(self):
        orch = OrchestratorAgent()
        request = AgentRequest(prompt="")
        response = orch.execute(request)
        assert response.success is False

    def test_execute_prompt_returns_multi_agent_result(self):
        orch = OrchestratorAgent()
        result = orch.execute_prompt("Generate Issavi map")
        assert isinstance(result, MultiAgentResult)
        assert result.workflow_id != ""
        assert "execution_time" in result.metrics

    def test_pipeline_runs_all_agents(self):
        orch = OrchestratorAgent()
        request = AgentRequest(prompt="Generate test map")
        response = orch.execute(request)
        result = response.output_data
        assert result is not None
        assert result["metrics"]["total_agents"] == 8
        assert result["metrics"]["successful_agents"] == 8

    def test_metrics_generated(self):
        orch = OrchestratorAgent()
        result = orch.execute_prompt("Test generation")
        assert "execution_time" in result.metrics
        assert "agent_times" in result.metrics
        assert "agent_failures" in result.metrics
        assert "agent_success_rate" in result.metrics

    def test_workflow_id_created(self):
        orch = OrchestratorAgent()
        result = orch.execute_prompt("Test")
        assert len(result.workflow_id) == 8

    def test_result_summary(self):
        orch = OrchestratorAgent()
        result = orch.execute_prompt("Test generation")
        summary = result.summary
        assert "Workflow" in summary
        assert result.workflow_id in summary

    def test_success_property(self):
        orch = OrchestratorAgent()
        result = orch.execute_prompt("Test generation")
        assert result.success is True

    def test_custom_pipeline(self):
        registry = AgentRegistry()
        orch = OrchestratorAgent(
            registry=registry,
            pipeline_order=["architect", "mapper", "quest"],
        )
        request = AgentRequest(prompt="Generate test")
        response = orch.execute(request)
        assert response.success is True

    def test_agent_metrics_file_created(self, tmpdir):
        orch = OrchestratorAgent(output_dir=str(tmpdir))
        orch.execute_prompt("Test")
        metrics_path = os.path.join(str(tmpdir), "agent_metrics.json")
        assert os.path.exists(metrics_path)

    def test_log_files_created(self, tmpdir):
        orch = OrchestratorAgent(
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        result = orch.execute_prompt("Test")
        log_files = [f for f in os.listdir(str(tmpdir)) if f.startswith("workflow_")]
        assert len(log_files) > 0