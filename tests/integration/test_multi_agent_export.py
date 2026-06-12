"""
Integration test for multi-agent export artifact generation.
"""

import os
import json
from core.agents import OrchestratorAgent, AgentRegistry, BaseAgent
from core.agents.contracts import AgentRequest, AgentResponse


class CreatorAgent(BaseAgent):
    """Agent that creates test world data."""

    AGENT_ID = "architect"

    def execute(self, request):
        return AgentResponse.success_response(
            self.agent_id,
            output_data={
                "primary_theme": "issavi",
                "themes": ["issavi", "roshamuul"],
                "level_min": 300,
                "level_max": 500,
                "cities": [{"name": "Issavi City", "population": 500}],
                "hunting_zones": [
                    {"name": "Issavi Hunt", "min_level": 300, "max_level": 400}
                ],
            },
        )


class WorldBuilderAgent(BaseAgent):
    """Agent that builds a world model dict."""

    AGENT_ID = "mapper"

    def execute(self, request):
        return AgentResponse.success_response(
            self.agent_id,
            output_data={
                "tiles": {},
                "structures": [],
                "regions": [
                    {"name": "Issavi", "theme": "issavi"},
                    {"name": "Roshamuul", "theme": "roshamuul"},
                ],
            },
        )


class DoNothingAgent(BaseAgent):
    """Agent that passes through data unchanged."""

    AGENT_ID = ""

    def __init__(self, agent_id: str) -> None:
        super().__init__()
        self.AGENT_ID = agent_id

    def execute(self, request):
        return AgentResponse.success_response(
            self.agent_id,
            output_data=request.input_data,
        )


class CampaignAgent(BaseAgent):
    """Agent that creates campaign data."""

    AGENT_ID = "quest"

    def execute(self, request):
        return AgentResponse.success_response(
            self.agent_id,
            output_data={
                "theme": "issavi",
                "name": "Chronicles of Issavi",
                "lore": [{"title": "The Rise", "content": "Ancient Issavi..."}],
                "factions": [{"name": "Issavi Council"}],
                "npcs": [{"name": "High Priest"}],
                "main_story": {"title": "The Prophecy", "quests": []},
            },
        )


class TestMultiAgentExport:
    def test_export_generates_artifacts(self, tmpdir):
        """Test export agent generates expected artifacts."""
        registry = AgentRegistry()
        registry.register(CreatorAgent())
        registry.register(WorldBuilderAgent())
        registry.register(DoNothingAgent("expansion"))
        registry.register(CampaignAgent())
        registry.register(DoNothingAgent("playtest"))
        registry.register(DoNothingAgent("balance"))
        registry.register(DoNothingAgent("qa"))
        registry.register(DoNothingAgent("export"))

        orch = OrchestratorAgent(
            registry=registry,
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        request = AgentRequest(prompt="Generate Issavi map")
        response = orch.execute(request)
        assert response.success is True
        result = response.output_data
        assert result is not None
        assert "errors" in result
        assert "metrics" in result

    def test_export_report_json(self, tmpdir):
        """Test that report.json is generated after export."""
        orch = OrchestratorAgent(
            output_dir=str(tmpdir),
            log_dir=str(tmpdir),
        )
        orch.execute_prompt("Generate test map")
        result_path = os.path.join(str(tmpdir), "multi_agent_result.json")
        assert os.path.exists(result_path)
        with open(result_path) as f:
            data = json.load(f)
        assert "workflow_id" in data
        assert "metrics" in data

    def test_agent_metrics_file(self, tmpdir):
        """Test that agent_metrics.json contains correct structure."""
        orch = OrchestratorAgent(output_dir=str(tmpdir))
        orch.execute_prompt("Generate test")
        metrics_path = os.path.join(str(tmpdir), "agent_metrics.json")
        assert os.path.exists(metrics_path)
        with open(metrics_path) as f:
            metrics = json.load(f)
        assert "agent_times" in metrics
        assert "agent_failures" in metrics
        assert "agent_success_rate" in metrics
