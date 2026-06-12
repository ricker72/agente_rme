"""core.agents.architect_agent — Real architect agent using core.architect.AIArchitect."""

from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class ArchitectAgent(BaseAgent):
    """Real architect agent. Uses AIArchitect engine. NO FALLBACKS."""

    AGENT_ID = "architect"

    def execute(self, request: Any) -> Dict[str, Any]:
        """Run AIArchitect on the prompt."""
        t0 = time.time()
        from core.architect.ai_architect import AIArchitect
        from core.architect.world_planner import WorldPlanner

        prompt = getattr(request, "prompt", "") or ""
        world_width = (
            getattr(request, "world_width", 512)
            if hasattr(request, "world_width")
            else 512
        )
        world_height = (
            getattr(request, "world_height", 512)
            if hasattr(request, "world_height")
            else 512
        )

        architect = AIArchitect()
        planner = WorldPlanner()
        plan = architect.plan(
            prompt, world_width=world_width, world_height=world_height
        )
        world_plan = planner.plan(prompt) if prompt else None

        return {
            "agent_id": self.agent_id,
            "success": True,
            "plan": plan.to_dict() if hasattr(plan, "to_dict") else dict(plan),
            "world_plan": (
                world_plan.to_dict()
                if world_plan and hasattr(world_plan, "to_dict")
                else None
            ),
            "duration_ms": int((time.time() - t0) * 1000),
        }
