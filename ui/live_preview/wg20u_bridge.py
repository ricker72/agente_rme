from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from core.wg20u import Wg20uVisualValidator


class Wg20uStudioBridge:
    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = workspace_root
        self.validator = Wg20uVisualValidator(self.workspace_root)

    def load(self) -> Dict[str, Any]:
        return self.validator.load_datasets()

    def viewport_data(self) -> Dict[str, Any]:
        return self.validator.get_viewport_data()

    def connectivity_data(self) -> Dict[str, Any]:
        return self.validator.get_connectivity_panel_data()

    def critic_data(self) -> Dict[str, Any]:
        return self.validator.get_critic_panel_data()

    def playtest_data(self) -> Dict[str, Any]:
        return self.validator.get_playtest_panel_data()

    def tile_data(self, x: int, y: int, z: int) -> Dict[str, Any]:
        return self.validator.get_tile_inspector_data(x, y, z)