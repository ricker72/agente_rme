"""Tests for typed UI service events."""

from __future__ import annotations

from dataclasses import is_dataclass

from ui.event_bus import (
    AutonomousDesignCompletedEvent,
    AutonomousDesignStartedEvent,
    AutonomousIterationCompletedEvent,
    CampaignGeneratedEvent,
    CriticAnalysisRequestedEvent,
    CriticCompletedEvent,
    EventBus,
    KnowledgeQueryCompletedEvent,
    KnowledgeQueryRequestedEvent,
    OTBMExportCompletedEvent,
    OTBMImportCompletedEvent,
    ServiceErrorEvent,
    WorldGeneratedEvent,
    WorldGenerationRequestedEvent,
)


def test_required_service_events_are_typed_dataclasses() -> None:
    events = [
        WorldGenerationRequestedEvent,
        WorldGeneratedEvent,
        CriticAnalysisRequestedEvent,
        CriticCompletedEvent,
        KnowledgeQueryRequestedEvent,
        KnowledgeQueryCompletedEvent,
        CampaignGeneratedEvent,
        OTBMImportCompletedEvent,
        OTBMExportCompletedEvent,
        AutonomousDesignStartedEvent,
        AutonomousIterationCompletedEvent,
        AutonomousDesignCompletedEvent,
        ServiceErrorEvent,
    ]
    for event_type in events:
        assert is_dataclass(event_type)
        assert event_type() is not None


def test_event_bus_dispatches_typed_event() -> None:
    bus = EventBus()
    seen: list[WorldGeneratedEvent] = []

    def on_world_generated(event: object) -> None:
        assert isinstance(event, WorldGeneratedEvent)
        seen.append(event)

    bus.register(WorldGeneratedEvent, on_world_generated)
    bus.emit(WorldGeneratedEvent(world_id="w1", world_name="Test"))
    assert seen == [WorldGeneratedEvent(world_id="w1", world_name="Test")]
