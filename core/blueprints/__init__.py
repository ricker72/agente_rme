from __future__ import annotations

from .blueprint import Blueprint, BlueprintTile, BlueprintMetadata
from .blueprint_loader import BlueprintLoader, BlueprintLoadError
from .blueprint_validator import BlueprintValidator, ValidationResult, ValidationError
from .blueprint_registry import BlueprintRegistry
from .blueprint_placer import BlueprintPlacer, BlueprintPlacerError
from .blueprint_search import BlueprintSearch, SearchResult, SearchQuery
from .blueprint_mixer import BlueprintMixer, MixResult

# HITO 13 — Blueprint Extractor pipeline
from .theme_classifier import ThemeClassifier
from .pattern_detector import PatternDetector, Pattern
from .structure_detector import StructureDetector, DetectedStructure
from .blueprint_extractor import BlueprintExtractor, ExtractionResult

__all__ = [
    # Core
    "Blueprint",
    "BlueprintTile",
    "BlueprintMetadata",
    "BlueprintLoader",
    "BlueprintLoadError",
    "BlueprintValidator",
    "ValidationResult",
    "ValidationError",
    "BlueprintRegistry",
    "BlueprintPlacer",
    "BlueprintPlacerError",
    "BlueprintSearch",
    "SearchResult",
    "SearchQuery",
    "BlueprintMixer",
    "MixResult",
    # HITO 13 — Extractor pipeline
    "ThemeClassifier",
    "PatternDetector",
    "Pattern",
    "StructureDetector",
    "DetectedStructure",
    "BlueprintExtractor",
    "ExtractionResult",
]
