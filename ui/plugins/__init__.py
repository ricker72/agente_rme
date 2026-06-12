"""
Plugin management for Agente RME Studio.

Provides a PluginManager that can discover, load, and unload plugins.
No real plugins are registered yet — this is the infrastructure skeleton.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any


class PluginBase:
    """Abstract base that every plugin must implement."""

    @property
    def plugin_id(self) -> str:
        """Unique identifier for this plugin."""
        return self.__class__.__name__

    def on_load(self, app: Any) -> None:
        """Called when the plugin is loaded.  *app* is the RMEStudioApp instance."""

    def on_unload(self) -> None:
        """Called when the plugin is unloaded."""


class PluginManager:
    """Discovers and manages UI plugins.

    Usage::

        mgr = PluginManager()
        mgr.discover("ui.plugins")
        mgr.load_all(app)
    """

    def __init__(self) -> None:
        self._plugins: dict[str, PluginBase] = {}
        self._loaded: set[str] = set()

    # ── discovery ───────────────────────────────────────────────────────

    def discover(self, package: str) -> list[str]:
        """Scan *package* for ``PluginBase`` subclasses and register them.

        Returns a list of plugin identifiers found.
        """
        found: list[str] = []
        # Walk the given package looking for importable modules
        try:
            pkg = importlib.import_module(package)
        except ImportError:
            return found

        for _finder, name, _ispkg in pkgutil.walk_packages(
            pkg.__path__,  # type: ignore[arg-type]
            prefix=f"{package}.",
        ):
            try:
                mod = importlib.import_module(name)
            except Exception:
                continue  # skip broken plugins

            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PluginBase)
                    and attr is not PluginBase
                ):
                    instance = attr()
                    self._plugins[instance.plugin_id] = instance
                    found.append(instance.plugin_id)
        return found

    def register(self, plugin: PluginBase) -> None:
        """Manually register a plugin instance."""
        self._plugins[plugin.plugin_id] = plugin

    # ── lifecycle ───────────────────────────────────────────────────────

    def load_all(self, app: Any) -> list[str]:
        """Call ``on_load`` on every registered plugin.

        Returns a list of plugin IDs that were loaded.
        """
        loaded: list[str] = []
        for pid, plugin in self._plugins.items():
            if pid not in self._loaded:
                try:
                    plugin.on_load(app)
                    self._loaded.add(pid)
                    loaded.append(pid)
                except Exception:
                    pass  # FIXME: log failure
        return loaded

    def unload_all(self) -> list[str]:
        """Call ``on_unload`` on every loaded plugin."""
        unloaded: list[str] = []
        for pid in list(self._loaded):
            plugin = self._plugins.get(pid)
            if plugin is not None:
                try:
                    plugin.on_unload()
                except Exception:
                    pass
                self._loaded.discard(pid)
                unloaded.append(pid)
        return unloaded

    # ── query ───────────────────────────────────────────────────────────

    @property
    def plugins(self) -> dict[str, PluginBase]:
        """All registered plugins (loaded or not)."""
        return dict(self._plugins)

    @property
    def loaded(self) -> set[str]:
        """Set of currently loaded plugin identifiers."""
        return set(self._loaded)


__all__: list[str] = [
    "PluginBase",
    "PluginManager",
]
