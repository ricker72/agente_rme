"""
Critic models — data structures for the Visual Map Critic AI.
"""

from .critic_score import CriticScore
from .critic_issue import CriticIssue, IssueType, IssueSeverity
from .critic_recommendation import CriticRecommendation, RecommendationPriority
from .critic_result import CriticResult, CriticCategoryResult

__all__ = [
    "CriticScore",
    "CriticIssue",
    "IssueType",
    "IssueSeverity",
    "CriticRecommendation",
    "RecommendationPriority",
    "CriticResult",
    "CriticCategoryResult",
]
