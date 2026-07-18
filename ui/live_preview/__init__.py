"""
WG-20U RME-like live preview and playtest interface.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .floor_selector import FloorSelector
    from .main_window import LivePreviewMainWindow
    from .minimap_widget import MinimapWidget
    from .viewport_widget import ViewportWidget

__all__ = [
    "LivePreviewMainWindow",
    "ViewportWidget",
    "FloorSelector",
    "MinimapWidget",
]


def __getattr__(name: str) -> object:
    if name == "LivePreviewMainWindow":
        from .main_window import LivePreviewMainWindow

        return LivePreviewMainWindow
    if name == "ViewportWidget":
        from .viewport_widget import ViewportWidget

        return ViewportWidget
    if name == "FloorSelector":
        from .floor_selector import FloorSelector

        return FloorSelector
    if name == "MinimapWidget":
        from .minimap_widget import MinimapWidget

        return MinimapWidget
    raise AttributeError(name)
