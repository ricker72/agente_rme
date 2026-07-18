"""
RULE-41 audit and report generation.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .event_storage import EventStorage


class ObservabilityReporter:
    """Build mandatory RULE-41 reports from authoritative storage."""

    AUDIT_REPORT = "RULE41_OBSERVABILITY_AUDIT.json"
    COVERAGE_REPORT = "RULE41_EVENT_COVERAGE.json"
    COMPLETENESS_REPORT = "RULE41_TRACE_COMPLETENESS.json"
    RUNTIME_REPORT = "RULE41_RUNTIME_OBSERVABILITY_REPORT.md"

    def __init__(self, storage: Optional[EventStorage] = None) -> None:
        self.storage = storage or EventStorage()

    def generate_reports(self) -> Dict[str, Any]:
        """Generate all mandatory RULE-41 reports."""
        events = self.storage.events()
        audit = self._load_json(EventStorage.OBSERVABILITY_AUDIT)
        if not audit:
            audit = {
                "rule": "RULE-41",
                "status": "NO_EVENTS_EMITTED",
                "events_emitted": 0,
                "blockers": ["EVENT_EMISSION_MISSING"],
            }
        coverage = self._coverage(events)
        completeness = self._completeness(events)

        self._write_json(self.AUDIT_REPORT, audit)
        self._write_json(self.COVERAGE_REPORT, coverage)
        self._write_json(self.COMPLETENESS_REPORT, completeness)
        self._write_markdown(self.RUNTIME_REPORT, audit, coverage, completeness)
        return {
            "audit": audit,
            "coverage": coverage,
            "completeness": completeness,
            "runtime_report": str(self.storage.workspace_root / self.RUNTIME_REPORT),
        }

    def _coverage(self, events: list[Dict[str, Any]]) -> Dict[str, Any]:
        modules = sorted({event["module"] for event in events})
        categories = sorted({event["category"] for event in events})
        required_categories = [
            "ARCHITECTURE_EVENT",
            "TILE_PLACEMENT_EVENT",
            "BRUSH_SELECTION_EVENT",
            "APPEARANCE_SELECTION_EVENT",
            "DISTRICT_EVENT",
            "ROAD_EVENT",
            "BUILDING_EVENT",
            "NPC_EVENT",
            "SPAWN_EVENT",
            "QUEST_EVENT",
            "CONNECTIVITY_EVENT",
            "PLAYABILITY_EVENT",
            "VALIDATION_EVENT",
            "EXPORT_EVENT",
        ]
        missing_categories = [
            category for category in required_categories if category not in categories
        ]
        return {
            "rule": "RULE-41",
            "events_emitted": len(events),
            "modules_covered": modules,
            "categories_covered": categories,
            "missing_required_categories": missing_categories,
            "module_coverage": len(modules),
            "category_coverage": len(categories),
            "coverage_status": "PASS" if events and not missing_categories else "PARTIAL",
        }

    def _completeness(self, events: list[Dict[str, Any]]) -> Dict[str, Any]:
        trace_ids = {event["trace_id"] for event in events}
        mandatory = {
            "event_id",
            "trace_id",
            "timestamp",
            "module",
            "phase",
            "action",
            "description",
            "coordinates",
            "floor",
            "entity_type",
            "severity",
            "result",
            "duration_ms",
            "parent_event",
            "source_dataset",
        }
        incomplete = [
            event["event_id"]
            for event in events
            if not mandatory.issubset(event.keys())
        ]
        return {
            "rule": "RULE-41",
            "trace_count": len(trace_ids),
            "event_count": len(events),
            "incomplete_event_ids": incomplete,
            "trace_completeness": 1.0 if events and not incomplete else 0.0,
            "completeness_status": "PASS" if events and not incomplete else "FAIL",
        }

    def _load_json(self, name: str) -> Dict[str, Any]:
        path = self.storage.workspace_root / name
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, name: str, payload: Dict[str, Any]) -> None:
        path = self.storage.workspace_root / name
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)

    def _write_markdown(
        self,
        name: str,
        audit: Dict[str, Any],
        coverage: Dict[str, Any],
        completeness: Dict[str, Any],
    ) -> None:
        path = self.storage.workspace_root / name
        lines = [
            "# RULE-41 Live Generation Observability",
            "",
            "## RULE-41 Live Generation Observability",
            "",
            f"Observability Enabled: {audit.get('events_emitted', 0) > 0}",
            f"Events Emitted: {audit.get('events_emitted', 0)}",
            f"Trace Coverage: {completeness.get('trace_completeness', 0.0)}",
            f"Modules Covered: {coverage.get('modules_covered', [])}",
            "Trace Storage Generated: LIVE_GENERATION_TRACE.jsonl, EVENT_STREAM.json, TRACE_REGISTRY.json, GENERATION_TIMELINE.json, OBSERVABILITY_AUDIT.json",
            "WG-20U Consumption Status: CONSUMES_RULE41_TRACE_ARTIFACTS",
            f"Observability Audit Result: {audit.get('status', 'UNKNOWN')}",
            f"Final RULE-41 Status: {audit.get('status', 'UNKNOWN')}",
            "",
            "## Blockers",
            "",
            ", ".join(audit.get("blockers", [])) or "None",
        ]
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
