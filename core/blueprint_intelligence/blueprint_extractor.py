# mypy: ignore-errors
"""Canonical Blueprint Intelligence 2.0 extractor import surface."""

from __future__ import annotations

from .blueprint_extractor_v2 import BlueprintExtractorV2


BlueprintExtractor = BlueprintExtractorV2

__all__ = ["BlueprintExtractor", "BlueprintExtractorV2"]
