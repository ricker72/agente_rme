"""
RULE-41 trace manager.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import uuid4


@dataclass
class TraceContext:
    """Represents one generation trace."""

    trace_id: str
    module: str
    phase: str
    parent_trace_id: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)


class TraceManager:
    """Creates stable trace IDs for generation pipelines."""

    def __init__(self, prefix: str = "TRACE") -> None:
        self.prefix = prefix

    def start_trace(
        self,
        module: str,
        phase: str,
        parent_trace_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> TraceContext:
        """Create a new trace context."""
        return TraceContext(
            trace_id=trace_id or f"{self.prefix}-{uuid4().hex[:8].upper()}",
            module=module,
            phase=phase,
            parent_trace_id=parent_trace_id,
            metadata=metadata or {},
        )
