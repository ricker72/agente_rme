"""
Tests for ExportAgent.
"""

import os
import json
from core.agents import ExportAgent
from core.agents.contracts import AgentRequest


class TestExportAgent:
    def test_agent_id(self):
        agent = ExportAgent()
        assert agent.agent_id == "export"

    def test_execute_with_prompt(self, tmpdir):
        agent = ExportAgent(output_dir=str(tmpdir))
        request = AgentRequest(prompt="Export Issavi map")
        response = agent.execute(request)
        assert response.success is True

    def test_execute_with_world_data(self, tmpdir):
        agent = ExportAgent(output_dir=str(tmpdir))
        request = AgentRequest(
            prompt="Export",
            input_data={"tiles": {}, "structures": [], "regions": []},
            context={
                "campaign": {"theme": "issavi"},
                "playtest_report": {"player_level": 300},
                "qa_report": {"score": 0.9},
            },
        )
        response = agent.execute(request)
        assert response.success is True

    def test_artifacts_created(self, tmpdir):
        agent = ExportAgent(output_dir=str(tmpdir))
        request = AgentRequest(
            prompt="Export",
            input_data={"tiles": {}, "structures": [], "regions": []},
            context={
                "campaign": {"theme": "issavi"},
                "playtest_report": {"player_level": 300},
            },
        )
        response = agent.execute(request)
        assert response.success is True
        # Should have created some artifact files
        assert len(response.artifacts) > 0

    def test_report_json_created(self, tmpdir):
        agent = ExportAgent(output_dir=str(tmpdir))
        request = AgentRequest(
            prompt="Export",
            input_data={"tiles": {}, "structures": [], "regions": []},
            context={
                "campaign": {"theme": "issavi"},
            },
        )
        agent.execute(request)
        report_path = os.path.join(str(tmpdir), "report.json")
        assert os.path.exists(report_path)
        with open(report_path) as f:
            report = json.load(f)
        assert "artifacts" in report

    def test_metrics_contains_execution_time(self, tmpdir):
        agent = ExportAgent(output_dir=str(tmpdir))
        request = AgentRequest(prompt="Test")
        response = agent.execute(request)
        assert "execution_time" in response.metrics

    def test_campaign_json_created(self, tmpdir):
        agent = ExportAgent(output_dir=str(tmpdir))
        request = AgentRequest(
            prompt="Export",
            context={"campaign": {"theme": "issavi", "name": "Test"}},
        )
        agent.execute(request)
        campaign_path = os.path.join(str(tmpdir), "campaign.json")
        assert os.path.exists(campaign_path)
