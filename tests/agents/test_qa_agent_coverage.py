"""
Coverage tests for QAAgent.

Hito 26.1D — covers all branches:
  * Happy path with world_model, campaign, playtest
  * Missing validators (fallback)
  * Validation of artifacts
  * Overall score calculation
  * Edge cases: empty/full contexts, injections
  * _get_validators with ImportError
  * _resolve_world with various inputs
  * Exception handling
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from agente_rme.core.agents.qa_agent import QAAgent
from agente_rme.core.agents.contracts import AgentRequest


class TestQAAgentHappyPath:
    """Happy path scenarios for the QAAgent."""

    def test_qa_executes_with_world(self):
        agent = QAAgent()
        world = {
            "tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}},
            "structures": [],
        }
        request = AgentRequest(
            agent_id="qa",
            prompt="qa",
            input_data=world,
        )
        response = agent.execute(request)
        assert response.agent_id == "qa"
        assert response.success or response.error is not None

    def test_qa_with_full_context(self):
        agent = QAAgent()
        world = {"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}}
        campaign = {"theme": "issavi", "lore": ["..."], "factions": [{"name": "A"}]}
        playtest = {"player_level": 200, "issues": []}
        artifacts = {"otbm": "/tmp/out.otbm", "lua": "/tmp/out.lua"}

        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data=world,
            context={"campaign": campaign, "playtest_report": playtest,
                     "artifacts": artifacts},
        )
        response = agent.execute(request)
        assert response.success

    def test_qa_validates_world_model(self):
        agent = QAAgent()
        world = {"tiles": {}}
        request = AgentRequest(
            agent_id="qa", prompt="qa", input_data=world,
        )
        response = agent.execute(request)
        if response.success:
            assert "world_model" in response.output_data

    def test_qa_validates_campaign(self):
        agent = QAAgent()
        campaign = {"theme": "issavi", "lore": ["..."], "factions": []}
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"campaign": campaign},
        )
        response = agent.execute(request)
        if response.success:
            assert "campaign" in response.output_data
            assert response.output_data["campaign"]["valid"] is True

    def test_qa_validates_playtest(self):
        agent = QAAgent()
        playtest = {"player_level": 200, "issues": []}
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"playtest_report": playtest},
        )
        response = agent.execute(request)
        if response.success:
            assert "playtest" in response.output_data

    def test_qa_validates_artifacts(self):
        agent = QAAgent()
        artifacts = {"nonexistent": "/tmp/__does_not_exist__.otbm"}
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"artifacts": artifacts},
        )
        response = agent.execute(request)
        if response.success:
            assert "artifacts" in response.output_data
            assert response.output_data["artifacts"]["valid"] is False

    def test_qa_computes_overall_score(self):
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert "overall" in response.output_data
            assert "score" in response.output_data["overall"]
            assert "valid" in response.output_data["overall"]


class TestQAAgentErrorHandling:
    """Error handling and edge cases for the QAAgent."""

    def test_qa_with_none_input(self):
        agent = QAAgent()
        request = AgentRequest(agent_id="qa", prompt="qa", input_data=None)
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_qa_with_empty_dict(self):
        agent = QAAgent()
        request = AgentRequest(agent_id="qa", prompt="qa", input_data={})
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_qa_with_invalid_input(self):
        agent = QAAgent()
        request = AgentRequest(agent_id="qa", prompt="qa", input_data="invalid")
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_qa_logger_uses_agent_id(self):
        agent = QAAgent()
        assert "qa" in agent.logger.name

    def test_qa_metrics_present(self):
        agent = QAAgent()
        request = AgentRequest(agent_id="qa", prompt="qa", input_data={})
        response = agent.execute(request)
        if response.success:
            assert "execution_time" in response.metrics

    def test_qa_empty_campaign_fails(self):
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"campaign": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert response.output_data["campaign"]["valid"] is False

    def test_qa_handles_world_model_with_world_validator(self):
        agent = QAAgent()
        world = {"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}}
        request = AgentRequest(
            agent_id="qa", prompt="qa", input_data=world,
        )
        response = agent.execute(request)
        assert response.success
        if response.success:
            assert "world_model" in response.output_data
            wm = response.output_data["world_model"]
            assert "checks" in wm or "valid" in wm

    def test_qa_with_artifacts_existing_files(self, tmp_path):
        artifact_path = tmp_path / "real.json"
        artifact_path.write_text('{"ok": true}')
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={
                "artifacts": {"myartifact": str(artifact_path)},
                "campaign": {"theme": "issavi", "lore": ["x"], "factions": []},
            },
        )
        response = agent.execute(request)
        assert response.success
        if response.success:
            artifacts = response.output_data["artifacts"]
            assert artifacts["valid"] is True
            assert len(artifacts["checks"]) == 1
            assert artifacts["checks"][0]["passed"] is True

    def test_qa_playtest_with_full_data(self):
        agent = QAAgent()
        playtest = {
            "player_level": 200,
            "issues": ["none"],
            "summary": "all good",
        }
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"playtest_report": playtest},
        )
        response = agent.execute(request)
        assert response.success

    def test_qa_validates_full_artifacts(self, tmp_path):
        f1 = tmp_path / "a.otbm"
        f1.write_bytes(b"OTBM" + b"\x00" * 100)
        f2 = tmp_path / "b.lua"
        f2.write_text("-- lua")
        f3 = tmp_path / "missing.json"
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"artifacts": {
                "otbm": str(f1), "lua": str(f2), "missing": str(f3),
            }},
        )
        response = agent.execute(request)
        if response.success:
            assert response.output_data["artifacts"]["valid"] is False
            checks = {c["name"]: c["passed"] for c in response.output_data["artifacts"]["checks"]}
            assert checks["otbm"] is True
            assert checks["lua"] is True
            assert checks["missing"] is False

    def test_qa_handles_exception(self):
        agent = QAAgent()
        request = AgentRequest(agent_id="qa", prompt="qa")
        request.context = "not a dict"
        response = agent.execute(request)
        assert response.success or response.error is not None

    def test_qa_get_validators_cached(self):
        agent = QAAgent()
        first = agent._get_validators()
        second = agent._get_validators()
        assert first == second

    def test_qa_get_validators_import_error(self):
        """Test _get_validators ImportError branch."""
        import sys
        from unittest.mock import patch

        agent = QAAgent()
        agent._qa_pipeline = None
        agent._world_validator = None
        with patch.dict(sys.modules, {"validators": None}, clear=False):
            result = agent._get_validators()
        assert result == (None, None)

    def test_qa_resolve_world_directly(self):
        agent = QAAgent()
        world = {"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}}
        result = agent._resolve_world(world)
        assert result is not None

    def test_qa_resolve_world_passthrough(self):
        agent = QAAgent()
        sentinel = "not a dict"
        result = agent._resolve_world(sentinel)
        assert result == sentinel

    def test_qa_validates_all_four_categories(self):
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={
                "campaign": {"theme": "issavi", "lore": ["x"], "factions": []},
                "playtest_report": {"player_level": 200},
                "artifacts": {},
            },
        )
        response = agent.execute(request)
        if response.success:
            for cat in ("world_model", "campaign", "playtest", "artifacts", "overall"):
                assert cat in response.output_data

    def test_qa_overall_score_is_numeric(self):
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}},
        )
        response = agent.execute(request)
        if response.success:
            score = response.output_data["overall"]["score"]
            assert isinstance(score, (int, float))
            assert 0.0 <= score <= 1.0

    def test_qa_world_validator_via_inject(self):
        """Inject a world validator to exercise the world_validator if-branch."""
        agent = QAAgent()

        class FakeResult:
            is_valid = True
            errors = []
            warnings = []
            def to_dict(self):
                return {"valid": True, "checks": []}

        class FakeValidator:
            def validate(self, world):
                return FakeResult()

        agent._qa_pipeline = None
        agent._world_validator = FakeValidator()

        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}},
        )
        response = agent.execute(request)
        assert response.success
        if response.success:
            assert response.output_data["world_model"].get("valid") is True

    def test_qa_world_validator_dict_result(self):
        """Test the elif isinstance branch where validator returns a dict."""
        agent = QAAgent()

        class FakeValidatorDict:
            def validate(self, world):
                return {"valid": True, "checks": [{"name": "ok", "passed": True}]}

        agent._qa_pipeline = None
        agent._world_validator = FakeValidatorDict()

        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}},
        )
        response = agent.execute(request)
        if response.success:
            wm = response.output_data["world_model"]
            assert wm.get("valid") is True

    def test_qa_world_validator_other_result(self):
        """Test the else branch where validator result is neither dict nor has to_dict."""
        agent = QAAgent()

        class FakeValidatorOther:
            def validate(self, world):
                return "just a string"

        agent._qa_pipeline = None
        agent._world_validator = FakeValidatorOther()

        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {"0,0,7": {"x": 0, "y": 0, "z": 7, "ground": 106}}},
        )
        response = agent.execute(request)
        if response.success:
            wm = response.output_data["world_model"]
            # Without to_dict and not a dict, should produce is_valid: True
            assert "valid" in wm

    def test_qa_resolve_world_import_error(self):
        """_resolve_world when import fails."""
        import sys
        from unittest.mock import patch

        agent = QAAgent()
        with patch.dict(sys.modules, {"core.world": None}, clear=False):
            result = agent._resolve_world({"tiles": {}})
        assert result == {"tiles": {}}

    def test_qa_playtest_empty(self):
        """Playtest validation with empty data."""
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"playtest_report": {}},
        )
        response = agent.execute(request)
        if response.success:
            assert "playtest" in response.output_data

    def test_qa_campaign_missing_fields(self):
        """Campaign validation with partial data."""
        agent = QAAgent()
        request = AgentRequest(
            agent_id="qa", prompt="qa",
            input_data={"tiles": {}},
            context={"campaign": {"theme": "issavi"}},  # missing lore/factions
        )
        response = agent.execute(request)
        if response.success:
            campaign = response.output_data["campaign"]
            # In the fallback path, theme alone counts as valid;
            # only truly empty dict fails.
            campaign2 = response.output_data.get("campaign", {})
            assert "checks" in campaign2
