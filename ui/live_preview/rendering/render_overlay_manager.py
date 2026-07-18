"""
Render overlay manager for WG-20U-A.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class RenderOverlayManager:
    """Tracks supported viewport overlays."""

    floor_overlay: bool = True
    brush_overlay: bool = True
    connectivity_overlay: bool = True
    critic_overlay: bool = True
    event_trace_overlay: bool = True
    invalid_placement_overlay: bool = True

    def audit(self) -> Dict[str, bool]:
        return {
            "floor_overlay": self.floor_overlay,
            "brush_overlay": self.brush_overlay,
            "connectivity_overlay": self.connectivity_overlay,
            "critic_overlay": self.critic_overlay,
            "event_trace_overlay": self.event_trace_overlay,
            "invalid_placement_overlay": self.invalid_placement_overlay,
        }
