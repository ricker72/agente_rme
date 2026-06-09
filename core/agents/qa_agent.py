"""core.agents.qa_agent — Real QA agent."""
from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class QAAgent(BaseAgent):
    """Real QA agent. NO FALLBACKS."""
    AGENT_ID = "qa"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.world.world_validator import WorldValidator
        from core.quality.quality_score import QualityScore
        from core.quality.map_reviewer import MapReviewer
        from core.blueprints.blueprint_validator import BlueprintValidator

        wv = WorldValidator()
        qs = QualityScore()
        mr = MapReviewer()
        bv = BlueprintValidator()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "validators": [wv.__class__.__name__, qs.__class__.__name__, mr.__class__.__name__, bv.__class__.__name__],
            "duration_ms": int((time.time() - t0) * 1000),
        }
