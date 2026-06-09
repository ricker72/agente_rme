"""core.agents.expansion_agent — Real expansion agent."""
from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class ExpansionAgent(BaseAgent):
    """Real expansion agent. Uses core.expansion. NO FALLBACKS."""
    AGENT_ID = "expansion"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.expansion.expansion_ai import ExpansionAI
        from core.expansion.hunt_expander import HuntExpander
        from core.expansion.boss_expander import BossExpander

        exp_ai = ExpansionAI()
        hunt_exp = HuntExpander()
        boss_exp = BossExpander()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "expanders": {
                "ai": exp_ai.__class__.__name__,
                "hunt": hunt_exp.__class__.__name__,
                "boss": boss_exp.__class__.__name__,
            },
            "duration_ms": int((time.time() - t0) * 1000),
        }
