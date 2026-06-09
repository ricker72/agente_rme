"""
Core Learning Module - Map Learning AI for OpenTibia

This module provides AI capabilities for learning from thousands of OpenTibia maps,
creating embeddings, encoding styles and patterns, and generating new map blueprints.

HITO 17 - Self-Learning Blueprint Library:
- BlueprintLearner: Main entry point for learning from OTBM maps
- PatternMiner: Mines recurring architectural patterns
- SimilarityEngine: Finds similar blueprints
- BlueprintRanker: Ranks blueprints by quality
- BlueprintCatalog: Persistent storage and retrieval
"""

from .dataset_builder import DatasetBuilder
from .map_embedding import MapEmbedding, MapEmbedder
from .style_encoder import StyleEncoder
from .pattern_encoder import PatternEncoder
from .similarity_engine import SimilarityEngine
from .learning_pipeline import LearningPipeline

# HITO 17 - Self-Learning Blueprint Library
from .blueprint_learner import BlueprintLearner, LearningResult
from .pattern_miner import PatternMiner, MinedPattern
from .blueprint_ranker import BlueprintRanker, RankedBlueprint
from .blueprint_catalog import BlueprintCatalog, BlueprintIndexEntry

__all__ = [
    "DatasetBuilder",
    "MapEmbedding",
    "MapEmbedder",
    "StyleEncoder",
    "PatternEncoder",
    "SimilarityEngine",
    "LearningPipeline",
    # HITO 17
    "BlueprintLearner",
    "LearningResult",
    "PatternMiner",
    "MinedPattern",
    "BlueprintRanker",
    "RankedBlueprint",
    "BlueprintCatalog",
    "BlueprintIndexEntry",
]
