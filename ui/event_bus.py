"""
Typed Event Bus for Agente RME Studio.

All events are concrete classes to avoid magic strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar

# ---------------------------------------------------------------------------
# Event types
# ---------------------------------------------------------------------------

T = TypeVar("T", bound="BaseEvent")


class BaseEvent:
    """Marker base for every event on the bus."""


@dataclass(frozen=True)
class ApplicationStartedEvent(BaseEvent):
    """Emitted once the main window and all subsystems are ready."""

    timestamp: float = 0.0


@dataclass(frozen=True)
class ApplicationClosingEvent(BaseEvent):
    """Emitted before the main window starts tearing down."""

    timestamp: float = 0.0


@dataclass(frozen=True)
class PageChangedEvent(BaseEvent):
    """Emitted when the active workspace page changes."""

    previous_page: str = ""
    current_page: str = ""


@dataclass(frozen=True)
class ThemeChangedEvent(BaseEvent):
    """Emitted when the UI theme palette is toggled or reloaded."""

    theme_name: str = "dark"


@dataclass(frozen=True)
class ConsoleMessageEvent(BaseEvent):
    """Emitted when a new line should be appended to the console panel."""

    level: str = "info"  # info | warn | error | debug
    message: str = ""
    source: str = ""


@dataclass(frozen=True)
class StatusMessageEvent(BaseEvent):
    """Emitted when the status bar text should be updated."""

    message: str = ""
    timeout_ms: int = 0  # 0 = persistent


@dataclass(frozen=True)
class ServiceStateChangedEvent(BaseEvent):
    """Emitted when a background service changes state."""

    service_name: str = ""
    state: str = ""  # idle | running | error


# ---------------------------------------------------------------------------
# Service Layer Events (UI-4)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WorldGenerationRequestedEvent(BaseEvent):
    """Emitted when world generation is requested."""

    request_id: str = ""
    world_name: str = ""


@dataclass(frozen=True)
class WorldGeneratedEvent(BaseEvent):
    """Emitted when a world has been generated."""

    world_id: str = ""
    world_name: str = ""
    success: bool = True
    message: str = ""


@dataclass(frozen=True)
class CriticAnalysisRequestedEvent(BaseEvent):
    """Emitted when critic analysis is requested."""

    request_id: str = ""
    world_id: str = ""


@dataclass(frozen=True)
class CriticCompletedEvent(BaseEvent):
    """Emitted when a critic analysis completes."""

    analysis_id: str = ""
    score: float = 0.0
    issue_count: int = 0


@dataclass(frozen=True)
class KnowledgeQueryRequestedEvent(BaseEvent):
    """Emitted when a knowledge query is requested."""

    request_id: str = ""
    query: str = ""


@dataclass(frozen=True)
class KnowledgeQueryCompletedEvent(BaseEvent):
    """Emitted when a knowledge query completes."""

    request_id: str = ""
    query: str = ""
    result_count: int = 0


@dataclass(frozen=True)
class KnowledgeQueryEvent(BaseEvent):
    """Emitted when a knowledge query is performed."""

    query: str = ""
    result_count: int = 0


@dataclass(frozen=True)
class CampaignGeneratedEvent(BaseEvent):
    """Emitted when a campaign has been generated."""

    campaign_id: str = ""
    campaign_name: str = ""
    success: bool = True


@dataclass(frozen=True)
class OTBMImportCompletedEvent(BaseEvent):
    """Emitted when an OTBM import completes."""

    path: str = ""
    world_id: str = ""
    success: bool = True
    message: str = ""


@dataclass(frozen=True)
class OTBMExportCompletedEvent(BaseEvent):
    """Emitted when an OTBM export completes."""

    path: str = ""
    tile_count: int = 0
    success: bool = True
    message: str = ""


@dataclass(frozen=True)
class OTBMExportedEvent(BaseEvent):
    """Emitted when an OTBM export completes."""

    path: str = ""
    tile_count: int = 0
    success: bool = True


@dataclass(frozen=True)
class AutonomousDesignStartedEvent(BaseEvent):
    """Emitted when autonomous design begins."""

    design_id: str = ""
    world_id: str = ""


@dataclass(frozen=True)
class AutonomousIterationCompletedEvent(BaseEvent):
    """Emitted when one autonomous design iteration completes."""

    design_id: str = ""
    iteration_number: int = 0
    success: bool = True
    message: str = ""


@dataclass(frozen=True)
class AutonomousDesignCompletedEvent(BaseEvent):
    """Emitted when autonomous design completes."""

    design_id: str = ""
    world_id: str = ""
    success: bool = True
    message: str = ""


@dataclass(frozen=True)
class AutonomousIterationEvent(BaseEvent):
    """Emitted during autonomous agent iterations."""

    iteration: int = 0
    status: str = ""  # started | progress | completed | error
    progress: float = 0.0


@dataclass(frozen=True)
class ServiceErrorEvent(BaseEvent):
    """Emitted when a UI service returns or reports an error."""

    service_name: str = ""
    operation: str = ""
    message: str = ""


# ---------------------------------------------------------------------------
# Listener protocol & bus implementation
# ---------------------------------------------------------------------------

EventListener = Callable[[BaseEvent], None]


class EventBus:
    """Simple typed, synchronous event bus.

    Events are dispatched synchronously.  For long-running listeners,
    consider wrapping them with :class:`QThread` or ``asyncio``.
    """

    def __init__(self) -> None:
        self._listeners: dict[type[BaseEvent], list[EventListener]] = {}

    def register(self, event_type: type[BaseEvent], listener: EventListener) -> None:
        """Register *listener* to be called when *event_type* is emitted."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def unregister(self, event_type: type[BaseEvent], listener: EventListener) -> None:
        """Remove a previously registered listener."""
        lst = self._listeners.get(event_type)
        if lst is not None:
            try:
                lst.remove(listener)
            except ValueError:
                pass

    def emit(self, event: BaseEvent) -> None:
        """Dispatch *event* to all registered listeners."""
        for listener in self._listeners.get(type(event), ()):
            listener(event)

    def clear(self) -> None:
        """Remove all registered listeners (useful for testing)."""
        self._listeners.clear()
