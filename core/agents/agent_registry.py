"""core.agents.agent_registry — Base agent class and registry."""
from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all agents. Subclasses must override execute()."""
    AGENT_ID = "base"

    def __init__(self) -> None:
        self.agent_id = self.AGENT_ID
        self.logger = logging.getLogger(f"agent.{self.agent_id}")

    def execute(self, request: Any) -> Any:
        raise NotImplementedError(f"{self.__class__.__name__}.execute() must be implemented")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.agent_id})"


class AgentRegistry:
    """Registry of agents by ID."""
    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> Optional[BaseAgent]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[str]:
        return list(self._agents.keys())
