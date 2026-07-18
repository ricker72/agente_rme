"""
RULE-41 persistent event storage.

Writes the authoritative files consumed by WG-20U and future milestones:
LIVE_GENERATION_TRACE.jsonl, EVENT_STREAM.json, TRACE_REGISTRY.json,
GENERATION_TIMELINE.json, and OBSERVABILITY_AUDIT.json.
"""

from __future__ import annotations

import json
import threading
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .event_models import GenerationEvent


class EventStorage:
    """Persist every emitted GenerationEvent to RULE-41 artifacts."""

    LIVE_TRACE = "LIVE_GENERATION_TRACE.jsonl"
    EVENT_STREAM = "EVENT_STREAM.json"
    TRACE_REGISTRY = "TRACE_REGISTRY.json"
    GENERATION_TIMELINE = "GENERATION_TIMELINE.json"
    OBSERVABILITY_AUDIT = "OBSERVABILITY_AUDIT.json"

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = Path(workspace_root or Path.cwd())
        self._lock = threading.Lock()
        self._events: List[Dict[str, Any]] = self._load_existing_events()

    @property
    def paths(self) -> Dict[str, Path]:
        """Return absolute storage paths keyed by artifact name."""
        return {
            self.LIVE_TRACE: self.workspace_root / self.LIVE_TRACE,
            self.EVENT_STREAM: self.workspace_root / self.EVENT_STREAM,
            self.TRACE_REGISTRY: self.workspace_root / self.TRACE_REGISTRY,
            self.GENERATION_TIMELINE: self.workspace_root / self.GENERATION_TIMELINE,
            self.OBSERVABILITY_AUDIT: self.workspace_root / self.OBSERVABILITY_AUDIT,
        }

    def persist(self, event: GenerationEvent) -> None:
        """Persist one event and refresh aggregate JSON artifacts."""
        event.validate()
        payload = event.to_dict()
        with self._lock:
            self._events.append(payload)
            self.workspace_root.mkdir(parents=True, exist_ok=True)
            with open(self.paths[self.LIVE_TRACE], "a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
            self._write_json_artifacts()

    def events(self) -> List[Dict[str, Any]]:
        """Return a copy of all observed events."""
        with self._lock:
            return list(self._events)

    def reset(self) -> None:
        """Clear in-memory and on-disk RULE-41 trace artifacts."""
        with self._lock:
            self._events = []
            for path in self.paths.values():
                if path.exists():
                    path.unlink()

    def _load_existing_events(self) -> List[Dict[str, Any]]:
        path = self.workspace_root / self.LIVE_TRACE
        if not path.exists():
            return []
        events: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return events

    def _write_json_artifacts(self) -> None:
        self._write_json(self.paths[self.EVENT_STREAM], {"events": self._events})
        self._write_json(self.paths[self.TRACE_REGISTRY], self._build_trace_registry())
        self._write_json(self.paths[self.GENERATION_TIMELINE], self._build_timeline())
        self._write_json(self.paths[self.OBSERVABILITY_AUDIT], self._build_audit())

    def _build_trace_registry(self) -> Dict[str, Any]:
        traces: Dict[str, Dict[str, Any]] = {}
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for event in self._events:
            grouped[event["trace_id"]].append(event)

        for trace_id, events in grouped.items():
            traces[trace_id] = {
                "trace_id": trace_id,
                "event_count": len(events),
                "modules": sorted({event["module"] for event in events}),
                "categories": sorted({event["category"] for event in events}),
                "started_at": events[0]["timestamp"],
                "last_event_at": events[-1]["timestamp"],
                "root_events": [
                    event["event_id"] for event in events if not event.get("parent_event")
                ],
            }
        return {"trace_count": len(traces), "traces": traces}

    def _build_timeline(self) -> Dict[str, Any]:
        return {
            "events": [
                {
                    "timestamp": event["timestamp"],
                    "trace_id": event["trace_id"],
                    "event_id": event["event_id"],
                    "module": event["module"],
                    "phase": event["phase"],
                    "action": event["action"],
                    "description": event["description"],
                    "severity": event["severity"],
                    "result": event["result"],
                }
                for event in self._events
            ]
        }

    def _build_audit(self) -> Dict[str, Any]:
        category_counts = Counter(event["category"] for event in self._events)
        module_counts = Counter(event["module"] for event in self._events)
        severity_counts = Counter(event["severity"] for event in self._events)
        trace_ids = {event["trace_id"] for event in self._events}
        event_ids = {event["event_id"] for event in self._events}
        orphan_events = [
            event["event_id"]
            for event in self._events
            if event.get("parent_event") and event["parent_event"] not in event_ids
        ]
        failed_events = [
            event["event_id"]
            for event in self._events
            if str(event.get("result", "")).upper() in {"FAIL", "FAILED", "ERROR"}
        ]
        total_latency = sum(float(event.get("duration_ms") or 0.0) for event in self._events)
        event_count = len(self._events)
        required_fields = {
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
        complete = [
            event
            for event in self._events
            if required_fields.issubset(event.keys()) and all(event.get(key) for key in ("event_id", "trace_id", "timestamp", "module"))
        ]
        return {
            "rule": "RULE-41",
            "status": "LIVE_GENERATION_OBSERVABILITY_READY" if event_count else "NO_EVENTS_EMITTED",
            "events_emitted": event_count,
            "events_consumed": 0,
            "trace_count": len(trace_ids),
            "orphan_events": len(orphan_events),
            "orphan_event_ids": orphan_events,
            "failed_events": len(failed_events),
            "failed_event_ids": failed_events,
            "warning_events": severity_counts.get("WARNING", 0),
            "error_events": severity_counts.get("ERROR", 0) + severity_counts.get("CRITICAL", 0),
            "average_event_latency": round(total_latency / event_count, 3) if event_count else 0.0,
            "trace_completeness": round(len(complete) / event_count, 4) if event_count else 0.0,
            "module_coverage": dict(sorted(module_counts.items())),
            "category_coverage": dict(sorted(category_counts.items())),
            "blockers": self._blockers(event_count, orphan_events, failed_events, complete),
        }

    def _blockers(
        self,
        event_count: int,
        orphan_events: Iterable[str],
        failed_events: Iterable[str],
        complete_events: Iterable[Dict[str, Any]],
    ) -> List[str]:
        blockers: List[str] = []
        complete_count = len(list(complete_events))
        if event_count == 0:
            blockers.append("EVENT_EMISSION_MISSING")
        if orphan_events:
            blockers.append("TRACE_COMPLETENESS_FAILED")
        if failed_events:
            blockers.append("TRACE_GENERATION_FAILED")
        if event_count and complete_count != event_count:
            blockers.append("TRACE_COMPLETENESS_FAILED")
        return blockers

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False, default=str)
