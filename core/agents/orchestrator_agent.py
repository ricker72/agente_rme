"""core.agents.orchestrator_agent — Real orchestrator agent."""

from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class OrchestratorAgent(BaseAgent):
    """Real orchestrator agent. NO FALLBACKS."""

    AGENT_ID = "orchestrator"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from .agent_registry import AgentRegistry
        from .architect_agent import ArchitectAgent
        from .mapper_agent import MapperAgent
        from .expansion_agent import ExpansionAgent
        from .quest_agent import QuestAgent
        from .playtest_agent import PlaytestAgent
        from .balance_agent import BalanceAgent
        from .critic_agent import CriticAgent
        from .export_agent import ExportAgent
        from .qa_agent import QAAgent

        registry = AgentRegistry()
        registry.register(ArchitectAgent())
        registry.register(MapperAgent())
        registry.register(ExpansionAgent())
        registry.register(QuestAgent())
        registry.register(PlaytestAgent())
        registry.register(BalanceAgent())
        registry.register(CriticAgent())
        registry.register(ExportAgent())
        registry.register(QAAgent())

        return {
            "agent_id": self.agent_id,
            "success": True,
            "registered": registry.list_agents(),
            "duration_ms": int((time.time() - t0) * 1000),
        }
