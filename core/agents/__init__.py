"""
core.agents — Real multi-agent pipeline for Agente RME.

All agents use real engines (no mocks, no fallbacks, no simulations).
"""

from .agent_registry import BaseAgent, AgentRegistry
from .architect_agent import ArchitectAgent
from .mapper_agent import MapperAgent
from .expansion_agent import ExpansionAgent
from .quest_agent import QuestAgent
from .playtest_agent import PlaytestAgent
from .balance_agent import BalanceAgent
from .critic_agent import CriticAgent
from .orchestrator_agent import OrchestratorAgent
from .export_agent import ExportAgent
from .qa_agent import QAAgent

__all__ = [
    "BaseAgent",
    "AgentRegistry",
    "ArchitectAgent",
    "MapperAgent",
    "ExpansionAgent",
    "QuestAgent",
    "PlaytestAgent",
    "BalanceAgent",
    "CriticAgent",
    "OrchestratorAgent",
    "ExportAgent",
    "QAAgent",
]
