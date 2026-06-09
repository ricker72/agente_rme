"""
Tests for AgentContext.
"""

import pytest
from agente_rme.core.agents import AgentContext


class TestAgentContext:
    def test_default_initialization(self):
        ctx = AgentContext()
        assert ctx.prompt == ""
        assert ctx.world_plan is None
        assert ctx.world_model is None
        assert ctx.campaign is None
        assert ctx.playtest_report == {}
        assert ctx.balance_report == {}
        assert ctx.qa_report == {}
        assert ctx.artifacts == {}
        assert ctx.parameters == {}

    def test_init_with_values(self):
        ctx = AgentContext(
            prompt="test prompt",
            parameters={"level": 300},
        )
        assert ctx.prompt == "test prompt"
        assert ctx.parameters == {"level": 300}

    def test_to_dict_excludes_optional_objects(self):
        ctx = AgentContext(prompt="hello")
        d = ctx.to_dict()
        assert d["prompt"] == "hello"
        assert "parameters" in d

    def test_update_existing_field(self):
        ctx = AgentContext()
        ctx.update({"prompt": "updated"})
        assert ctx.prompt == "updated"

    def test_update_unknown_goes_to_metadata(self):
        ctx = AgentContext()
        ctx.update({"unknown_field": "value"})
        assert ctx.metadata.get("unknown_field") == "value"

    def test_update_multiple_fields(self):
        ctx = AgentContext()
        ctx.update({"prompt": "test", "parameters": {"key": "val"}})
        assert ctx.prompt == "test"
        assert ctx.parameters == {"key": "val"}

    def test_playtest_report_dict(self):
        ctx = AgentContext(playtest_report={"xp": 100})
        d = ctx.to_dict()
        assert d["playtest_report"] == {"xp": 100}

    def test_artifacts_dict(self):
        ctx = AgentContext(artifacts={"preview.png": "/path/to/png"})
        d = ctx.to_dict()
        assert d["artifacts"]["preview.png"] == "/path/to/png"

    def test_qa_report_dict(self):
        ctx = AgentContext(qa_report={"score": 0.85})
        d = ctx.to_dict()
        assert d["qa_report"]["score"] == 0.85