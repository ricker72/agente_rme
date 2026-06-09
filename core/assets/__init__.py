from __future__ import annotations

from .asset_indexer import AssetIndexer, IndexedItem, IndexedMonster
from .asset_classifier import AssetClassifier, ClassificationResult
from .asset_similarity import AssetSimilarity, SimilarityResult, SimilarItem
from .asset_recommender import AssetRecommender, Recommendation, RecommendationResult

__all__ = [
    # Indexer
    "AssetIndexer",
    "IndexedItem",
    "IndexedMonster",
    # Classifier
    "AssetClassifier",
    "ClassificationResult",
    # Similarity
    "AssetSimilarity",
    "SimilarityResult",
    "SimilarItem",
    # Recommender
    "AssetRecommender",
    "Recommendation",
    "RecommendationResult",
]