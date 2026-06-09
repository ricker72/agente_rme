"""
HITO 28 — OpenTibia Knowledge Dataset Builder.

A learning subsystem that catalogs knowledge extracted from maps, blueprints,
campaigns, playtest reports and critic reports, then exposes similarity,
search, ranking and recommendation APIs.

Top-level entry points:

  - `DatasetBuilder`     — process sources into a `KnowledgeDataset`.
  - `KnowledgeEngine`    — high-level public API (find_similar_*, search, query).
  - `KnowledgeIndex`     — per-type in-memory indexers.
  - `KnowledgeQuery`     — text / structured / filter queries.
  - `KnowledgeRanker`    — combines quality, critic, playtest, reuse, similarity.
  - `KnowledgeRecommender` — reuse recommendations.
  - `KnowledgeSearch`    — search facade.
  - `KnowledgeCatalog`   — high-level catalog description.
  - `KnowledgeMetrics`   — coverage / quality metrics (knowledge_metrics.json).
  - `KnowledgeReport`    — human-readable report (knowledge_report.md).
"""

from .dataset_builder import DatasetBuilder, BuildStats
from .knowledge_catalog import KnowledgeCatalog
from .knowledge_engine import KnowledgeEngine
from .knowledge_index import KnowledgeIndex
from .knowledge_metrics import KnowledgeMetrics, build_metrics
from .knowledge_query import KnowledgeQuery, parse_query, ParsedQuery
from .knowledge_ranker import KnowledgeRanker, RankerWeights
from .knowledge_recommender import KnowledgeRecommender
from .knowledge_report import KnowledgeReport
from .knowledge_search import KnowledgeSearch
from .models import (
    EntryType,
    KnowledgeDataset,
    KnowledgeEntry,
    KnowledgeQueryResult,
    QueryMatch,
    cosine_similarity,
    hybrid_similarity,
    jaccard_similarity,
    pattern_similarity,
)

__all__ = [
    "DatasetBuilder",
    "BuildStats",
    "KnowledgeCatalog",
    "KnowledgeEngine",
    "KnowledgeIndex",
    "KnowledgeMetrics",
    "KnowledgeQuery",
    "KnowledgeRanker",
    "KnowledgeRecommender",
    "KnowledgeReport",
    "KnowledgeSearch",
    "ParsedQuery",
    "parse_query",
    "RankerWeights",
    "build_metrics",
    "EntryType",
    "KnowledgeDataset",
    "KnowledgeEntry",
    "KnowledgeQueryResult",
    "QueryMatch",
    "cosine_similarity",
    "jaccard_similarity",
    "pattern_similarity",
    "hybrid_similarity",
]
