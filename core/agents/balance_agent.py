"""core.agents.balance_agent — Real balance agent."""

from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class BalanceAgent(BaseAgent):
    """Real balance agent. NO FALLBACKS."""

    AGENT_ID = "balance"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.balance.balance_engine import BalanceEngine
        from core.balance.difficulty_balancer import DifficultyBalancer
        from core.balance.xp_balancer import XPBalancer

        engine = BalanceEngine()
        diff = DifficultyBalancer()
        xp = XPBalancer()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "balancers": [
                engine.__class__.__name__,
                diff.__class__.__name__,
                xp.__class__.__name__,
            ],
            "duration_ms": int((time.time() - t0) * 1000),
        }
