# mypy: ignore-errors
"""Canonical Blueprint Intelligence 2.0 analyzer import surface."""

from __future__ import annotations

from .blueprint_analyzer_v2 import BlueprintAnalyzerV2


BlueprintAnalyzer = BlueprintAnalyzerV2

__all__ = ["BlueprintAnalyzer", "BlueprintAnalyzerV2"]
