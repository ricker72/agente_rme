"""
Tests for AgentRegistry and BaseAgent.
"""

import pytest
from agente_rme.core.agents import AgentRegistry, BaseAgent
from agente_rme.core.agents.contracts import AgentRequest, AgentResponse


class TestBaseAgent:
    def test_agent_id_default(self):
        agent = BaseAgent()
        assert agent.agent_id == "base"

    def test_agent_id_custom(self):
        class CustomAgent(BaseAgent):
            AGENT_ID = "custom"
        agent = CustomAgent()
        assert agent.agent_id == "custom"

    def test_execute_raises_not_implemented(self):
        agent = BaseAgent()
        request = AgentRequest()
        with pytest.raises(NotImplementedError):
            agent.execute(request)

    def test_repr(self):
        class CustomAgent(BaseAgent):
            AGENT_ID = "test_agent"
        agent = CustomAgent()
        assert "CustomAgent" in repr(agent)
        assert "test_agent" in repr(agent)


class TestAgentRegistry:
    def test_register_and_get(self):
        registry = AgentRegistry()
        agent = BaseAgent()
        registry.register(agent)
        assert registry.get("base") is agent

    def test_get_unregistered(self):
        registry = AgentRegistry()
        assert registry.get("nonexistent") is None

    def test_get_or_raise_found(self):
        registry = AgentRegistry()
        agent = BaseAgent()
        registry.register(agent)
        assert registry.get_or_raise("base") is agent

    def test_get_or_raise_missing(self):
        registry = AgentRegistry()
        with pytest.raises(KeyError):
            registry.get_or_raise("nonexistent")

    def test_unregister(self):
        registry = AgentRegistry()
        agent = BaseAgent()
        registry.register(agent)
        registry.unregister("base")
        assert registry.get("base") is None

    def test_unregister_nonexistent(self):
        registry = AgentRegistry()
        registry.unregister("nonexistent")  # Should not raise

    def test_list_agents_empty(self):
        registry = AgentRegistry()
        assert registry.list_agents() == []

    def test_list_agents(self):
        registry = AgentRegistry()
        registry.register(BaseAgent())
        assert "base" in registry.list_agents()

    def test_has_agent_true(self):
        registry = AgentRegistry()
        registry.register(BaseAgent())
        assert registry.has_agent("base") is True

    def test_has_agent_false(self):
        registry = AgentRegistry()
        assert registry.has_agent("nonexistent") is False

    def test_execute_delegates_to_agent(self):
        class TestAgent(BaseAgent):
            AGENT_ID = "test"

            def execute(self, request):
                return AgentResponse.success_response(
                    self.agent_id,
                    output_data={"result": "success"},
                )

        registry = AgentRegistry()
        agent = TestAgent()
        registry.register(agent)
        request = AgentRequest()
        response = registry.execute("test", request)
        assert response.success is True
        assert response.output_data == {"result": "success"}

    def test_execute_unregistered_raises(self):
        registry = AgentRegistry()
        request = AgentRequest()
        with pytest.raises(KeyError):
            registry.execute("nonexistent", request)

    def test_multiple_agents(self):
        registry = AgentRegistry()

        class AgentA(BaseAgent):
            AGENT_ID = "a"

        class AgentB(BaseAgent):
            AGENT_ID = "b"

        registry.register(AgentA())
        registry.register(AgentB())
        assert len(registry.list_agents()) == 2
        assert "a" in registry.list_agents()
        assert "b" in registry.list_agents()

    def test_register_overwrites(self):
        registry = AgentRegistry()
        agent1 = BaseAgent()
        agent2 = BaseAgent()
        registry.register(agent1)
        registry.register(agent2)
        assert registry.get("base") is agent2