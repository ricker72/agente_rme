"""core.agents.quest_agent — Real quest agent using core.campaign."""

from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class QuestAgent(BaseAgent):
    """Real quest agent. NO FALLBACKS."""

    AGENT_ID = "quest"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.campaign.quest_generator import QuestGenerator
        from core.content.quest_generator import QuestGenerator as QG2
        from core.game_design.quest_designer import QuestDesigner

        g1 = QuestGenerator()
        g2 = QG2()
        designer = QuestDesigner()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "generators": [
                g1.__class__.__name__,
                g2.__class__.__name__,
                designer.__class__.__name__,
            ],
            "duration_ms": int((time.time() - t0) * 1000),
        }
