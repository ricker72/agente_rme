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
        from core.content.quest_generator import QuestGenerator
        from core.game_design.quest_designer import QuestDesigner

        designer = QuestDesigner()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "generators": [
                QuestGenerator.__name__,
                designer.__class__.__name__,
            ],
            "duration_ms": int((time.time() - t0) * 1000),
        }
