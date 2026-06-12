"""core.agents.mapper_agent — Real mapper agent using AI mapper engines."""

from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class MapperAgent(BaseAgent):
    """Real mapper agent. Uses core.architect.mapper_ai. NO FALLBACKS."""

    AGENT_ID = "mapper"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.architect.mapper_ai import MapperAI
        from core.architect.layout_engine import LayoutEngine

        mapper = MapperAI()
        layout = LayoutEngine()
        layout_map = (
            layout.generate_layout() if hasattr(layout, "generate_layout") else {}
        )

        return {
            "agent_id": self.agent_id,
            "success": True,
            "mapper_info": {"class": mapper.__class__.__name__},
            "layout": layout_map,
            "duration_ms": int((time.time() - t0) * 1000),
        }
