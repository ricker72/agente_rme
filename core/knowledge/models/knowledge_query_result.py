"""
KnowledgeQueryResult — container for the result of a knowledge query.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List

from .knowledge_entry import KnowledgeEntry


@dataclass
class QueryMatch:
    """A single match returned by a knowledge query."""

    entry: KnowledgeEntry
    score: float
    match_type: str = "similarity"  # one of: similarity, text, filter, exact
    explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry": self.entry.to_dict(),
            "score": round(float(self.score), 4),
            "match_type": self.match_type,
            "explanation": self.explanation,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QueryMatch":
        return cls(
            entry=KnowledgeEntry.from_dict(data.get("entry", {})),
            score=float(data.get("score", 0.0)),
            match_type=data.get("match_type", "similarity"),
            explanation=data.get("explanation", ""),
        )


@dataclass
class KnowledgeQueryResult:
    """Result of a knowledge query: a ranked list of matches + metadata."""

    query: str
    matches: List[QueryMatch] = field(default_factory=list)
    total: int = 0
    took_ms: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)

    def add(self, match: QueryMatch) -> None:
        self.matches.append(match)
        self.total = len(self.matches)

    def sort(self) -> "KnowledgeQueryResult":
        self.matches.sort(key=lambda m: m.score, reverse=True)
        return self

    def top(self, k: int = 5) -> List[QueryMatch]:
        return self.matches[:k]

    def names(self) -> List[str]:
        return [m.entry.name for m in self.matches]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "total": self.total,
            "took_ms": round(self.took_ms, 4),
            "matches": [m.to_dict() for m in self.matches],
            "extra": dict(self.extra),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeQueryResult":
        return cls(
            query=data.get("query", ""),
            matches=[QueryMatch.from_dict(d) for d in data.get("matches", []) or []],
            total=int(data.get("total", 0)),
            took_ms=float(data.get("took_ms", 0.0)),
            extra=dict(data.get("extra", {}) or {}),
        )
