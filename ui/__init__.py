"""
Agente RME Studio — New-Generation UI Foundation.

This package is the entry point for the decoupled user interface.
Architecture follows: UI → Services → Adapters → Core.

GA Freeze Compliance:
    - No modifications to core/, agents/, architect/, autonomous/, critic/,
      knowledge/, blueprint_intelligence/, campaign/, export/, otbm/,
      playtest/, world/ directories.
    - No import from any frozen module.
    - All dependencies are declared in pyproject.toml under the `ui` extra.
"""

from .app import RMEStudioApp
from .event_bus import EventBus
from .navigation import NavigationController
from .page_registry import PageRegistry
from .theme import ThemeManager

__all__: list[str] = [
    "RMEStudioApp",
    "EventBus",
    "NavigationController",
    "PageRegistry",
    "ThemeManager",
]

__version__ = "2.0.0"
__author__ = "OpenTibiaBR RME Agent Team"
