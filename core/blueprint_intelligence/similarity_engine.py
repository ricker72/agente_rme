# mypy: ignore-errors
"""Canonical Blueprint Intelligence 2.0 similarity import surface."""

from __future__ import annotations

from .similarity_engine_v2 import SimilarityEngineV2, SimilarityResultV2


SimilarityEngine = SimilarityEngineV2
SimilarityResult = SimilarityResultV2

__all__ = [
    "SimilarityEngine",
    "SimilarityEngineV2",
    "SimilarityResult",
    "SimilarityResultV2",
]
