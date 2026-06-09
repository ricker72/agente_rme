"""
Integration test for the full multi-agent pipeline.
"""

import pytest
import os
import json
from agente_rme.core.agents import OrchestratorAgent, MultiAgentResult
from agente_rme.core.agents.contracts import AgentRequest


class TestMultiAgentPipeline:
    """Full pipeline integration tests."""

    def test_full_pipeline_execution(self, tmpdir):
        """Test that all 8 agents execute in sequence."""
        orch = OrchestratorAgent(
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        result = orch.execute_prompt(
            "Generate Issavi city for level 300",
            world_width=100,
            world_height=100,
        )
        assert isinstance(result, MultiAgentResult)
        assert result.success is True
        assert len(result.errors) == 0

    def test_pipeline_metrics(self, tmpdir):
        """Test that pipeline metrics are complete."""
        orch = OrchestratorAgent(
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        result = orch.execute_prompt("Generate Roshamuul hunt")
        metrics = result.metrics
        assert metrics["total_agents"] == 8
        assert metrics["successful_agents"] == 8
        assert metrics["agent_success_rate"] == 100.0
        assert len(metrics["agent_times"]) == 8

    def test_pipeline_artifacts(self, tmpdir):
        """Test that artifacts are exported."""
        orch = OrchestratorAgent(
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        result = orch.execute_prompt(
            "Generate Issavi map",
            input_data={"tiles": {}, "structures": [], "regions": []},
        )
        # At minimum, the result file should be saved
        result_path = os.path.join(str(tmpdir), "multi_agent_result.json")
        assert os.path.exists(result_path)
        with open(result_path) as f:
            saved = json.load(f)
        assert "workflow_id" in saved

    def test_pipeline_with_custom_parameters(self, tmpdir):
        """Test pipeline with custom parameters."""
        orch = OrchestratorAgent(output_dir=str(tmpdir))
        result = orch.execute_prompt(
            "Generate Issavi expansion",
            theme="issavi",
            level_min=300,
            level_max=500,
            max_hunts=3,
        )
        assert isinstance(result, MultiAgentResult)
        assert result.success is True

    def test_pipeline_logs_created(self, tmpdir):
        """Test that execution logs are created."""
        orch = OrchestratorAgent(
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        orch.execute_prompt("Test generation")
        log_files = [f for f in os.listdir(str(tmpdir)) if f.endswith(".log")]
        assert len(log_files) >= 1

    def test_pipeline_metrics_file_created(self, tmpdir):
        """Test that agent_metrics.json is created."""
        orch = OrchestratorAgent(output_dir=str(tmpdir))
        orch.execute_prompt("Test generation")
        metrics_path = os.path.join(str(tmpdir), "agent_metrics.json")
        assert os.path.exists(metrics_path)
        with open(metrics_path) as f:
            metrics = json.load(f)
        assert "execution_time" in metrics
        assert "agent_times" in metrics
        assert "agent_success_rate" in metrics