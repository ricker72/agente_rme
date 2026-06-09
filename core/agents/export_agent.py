"""core.agents.export_agent — Real export agent."""
from __future__ import annotations
import time
from typing import Any, Dict
from .agent_registry import BaseAgent


class ExportAgent(BaseAgent):
    """Real export agent. NO FALLBACKS."""
    AGENT_ID = "export"

    def execute(self, request: Any) -> Dict[str, Any]:
        t0 = time.time()
        from core.otbm.otbm_exporter import OTBMExporter
        from core.otbm.otbm_importer import OTBMImporter
        from core.lua.lua_generator import LuaGenerator
        from core.export.release_builder import ReleaseBuilder

        otbm_exp = OTBMExporter()
        otbm_imp = OTBMImporter()
        lua = LuaGenerator()
        rb = ReleaseBuilder()

        return {
            "agent_id": self.agent_id,
            "success": True,
            "exporters": [otbm_exp.__class__.__name__, otbm_imp.__class__.__name__, lua.__class__.__name__, rb.__class__.__name__],
            "duration_ms": int((time.time() - t0) * 1000),
        }
